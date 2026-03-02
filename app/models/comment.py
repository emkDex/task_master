"""
Comment model for TaskMaster Pro.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Text, DateTime, ForeignKey, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.task import Task


class Comment(Base):
    """Comment model for task comments."""
    
    __tablename__ = "comments"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    
    # Foreign keys
    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    
    author_id: Mapped[uuid.UUID] = mapped_column(
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="comments"
    )
    
    author: Mapped["User"] = relationship(
        "User",
        back_populates="comments"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_comments_task_id", "task_id"),
        Index("ix_comments_author_id", "author_id"),
        Index("ix_comments_created_at", "created_at"),
    )
