"""
Bandsintown API service.
Fetches real events for artists and normalises them for upsert into artist_events.

API: https://rest.bandsintown.com/artists/{name}/events?app_id=xxx&date=upcoming
Free public tier: no explicit rate limit documented.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

import httpx

logger = logging.getLogger(__name__)

BIT_BASE = "https://rest.bandsintown.com"
APP_ID = "squarespace-lewis"


class BandsintownService:
    """Fetch events from the Bandsintown REST API."""

    def __init__(self, app_id: str = APP_ID):
        self.app_id = app_id

    def search_events_for_artist(
        self,
        artist_name: str,
        date: str = "upcoming",
    ) -> List[Dict[str, Any]]:
        """Fetch upcoming events for a specific artist.
        Returns a list of normalised event dicts."""

        params = {
            "app_id": self.app_id,
            "date": date,
        }

        try:
            with httpx.Client(timeout=20) as client:
                resp = client.get(
                    f"{BIT_BASE}/artists/{artist_name}/events",
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning("Bandsintown HTTP %s for '%s': %s", e.response.status_code, artist_name, e)
            return []
        except Exception as e:
            logger.error("Bandsintown error for '%s': %s", artist_name, e)
            return []

        if not isinstance(data, list):
            return []

        return [self._normalise(ev, artist_name) for ev in data]

    def get_artist_info(self, artist_name: str) -> Optional[Dict[str, Any]]:
        """Get basic artist info (tracker count, image, etc.)."""
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(
                    f"{BIT_BASE}/artists/{artist_name}",
                    params={"app_id": self.app_id},
                )
                resp.raise_for_status()
                return resp.json()
        except Exception:
            return None

    @staticmethod
    def _normalise(ev: Dict[str, Any], fallback_artist: str = "") -> Dict[str, Any]:
        """Turn a raw Bandsintown event object into a flat dict
        compatible with the TicketmasterService format."""

        venue = ev.get("venue", {})

        # Coordinates
        lat = None
        lng = None
        try:
            lat = float(venue.get("latitude")) if venue.get("latitude") else None
            lng = float(venue.get("longitude")) if venue.get("longitude") else None
        except (ValueError, TypeError):
            pass

        # Date
        event_date = None
        dt_str = ev.get("datetime") or ev.get("starts_at")
        if dt_str:
            try:
                event_date = datetime.fromisoformat(dt_str)
            except Exception:
                pass

        # Artist
        artist_data = ev.get("artist", {})
        artist_name = artist_data.get("name") or fallback_artist
        artist_image = artist_data.get("image_url")

        # Offers / tickets
        offers = ev.get("offers", [])
        event_url = None
        if offers:
            event_url = offers[0].get("url")
        if not event_url:
            event_url = ev.get("url")

        # Event type
        event_type = "concert"
        if ev.get("festival_start_date"):
            event_type = "festival"

        city = venue.get("city", "")
        country = venue.get("country", "")

        result = {
            "external_id": f"bit_{ev.get('id', '')}",
            "artist_name": artist_name,
            "event_name": ev.get("title") or f"{artist_name} @ {venue.get('name', city)}",
            "event_type": event_type,
            "event_url": event_url,
            "event_image": artist_image,
            "venue": venue.get("name"),
            "city": city,
            "country": country,
            "lat": lat,
            "lng": lng,
            "event_date": event_date,
            "on_sale_date": None,
            "price_min": None,
            "price_max": None,
            "currency": "EUR",
            "status": "onsale" if not ev.get("sold_out") else "soldout",
            "promoter": None,
            "segment": "Music",
            "genre_classification": None,
            "raw_data": ev,
        }

        # Geocoding fallback
        if not result.get("lat") or not result.get("lng"):
            if city:
                try:
                    from app.api.map_calendar import get_coordinates_for_location
                    coords = get_coordinates_for_location(city)
                    if coords:
                        result["lat"] = coords["lat"]
                        result["lng"] = coords["lng"]
                except Exception:
                    pass

        return result
