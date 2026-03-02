"""
Task model for TaskMaster Pro.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Text, DateTime, Enum, Boolean, ForeignKey, Index, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.team import Team
    from app.models.comment import Comment
    from app.models.attachment import Attachment


class Task(Base):
    """Task model for task management."""
    
    __tablename__ = "tasks"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Content fields
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    
    # Status and priority
    status: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "in_progress",
            "completed",
            "cancelled",
            name="task_status_enum"
        ),
        default="pending",
        nullable=False
    )
    priority: Mapped[str] = mapped_column(
        Enum(
            "low",
            "medium",
            "high",
            "critical",
            name="task_priority_enum"
        ),
        default="medium",
        nullable=False
    )
    
    # Due date
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Foreign keys
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    assigned_to_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Tags (PostgreSQL native array)
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        default=list
    )
    
    # Soft delete
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    owner: Mapped["User"] = relationship(
        "User",
        foreign_keys=[owner_id],
        back_populates="owned_tasks"
    )
    
    assigned_to: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_to_id],
        back_populates="assigned_tasks"
    )
    
    team: Mapped[Optional["Team"]] = relationship(
        "Team",
        back_populates="tasks"
    )
    
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="Comment.created_at"
    )
    
    attachments: Mapped[List["Attachment"]] = relationship(
        "Attachment",
        back_populates="task",
        cascade="all, delete-orphan"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("ix_tasks_owner_id", "owner_id"),
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_priority", "priority"),
        Index("ix_tasks_due_date", "due_date"),
        Index("ix_tasks_team_id", "team_id"),
        Index("ix_tasks_assigned_to_id", "assigned_to_id"),
        Index("ix_tasks_is_archived", "is_archived"),
        Index("ix_tasks_owner_status", "owner_id", "status"),
        Index("ix_tasks_created_at", "created_at"),
    )
