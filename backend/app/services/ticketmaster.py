"""
Ticketmaster Discovery API service.
Fetches real events for discovered artists and upserts them into artist_events.

API docs: https://developer.ticketmaster.com/products-and-docs/apis/discovery-api/v2/
Free tier: 5 000 requests/day, rate-limited to 5 req/s.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import httpx
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import settings
from app.db.models.artist_event import ArtistEvent

logger = logging.getLogger(__name__)

TM_BASE = "https://app.ticketmaster.com/discovery/v2"
COUNTRY_CODE = "FR"  # Default country filter
PAGE_SIZE = 50


class TicketmasterService:
    """Fetch events from the Ticketmaster Discovery API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ticketmaster_api_key
        if not self.api_key:
            raise ValueError("TICKETMASTER_API_KEY is not set")

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def search_events_for_artist(
        self,
        artist_name: str,
        country_code: str = COUNTRY_CODE,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        size: int = PAGE_SIZE,
    ) -> List[Dict[str, Any]]:
        """Search Ticketmaster for events matching an artist keyword.
        Returns a list of normalised event dicts ready to be stored."""

        if not start_date:
            start_date = datetime.utcnow()
        if not end_date:
            end_date = datetime.utcnow() + timedelta(days=365)

        params = {
            "apikey": self.api_key,
            "keyword": artist_name,
            "countryCode": country_code,
            "classificationName": "Music",
            "startDateTime": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "endDateTime": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "size": str(size),
            "sort": "date,asc",
        }

        try:
            with httpx.Client(timeout=20) as client:
                resp = client.get(f"{TM_BASE}/events.json", params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning("Ticketmaster HTTP %s for '%s': %s", e.response.status_code, artist_name, e)
            return []
        except Exception as e:
            logger.error("Ticketmaster error for '%s': %s", artist_name, e)
            return []

        embedded = data.get("_embedded", {})
        raw_events = embedded.get("events", [])

        return [self._normalise(ev) for ev in raw_events]

    def search_all_music_events(
        self,
        country_code: str = COUNTRY_CODE,
        start_date: Optional[datetime] = None,
        pages: int = 3,
    ) -> List[Dict[str, Any]]:
        """Fetch latest music events across a whole country (no artist filter).
        Good for discovering events that could match artists later."""

        if not start_date:
            start_date = datetime.utcnow()

        all_events: List[Dict[str, Any]] = []

        for page in range(pages):
            params = {
                "apikey": self.api_key,
                "countryCode": country_code,
                "classificationName": "Music",
                "startDateTime": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "size": str(PAGE_SIZE),
                "page": str(page),
                "sort": "date,asc",
            }
            try:
                with httpx.Client(timeout=20) as client:
                    resp = client.get(f"{TM_BASE}/events.json", params=params)
                    resp.raise_for_status()
                    data = resp.json()
            except Exception as e:
                logger.error("Ticketmaster bulk fetch page %d error: %s", page, e)
                break

            embedded = data.get("_embedded", {})
            raw_events = embedded.get("events", [])
            if not raw_events:
                break
            all_events.extend(self._normalise(ev) for ev in raw_events)

        return all_events

    # ------------------------------------------------------------------
    # DB upsert
    # ------------------------------------------------------------------

    @staticmethod
    def upsert_events(
        db: Session,
        workspace_id: int,
        events: List[Dict[str, Any]],
        artist_id: Optional[str] = None,
        artist_meta: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> int:
        """Upsert normalised events into the artist_events table.
        Returns the number of rows upserted."""
        if not events:
            return 0

        meta = artist_meta or {}
        count = 0

        for ev in events:
            values = {
                "workspace_id": workspace_id,
                "artist_id": artist_id,
                "external_id": ev["external_id"],
                "source": ev.get("source", source or "ticketmaster"),
                "artist_name": ev.get("artist_name") or meta.get("name", "Artiste"),
                "artist_image": meta.get("image_url"),
                "artist_genres": meta.get("genres", []),
                "artist_score": meta.get("score"),
                "monthly_listeners": meta.get("monthly_listeners"),
                "event_name": ev["event_name"],
                "event_type": ev["event_type"],
                "event_url": ev.get("event_url"),
                "event_image": ev.get("event_image"),
                "venue": ev.get("venue"),
                "city": ev.get("city"),
                "country": ev.get("country", "FR"),
                "lat": ev.get("lat"),
                "lng": ev.get("lng"),
                "event_date": ev.get("event_date"),
                "on_sale_date": ev.get("on_sale_date"),
                "price_min": ev.get("price_min"),
                "price_max": ev.get("price_max"),
                "currency": ev.get("currency", "EUR"),
                "capacity": ev.get("capacity"),
                "status": ev.get("status"),
                "promoter": ev.get("promoter"),
                "segment": ev.get("segment"),
                "genre_classification": ev.get("genre_classification"),
                "raw_data": ev.get("raw_data"),
                "fetched_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_deleted": False,
            }

            stmt = pg_insert(ArtistEvent).values(**values)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_workspace_event_source",
                set_={
                    "event_name": stmt.excluded.event_name,
                    "event_type": stmt.excluded.event_type,
                    "event_url": stmt.excluded.event_url,
                    "event_image": stmt.excluded.event_image,
                    "venue": stmt.excluded.venue,
                    "city": stmt.excluded.city,
                    "lat": stmt.excluded.lat,
                    "lng": stmt.excluded.lng,
                    "event_date": stmt.excluded.event_date,
                    "price_min": stmt.excluded.price_min,
                    "price_max": stmt.excluded.price_max,
                    "status": stmt.excluded.status,
                    "promoter": stmt.excluded.promoter,
                    "raw_data": stmt.excluded.raw_data,
                    "fetched_at": stmt.excluded.fetched_at,
                    "updated_at": stmt.excluded.updated_at,
                    "is_deleted": False,
                },
            )
            db.execute(stmt)
            count += 1

        db.commit()
        return count

    # ------------------------------------------------------------------
    # Private — normalise a single TM event JSON
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(ev: Dict[str, Any]) -> Dict[str, Any]:
        """Turn a raw Ticketmaster event object into a flat dict."""

        # Venue & location
        venue_data = {}
        venues = ev.get("_embedded", {}).get("venues", [])
        if venues:
            v = venues[0]
            venue_data = {
                "venue": v.get("name"),
                "city": v.get("city", {}).get("name"),
                "country": v.get("country", {}).get("countryCode", "FR"),
                "lat": float(v["location"]["latitude"]) if v.get("location", {}).get("latitude") else None,
                "lng": float(v["location"]["longitude"]) if v.get("location", {}).get("longitude") else None,
                "capacity": v.get("generalInfo", {}).get("generalRule") and None,  # TM rarely gives capacity
            }

        # Date
        dates = ev.get("dates", {})
        start = dates.get("start", {})
        event_date = None
        if start.get("dateTime"):
            try:
                event_date = datetime.fromisoformat(start["dateTime"].replace("Z", "+00:00"))
            except Exception:
                pass
        elif start.get("localDate"):
            try:
                event_date = datetime.strptime(start["localDate"], "%Y-%m-%d")
            except Exception:
                pass

        # On-sale date
        on_sale_date = None
        sales = ev.get("sales", {}).get("public", {})
        if sales.get("startDateTime"):
            try:
                on_sale_date = datetime.fromisoformat(sales["startDateTime"].replace("Z", "+00:00"))
            except Exception:
                pass

        # Pricing
        price_ranges = ev.get("priceRanges", [])
        price_min = None
        price_max = None
        currency = "EUR"
        if price_ranges:
            pr = price_ranges[0]
            price_min = pr.get("min")
            price_max = pr.get("max")
            currency = pr.get("currency", "EUR")

        # Classifications
        classifications = ev.get("classifications", [])
        event_type = "concert"
        segment = None
        genre_classification = None
        if classifications:
            c = classifications[0]
            segment = c.get("segment", {}).get("name")
            genre_name = c.get("genre", {}).get("name", "")
            sub_genre = c.get("subGenre", {}).get("name", "")
            genre_classification = f"{genre_name} / {sub_genre}" if sub_genre else genre_name

            type_name = c.get("type", {}).get("name", "").lower()
            if "festival" in type_name or "festival" in ev.get("name", "").lower():
                event_type = "festival"

        # Promoter
        promoter = None
        promoters = ev.get("promoter") or ev.get("promoters", [])
        if isinstance(promoters, dict):
            promoter = promoters.get("name")
        elif isinstance(promoters, list) and promoters:
            promoter = promoters[0].get("name")

        # Artist name from embedded attractions
        artist_name = None
        attractions = ev.get("_embedded", {}).get("attractions", [])
        if attractions:
            artist_name = attractions[0].get("name")

        # Best image
        images = ev.get("images", [])
        event_image = None
        if images:
            # Prefer 16:9 ratio, largest
            best = sorted(images, key=lambda i: i.get("width", 0), reverse=True)
            event_image = best[0].get("url") if best else None

        result = {
            "external_id": ev.get("id"),
            "artist_name": artist_name or ev.get("name", "Événement"),
            "event_name": ev.get("name", ""),
            "event_type": event_type,
            "event_url": ev.get("url"),
            "event_image": event_image,
            **venue_data,
            "event_date": event_date,
            "on_sale_date": on_sale_date,
            "price_min": price_min,
            "price_max": price_max,
            "currency": currency,
            "status": ev.get("dates", {}).get("status", {}).get("code"),
            "promoter": promoter,
            "segment": segment,
            "genre_classification": genre_classification,
            "raw_data": ev,
        }

        # Geocoding fallback: resolve lat/lng from city name when missing
        if not result.get("lat") or not result.get("lng"):
            city = result.get("city")
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
