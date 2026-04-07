"""
Spotify Web Scraper Provider
Scrapes public Spotify artist pages using Playwright to get:
- Monthly listeners (real number from the page)
- Artist name, image, verified status
- Genres (from meta tags)
No API key needed — uses open.spotify.com public pages.
"""
import logging
import re
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def _parse_listener_count(raw: str) -> int:
    """Parse listener count strings like '6.1M', '500K', '1,234,567'."""
    raw = raw.strip().replace(",", "").replace(" ", "")
    multiplier = 1
    if raw.upper().endswith("B"):
        multiplier = 1_000_000_000
        raw = raw[:-1]
    elif raw.upper().endswith("M"):
        multiplier = 1_000_000
        raw = raw[:-1]
    elif raw.upper().endswith("K"):
        multiplier = 1_000
        raw = raw[:-1]
    try:
        return int(float(raw) * multiplier)
    except (ValueError, TypeError):
        return 0


def scrape_spotify_artist(spotify_id: str) -> Optional[Dict[str, Any]]:
    """
    Scrape a Spotify public artist page for monthly listeners + metadata.
    Uses Playwright (sync) with headless Chromium.
    
    Returns dict with: name, monthly_listeners, image_url, description
    or None on failure.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Playwright not installed")
        return None

    url = f"https://open.spotify.com/artist/{spotify_id}"
    logger.info(f"Scraping Spotify artist page: {url}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
            )
            page = context.new_page()
            page.goto(url, timeout=15000, wait_until="domcontentloaded")
            # Wait briefly for SSR meta tags (they're in the initial HTML)
            page.wait_for_timeout(1500)

            content = page.content()
            browser.close()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, "lxml")

        result: Dict[str, Any] = {"spotify_artist_id": spotify_id}

        # Extract from OG meta tags (server-side rendered)
        og_title = soup.find("meta", property="og:title")
        if og_title:
            result["name"] = og_title.get("content", "").strip()

        og_image = soup.find("meta", property="og:image")
        if og_image:
            result["image_url"] = og_image.get("content", "")

        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            desc = og_desc.get("content", "")
            result["description"] = desc
            # Parse monthly listeners: "Artist · 6.1M monthly listeners."
            ml_match = re.search(r"([\d,.]+[KMB]?)\s*monthly\s*listener", desc, re.IGNORECASE)
            if ml_match:
                result["monthly_listeners"] = _parse_listener_count(ml_match.group(1))

        # Try to extract from page title as fallback
        title_tag = soup.find("title")
        if title_tag and not result.get("name"):
            # "Niska | Spotify"
            name = title_tag.text.split("|")[0].strip()
            if name and name != "Spotify":
                result["name"] = name

        logger.info(f"Scraped Spotify {spotify_id}: name={result.get('name')}, ml={result.get('monthly_listeners')}")
        return result if result.get("name") or result.get("monthly_listeners") else None

    except Exception as e:
        logger.error(f"Spotify scraping failed for {spotify_id}: {e}")
        return None


def _search_musicbrainz(name: str) -> Optional[str]:
    """
    Find Spotify artist ID via MusicBrainz (free, reliable, no auth).
    MusicBrainz stores external links (url-rels) including Spotify URLs.
    Rate limit: 1 request/second, requires User-Agent.
    """
    import time
    try:
        import httpx
        headers = {"User-Agent": "RadarApp/1.0 (contact@radarapp.fr)"}

        # Step 1: Search for artist by name
        r = httpx.get(
            "https://musicbrainz.org/ws/2/artist/",
            params={"query": name, "fmt": "json", "limit": 5},
            headers=headers,
            timeout=10,
        )
        if r.status_code != 200:
            logger.warning(f"MusicBrainz search HTTP {r.status_code} for '{name}'")
            return None

        artists = r.json().get("artists", [])
        if not artists:
            logger.warning(f"MusicBrainz: no results for '{name}'")
            return None

        # Pick best match: prefer exact name match with high score
        name_lower = name.lower().strip()
        best = None
        for a in artists:
            if a.get("name", "").lower().strip() == name_lower and a.get("score", 0) >= 80:
                best = a
                break
        if not best:
            # Fallback to highest score if >= 90
            top = artists[0]
            if top.get("score", 0) >= 90:
                best = top
        if not best:
            logger.warning(f"MusicBrainz: no confident match for '{name}' (top score: {artists[0].get('score')})")
            return None

        mbid = best["id"]
        logger.info(f"MusicBrainz matched '{name}' → '{best['name']}' (score={best.get('score')}, mbid={mbid})")

        # Step 2: Get external URLs (url-rels) — respect rate limit
        time.sleep(1.1)
        r2 = httpx.get(
            f"https://musicbrainz.org/ws/2/artist/{mbid}",
            params={"inc": "url-rels", "fmt": "json"},
            headers=headers,
            timeout=10,
        )
        if r2.status_code != 200:
            logger.warning(f"MusicBrainz url-rels HTTP {r2.status_code} for mbid={mbid}")
            return None

        for rel in r2.json().get("relations", []):
            url = rel.get("url", {}).get("resource", "")
            if "open.spotify.com/artist/" in url:
                spotify_id = url.split("/artist/")[-1].split("?")[0]
                if re.match(r"^[a-zA-Z0-9]{22}$", spotify_id):
                    logger.info(f"MusicBrainz found Spotify ID for '{name}': {spotify_id}")
                    return spotify_id

        logger.warning(f"MusicBrainz: no Spotify URL for '{name}' (mbid={mbid})")
        return None

    except Exception as e:
        logger.warning(f"MusicBrainz search failed for '{name}': {e}")
        return None


def search_spotify_id_by_name(name: str) -> Optional[str]:
    """
    Find a Spotify artist ID by name.
    Strategy: MusicBrainz (primary) → Google search (fallback).
    
    Returns the Spotify artist ID (22 chars) or None.
    """
    # Primary: MusicBrainz (free, reliable, structured data)
    spotify_id = _search_musicbrainz(name)
    if spotify_id:
        return spotify_id

    # Fallback: Google search
    try:
        import httpx
        query = f'site:open.spotify.com/artist "{name}"'
        r = httpx.get(
            "https://www.google.com/search",
            params={"q": query, "num": 5},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=10,
            follow_redirects=True,
        )
        ids = re.findall(r'open\.spotify\.com/artist/([a-zA-Z0-9]{22})', r.text)
        if ids:
            from collections import Counter
            best_id = Counter(ids).most_common(1)[0][0]
            logger.info(f"Google fallback found Spotify ID for '{name}': {best_id}")
            return best_id
    except Exception as e:
        logger.warning(f"Google fallback failed for '{name}': {e}")

    logger.warning(f"No Spotify ID found for '{name}' via any source")
    return None
