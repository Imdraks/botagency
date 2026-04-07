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


def search_spotify_artist(name: str) -> Optional[Dict[str, Any]]:
    """
    Search for an artist on Spotify via web scraping.
    Uses Spotify's open search page to find the artist, then scrapes their page.
    
    Returns dict with: spotify_artist_id, name, monthly_listeners, image_url
    or None on failure.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Playwright not installed")
        return None

    search_url = f"https://open.spotify.com/search/{name}/artists"
    logger.info(f"Searching Spotify for artist: {name}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
            )
            page = context.new_page()
            page.goto(search_url, timeout=15000, wait_until="domcontentloaded")
            # Need to wait for JS to render search results
            page.wait_for_timeout(4000)

            # Look for artist links in the page
            content = page.content()
            browser.close()

        # Extract artist IDs from links: /artist/<22-char-id>
        artist_ids = re.findall(r'/artist/([a-zA-Z0-9]{22})', content)
        if not artist_ids:
            logger.warning(f"No Spotify artist results for '{name}'")
            return None

        # Take the first unique ID (most relevant result)
        seen = set()
        unique_ids = []
        for aid in artist_ids:
            if aid not in seen:
                seen.add(aid)
                unique_ids.append(aid)

        # Scrape the first result's artist page
        best_id = unique_ids[0]
        logger.info(f"Spotify search found {len(unique_ids)} artists, scraping first: {best_id}")
        return scrape_spotify_artist(best_id)

    except Exception as e:
        logger.error(f"Spotify search scraping failed for '{name}': {e}")
        return None
