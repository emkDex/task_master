"""
Pydantic schemas for Comment model.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.user import UserMinimal


# Base schema
class CommentBase(BaseModel):
    """Base comment schema with common attributes."""
    content: str = Field(..., min_length=1)


# Create schema
class CommentCreate(CommentBase):
    """Schema for creating a new comment."""
    pass


# Update schema
class CommentUpdate(BaseModel):
    """Schema for updating a comment."""
    content: str = Field(..., min_length=1)


# Read schema (response)
class CommentRead(CommentBase):
    """Schema for reading comment data (response)."""
    id: UUID
    task_id: UUID
    author_id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Nested relationships
    author: Optional[UserMinimal] = None
    
    model_config = {"from_attributes": True}
