"""
Deezer API Provider
Free API, no authentication required.
Provides: artist search, profile (fans, image), top tracks.
Rate limit: ~50 requests/5 seconds (very generous).
"""
import logging
from typing import Optional, Dict, Any, List

import httpx

logger = logging.getLogger(__name__)

DEEZER_API = "https://api.deezer.com"
TIMEOUT = 10


def search_deezer_artist(name: str) -> Optional[Dict[str, Any]]:
    """
    Search for an artist on Deezer by name.
    Returns the best match with profile + top tracks.
    """
    try:
        r = httpx.get(
            f"{DEEZER_API}/search/artist",
            params={"q": name},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()

        items = data.get("data", [])
        if not items:
            logger.warning(f"No Deezer results for '{name}'")
            return None

        # Pick best match (exact name first, then most fans)
        name_lower = name.lower().strip()
        best = None
        for item in items:
            if item.get("name", "").lower().strip() == name_lower:
                best = item
                break
        if not best:
            best = max(items, key=lambda x: x.get("nb_fan", 0))

        return fetch_deezer_artist(best["id"])

    except Exception as e:
        logger.error(f"Deezer search failed for '{name}': {e}")
        return None


def fetch_deezer_artist(artist_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch full artist profile + top tracks from Deezer.
    """
    try:
        # Profile
        r = httpx.get(f"{DEEZER_API}/artist/{artist_id}", timeout=TIMEOUT)
        r.raise_for_status()
        profile = r.json()

        if profile.get("error"):
            logger.warning(f"Deezer artist {artist_id} error: {profile['error']}")
            return None

        result: Dict[str, Any] = {
            "deezer_id": profile.get("id"),
            "name": profile.get("name"),
            "deezer_fans": profile.get("nb_fan", 0),
            "image_url": profile.get("picture_xl") or profile.get("picture_big") or profile.get("picture_medium"),
            "nb_album": profile.get("nb_album", 0),
            "deezer_url": profile.get("link"),
        }

        # Top tracks
        try:
            r2 = httpx.get(
                f"{DEEZER_API}/artist/{artist_id}/top",
                params={"limit": 10},
                timeout=TIMEOUT,
            )
            r2.raise_for_status()
            top = r2.json()

            result["top_tracks"] = [
                {
                    "name": t.get("title"),
                    "rank": t.get("rank", 0),
                    "duration_s": t.get("duration", 0),
                    "album": t.get("album", {}).get("title"),
                }
                for t in top.get("data", [])
            ]
        except Exception:
            result["top_tracks"] = []

        logger.info(f"Deezer fetched {profile.get('name')}: {result['deezer_fans']} fans, {len(result['top_tracks'])} tracks")
        return result

    except Exception as e:
        logger.error(f"Deezer fetch failed for artist {artist_id}: {e}")
        return None
