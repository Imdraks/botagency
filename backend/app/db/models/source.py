"""
Source configuration model
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from .opportunity import SourceType


class SourceConfig(Base):
    """Configuration for data sources"""
    __tablename__ = "source_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic info
    name = Column(String(255), unique=True, nullable=False)
    source_type = Column(Enum(SourceType), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Connection details
    url = Column(String(2000), nullable=True)  # For RSS, HTML, API
    
    # Email specific (stored separately for IMAP source)
    email_folder = Column(String(255), nullable=True)
    email_sender_filter = Column(String(255), nullable=True)  # Filter by sender
    
    # HTML scraping config
    html_selectors = Column(JSON, nullable=True)
    # Example: {
    #   "item_selector": ".opportunity-item",
    #   "title_selector": "h2",
    #   "description_selector": ".description",
    #   "link_selector": "a.primary-link",
    #   "deadline_selector": ".deadline",
    #   "pagination_selector": ".next-page"
    # }
    
    # API config
    api_headers = Column(JSON, nullable=True)
    api_params = Column(JSON, nullable=True)
    api_response_mapping = Column(JSON, nullable=True)
    
    # Scheduling
    poll_interval_minutes = Column(Integer, default=360)  # 6 hours default
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    
    # Stats
    total_items_fetched = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    last_error_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    opportunities = relationship("Opportunity", back_populates="source_config")
    ingestion_runs = relationship("IngestionRun", back_populates="source_config")
    
    def __repr__(self):
        return f"<SourceConfig {self.name} ({self.source_type})>"
