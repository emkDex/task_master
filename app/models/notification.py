"""
Notification model for TaskMaster Pro.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text, DateTime, Enum, Boolean, ForeignKey, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Notification(Base):
    """Notification model for user notifications."""
    
    __tablename__ = "notifications"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Notification content
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    
    # Notification type
    type: Mapped[str] = mapped_column(
        Enum(
            "task_assigned",
            "task_updated",
            "task_completed",
            "comment_added",
            "team_invitation",
            "mention",
            "system",
            name="notification_type_enum"
        ),
        default="system",
        nullable=False
    )
    
    # Foreign key to user
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Reference to related entity (optional)
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True
    )
    
    # Reference entity type (e.g., "task", "comment", "team")
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    
    # Read status
    is_read: Mapped[bool] = mapped_column(
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
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notifications"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_is_read", "is_read"),
        Index("ix_notifications_user_read", "user_id", "is_read"),
        Index("ix_notifications_created_at", "created_at"),
        Index("ix_notifications_type", "type"),
    )
