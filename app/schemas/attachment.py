"""
Pydantic schemas for Attachment model.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.user import UserMinimal


# Base schema
class AttachmentBase(BaseModel):
    """Base attachment schema with common attributes."""
    filename: str = Field(..., min_length=1, max_length=255)


# Create schema (used internally after upload)
class AttachmentCreate(AttachmentBase):
    """Schema for creating a new attachment record."""
    file_url: str = Field(..., max_length=500)
    file_size: int = Field(..., gt=0)
    mime_type: str = Field(..., max_length=100)


# Read schema (response)
class AttachmentRead(AttachmentBase):
    """Schema for reading attachment data (response)."""
    id: UUID
    file_url: str
    file_size: int
    mime_type: str
    task_id: UUID
    uploaded_by: UUID
    created_at: datetime
    
    # Nested relationships
    uploaded_by_user: Optional[UserMinimal] = None
    
    model_config = {"from_attributes": True}


# File upload response schema
class FileUploadResponse(BaseModel):
    """Schema for file upload response."""
    success: bool
    message: str
    attachment: Optional[AttachmentRead] = None
