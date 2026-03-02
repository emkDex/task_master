"""
Pydantic schemas for ActivityLog model.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.user import UserMinimal


# Base schema
class ActivityLogBase(BaseModel):
    """Base activity log schema with common attributes."""
    action: str = Field(..., min_length=1, max_length=100)
    entity_type: str = Field(..., min_length=1, max_length=50)
    entity_id: UUID


# Create schema (used internally)
class ActivityLogCreate(ActivityLogBase):
    """Schema for creating a new activity log entry."""
    user_id: UUID
    meta: Optional[Dict[str, Any]] = Field(default_factory=dict)
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)


# Read schema (response)
class ActivityLogRead(ActivityLogBase):
    """Schema for reading activity log data (response)."""
    id: UUID
    user_id: UUID
    meta: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    
    # Nested relationships
    user: Optional[UserMinimal] = None
    
    model_config = {"from_attributes": True}


# Activity log filter
class ActivityLogFilter(BaseModel):
    """Schema for activity log filtering."""
    user_id: Optional[UUID] = None
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    action: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
