"""
ArtistEvent model — real events fetched from Ticketmaster & other sources.
Used by the map to display concerts, festivals, pop-ups on the globe.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Boolean, Text, ForeignKey, Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db import Base


class ArtistEvent(Base):
    __tablename__ = "artist_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    artist_id = Column(UUID(as_uuid=True), ForeignKey("discovery_artists.id", ondelete="CASCADE"), nullable=True)

    # Event identification
    external_id = Column(String(255), nullable=True)  # Ticketmaster event ID
    source = Column(String(50), nullable=False, default="ticketmaster")  # ticketmaster, bandsintown, manual

    # Artist info (denormalized for fast reads)
    artist_name = Column(String(500), nullable=False)
    artist_image = Column(Text, nullable=True)
    artist_genres = Column(JSONB, default=list)
    artist_score = Column(Float, nullable=True)
    monthly_listeners = Column(Integer, nullable=True)

    # Event details
    event_name = Column(String(1000), nullable=False)
    event_type = Column(String(50), nullable=False, default="concert")  # concert, festival, popup_store, brand_event
    event_url = Column(Text, nullable=True)
    event_image = Column(Text, nullable=True)

    # Venue & location
    venue = Column(String(500), nullable=True)
    city = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True, default="FR")
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

    # Date & pricing
    event_date = Column(DateTime, nullable=True)
    on_sale_date = Column(DateTime, nullable=True)
    price_min = Column(Float, nullable=True)
    price_max = Column(Float, nullable=True)
    currency = Column(String(10), nullable=True, default="EUR")
    capacity = Column(Integer, nullable=True)

    # Market intelligence
    status = Column(String(50), nullable=True)  # onsale, offsale, cancelled, rescheduled
    promoter = Column(String(500), nullable=True)
    segment = Column(String(100), nullable=True)  # Music, Arts, Sports
    genre_classification = Column(String(255), nullable=True)  # Ticketmaster genre

    # Metadata
    raw_data = Column(JSONB, nullable=True)  # Full API response for reference
    fetched_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("workspace_id", "external_id", "source", name="uq_workspace_event_source"),
        Index("ix_artist_events_workspace", "workspace_id"),
        Index("ix_artist_events_artist", "artist_id"),
        Index("ix_artist_events_date", "event_date"),
        Index("ix_artist_events_city", "city"),
        Index("ix_artist_events_type", "event_type"),
    )

    def to_map_dict(self) -> dict:
        """Serialize for the map API response."""
        lat = self.lat
        lng = self.lng
        # Geocoding fallback for events missing coordinates
        if not lat or not lng:
            try:
                from app.api.map_calendar import get_coordinates_for_location
                coords = get_coordinates_for_location(self.city)
                if coords:
                    lat = coords["lat"]
                    lng = coords["lng"]
            except Exception:
                pass
        return {
            "id": str(self.id),
            "artist_name": self.artist_name,
            "artist_id": str(self.artist_id) if self.artist_id else None,
            "artist_image": self.artist_image,
            "artist_score": self.artist_score or 0,
            "artist_genres": self.artist_genres or [],
            "monthly_listeners": self.monthly_listeners or 0,
            "event_name": self.event_name,
            "event_type": self.event_type,
            "event_type_label": {
                "concert": "Concert",
                "festival": "Festival",
                "popup_store": "Pop-up Store",
                "brand_event": "Événement de marque",
            }.get(self.event_type, self.event_type),
            "event_url": self.event_url,
            "event_image": self.event_image,
            "venue": self.venue,
            "city": self.city or "",
            "country": self.country or "FR",
            "lat": lat,
            "lng": lng,
            "date": self.event_date.isoformat() if self.event_date else None,
            "date_label": self.event_date.strftime("%d %b %Y") if self.event_date else "",
            "price_min": self.price_min,
            "price_max": self.price_max,
            "currency": self.currency or "EUR",
            "capacity": self.capacity,
            "status": self.status,
            "promoter": self.promoter,
            "source": self.source,
        }
