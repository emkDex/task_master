"""
Team and TeamMember models for TaskMaster Pro.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Text, DateTime, Enum, ForeignKey, PrimaryKeyConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.task import Task


class Team(Base):
    """Team model for team management."""
    
    __tablename__ = "teams"
    
    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    # Team info
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )
    
    # Owner
    owner_id: Mapped[uuid.UUID] = mapped_column(
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
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_teams"
    )
    
    members: Mapped[List["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan"
    )
    
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="team"
    )


class TeamMember(Base):
    """TeamMember association model for team memberships."""
    
    __tablename__ = "team_members"
    
    # Foreign keys (composite primary key)
    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Role in team
    role: Mapped[str] = mapped_column(
        Enum("member", "manager", name="team_member_role_enum"),
        default="member",
        nullable=False
    )
    
    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Primary key constraint
    __table_args__ = (
        PrimaryKeyConstraint("team_id", "user_id"),
    )
    
    # Relationships
    team: Mapped["Team"] = relationship(
        "Team",
        back_populates="members"
    )
    
    user: Mapped["User"] = relationship(
        "User",
        back_populates="team_memberships"
    )
