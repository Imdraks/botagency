"""
Ingestion run model - logs for each ingestion execution
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Text, DateTime, Enum, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class IngestionStatus(str, PyEnum):
    """Status of an ingestion run"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"  # Some errors but completed
    FAILED = "FAILED"


class IngestionRun(Base):
    """Log of each ingestion execution"""
    __tablename__ = "ingestion_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source reference
    source_config_id = Column(UUID(as_uuid=True), ForeignKey('source_configs.id'), nullable=True)
    source_name = Column(String(255), nullable=False)  # For quick access
    
    # Status
    status = Column(Enum(IngestionStatus), default=IngestionStatus.PENDING)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Stats
    items_fetched = Column(Integer, default=0)
    items_new = Column(Integer, default=0)
    items_duplicate = Column(Integer, default=0)
    items_updated = Column(Integer, default=0)
    items_error = Column(Integer, default=0)
    
    # Errors
    errors = Column(JSON, default=list)  # List of error messages
    
    # Extra info
    run_metadata = Column(JSON, default=dict)  # Additional info (page count, etc.)
    
    # Relationships
    source_config = relationship("SourceConfig", back_populates="ingestion_runs")
    
    def __repr__(self):
        return f"<IngestionRun {self.source_name} - {self.status}>"
    
    def complete(self, status: IngestionStatus = IngestionStatus.SUCCESS):
        """Mark the run as complete"""
        self.completed_at = datetime.utcnow()
        self.status = status
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
