"""
ActivityLog model for TaskMaster Pro.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Any, Dict

from sqlalchemy import String, DateTime, ForeignKey, Index, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class ActivityLog(Base):
    """ActivityLog model for tracking user actions."""
    
    __tablename__ = "activity_logs"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Action performed
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    
    # Entity information
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    
    entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        nullable=False
    )
    
    # Foreign key to user who performed the action
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Additional metadata (JSONB for PostgreSQL)
    meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict
    )
    
    # IP address and user agent (for audit)
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True
    )
    
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="activity_logs"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index("ix_activity_logs_user_id", "user_id"),
        Index("ix_activity_logs_entity", "entity_type", "entity_id"),
        Index("ix_activity_logs_action", "action"),
        Index("ix_activity_logs_created_at", "created_at"),
        Index("ix_activity_logs_user_created", "user_id", "created_at"),
    )
