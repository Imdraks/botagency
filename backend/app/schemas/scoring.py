"""
Scoring rule schemas
"""
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

from app.db.models.scoring import RuleType


class ScoringRuleBase(BaseModel):
    """Base scoring rule schema"""
    name: str = Field(..., max_length=100)
    rule_type: RuleType
    description: Optional[str] = None
    condition_type: str = Field(..., max_length=50)
    condition_value: Dict[str, Any]
    points: int
    label: str = Field(..., max_length=100)
    priority: int = 0
    is_active: bool = True


class ScoringRuleCreate(ScoringRuleBase):
    """Create scoring rule schema"""
    pass


class ScoringRuleUpdate(BaseModel):
    """Update scoring rule schema"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    condition_type: Optional[str] = Field(None, max_length=50)
    condition_value: Optional[Dict[str, Any]] = None
    points: Optional[int] = None
    label: Optional[str] = Field(None, max_length=100)
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class ScoringRuleResponse(ScoringRuleBase):
    """Scoring rule response schema"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
