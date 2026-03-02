"""
Pydantic schemas for Task model.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.user import UserMinimal


# Enums as strings
TaskStatus = str  # pending, in_progress, completed, cancelled
TaskPriority = str  # low, medium, high, critical


# Base schema
class TaskBase(BaseModel):
    """Base task schema with common attributes."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: TaskStatus = "pending"
    priority: TaskPriority = "medium"
    due_date: Optional[datetime] = None
    tags: Optional[List[str]] = Field(default_factory=list)


# Create schema
class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    assigned_to_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        allowed = {"pending", "in_progress", "completed", "cancelled"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {allowed}")
        return v
    
    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate priority value."""
        allowed = {"low", "medium", "high", "critical"}
        if v not in allowed:
            raise ValueError(f"Priority must be one of: {allowed}")
        return v


# Update schema
class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    assigned_to_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    is_archived: Optional[bool] = None
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status value."""
        if v is None:
            return v
        allowed = {"pending", "in_progress", "completed", "cancelled"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {allowed}")
        return v
    
    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate priority value."""
        if v is None:
            return v
        allowed = {"low", "medium", "high", "critical"}
        if v not in allowed:
            raise ValueError(f"Priority must be one of: {allowed}")
        return v


# Read schema (response)
class TaskRead(TaskBase):
    """Schema for reading task data (response)."""
    id: UUID
    owner_id: UUID
    assigned_to_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    # Nested relationships
    owner: Optional[UserMinimal] = None
    assigned_to: Optional[UserMinimal] = None
    
    model_config = {"from_attributes": True}


# Task with counts (for list views)
class TaskListItem(TaskRead):
    """Task schema optimized for list views."""
    comments_count: int = 0
    attachments_count: int = 0


# Filter schema for query parameters
class TaskFilter(BaseModel):
    """Schema for task filtering query parameters."""
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to_id: Optional[UUID] = None
    team_id: Optional[UUID] = None
    search: Optional[str] = None
    due_before: Optional[datetime] = None
    due_after: Optional[datetime] = None
    is_archived: Optional[bool] = False
    tags: Optional[List[str]] = None
    
    model_config = {"extra": "ignore"}


# Assign task schema
class TaskAssignRequest(BaseModel):
    """Schema for assigning a task to a user."""
    assigned_to_id: UUID


# Task status update schema
class TaskStatusUpdate(BaseModel):
    """Schema for updating task status."""
    status: TaskStatus
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate status value."""
        allowed = {"pending", "in_progress", "completed", "cancelled"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {allowed}")
        return v
