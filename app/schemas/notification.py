"""
Pydantic schemas for Notification model.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Base schema
class NotificationBase(BaseModel):
    """Base notification schema with common attributes."""
    message: str = Field(..., min_length=1)
    type: str = "system"


# Create schema (used internally)
class NotificationCreate(NotificationBase):
    """Schema for creating a new notification."""
    user_id: UUID
    reference_id: Optional[UUID] = None
    reference_type: Optional[str] = Field(None, max_length=50)


# Read schema (response)
class NotificationRead(NotificationBase):
    """Schema for reading notification data (response)."""
    id: UUID
    user_id: UUID
    reference_id: Optional[UUID] = None
    reference_type: Optional[str] = None
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


# Mark as read request
class MarkAsReadRequest(BaseModel):
    """Schema for marking notifications as read."""
    notification_ids: Optional[list[UUID]] = None  # If None, mark all as read


# Notification filter
class NotificationFilter(BaseModel):
    """Schema for notification filtering."""
    is_read: Optional[bool] = None
    type: Optional[str] = None
