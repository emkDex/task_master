"""
Attachment model for TaskMaster Pro.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, ForeignKey, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.task import Task


class Attachment(Base):
    """Attachment model for task file attachments."""
    
    __tablename__ = "attachments"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # File info
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    file_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    
    # Foreign keys
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="attachments"
    )
    
    uploaded_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="attachments"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_attachments_task_id", "task_id"),
        Index("ix_attachments_uploaded_by", "uploaded_by"),
        Index("ix_attachments_created_at", "created_at"),
    )
