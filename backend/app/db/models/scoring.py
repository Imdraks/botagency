"""
Scoring rules model
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Text, Boolean, DateTime, Enum, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class RuleType(str, PyEnum):
    """Types of scoring rules"""
    URGENCY = "URGENCY"
    EVENT_FIT = "EVENT_FIT"
    QUALITY = "QUALITY"
    VALUE = "VALUE"
    PENALTY = "PENALTY"


class ScoringRule(Base):
    """Configurable scoring rules"""
    __tablename__ = "scoring_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Rule identification
    name = Column(String(100), unique=True, nullable=False)
    rule_type = Column(Enum(RuleType), nullable=False)
    description = Column(Text, nullable=True)
    
    # Rule logic
    condition_type = Column(String(50), nullable=False)
    # Types: "deadline_days", "keywords", "has_field", "regex", "organization_type"
    
    condition_value = Column(JSON, nullable=False)
    # Examples:
    # - deadline_days: {"operator": "lt", "value": 7}
    # - keywords: {"words": ["privatisation", "lieu"], "match": "any"}
    # - has_field: {"fields": ["url_primary", "contact_email"]}
    # - regex: {"pattern": "budget.*\\d+.*€", "field": "description"}
    
    # Scoring
    points = Column(Integer, nullable=False)
    label = Column(String(100), nullable=False)  # Display label for breakdown
    
    # Ordering and grouping
    priority = Column(Integer, default=0)  # Higher priority rules evaluated first
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ScoringRule {self.name}: {self.points:+d}>"
