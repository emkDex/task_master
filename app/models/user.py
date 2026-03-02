"""
User model for TaskMaster Pro.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, Boolean, DateTime, Enum, Index, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.team import Team, TeamMember
    from app.models.comment import Comment
    from app.models.attachment import Attachment
    from app.models.notification import Notification
    from app.models.activity_log import ActivityLog


class User(Base):
    """User model for authentication and user management."""
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    
    # Profile fields
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    
    # Role and status
    role: Mapped[str] = mapped_column(
        Enum("user", "admin", name="user_role_enum"),
        default="user",
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    
    # Refresh token hash for token rotation
    refresh_token_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
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
    owned_tasks: Mapped[List["Task"]] = relationship(
        "Task",
        foreign_keys="Task.owner_id",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    
    assigned_tasks: Mapped[List["Task"]] = relationship(
        "Task",
        foreign_keys="Task.assigned_to_id",
        back_populates="assigned_to"
    )
    
    owned_teams: Mapped[List["Team"]] = relationship(
        "Team",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    
    team_memberships: Mapped[List["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="author",
        cascade="all, delete-orphan"
    )
    
    attachments: Mapped[List["Attachment"]] = relationship(
        "Attachment",
        back_populates="uploaded_by_user",
        cascade="all, delete-orphan"
    )
    
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    activity_logs: Mapped[List["ActivityLog"]] = relationship(
        "ActivityLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
        Index("ix_users_role", "role"),
    )
