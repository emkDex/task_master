"""
Pydantic schemas for Team and TeamMember models.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.user import UserMinimal


# Team Member schemas
class TeamMemberBase(BaseModel):
    """Base team member schema."""
    role: str = "member"


class TeamMemberCreate(TeamMemberBase):
    """Schema for adding a member to a team."""
    team_id: UUID
    user_id: UUID


class TeamMemberRead(TeamMemberBase):
    """Schema for reading team member data."""
    team_id: UUID
    user_id: UUID
    joined_at: datetime
    user: Optional[UserMinimal] = None
    
    model_config = {"from_attributes": True}


# Team schemas
class TeamBase(BaseModel):
    """Base team schema with common attributes."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class TeamCreate(TeamBase):
    """Schema for creating a new team."""
    pass


class TeamUpdate(BaseModel):
    """Schema for updating a team."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class TeamRead(TeamBase):
    """Schema for reading team data (response)."""
    id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
    
    # Nested relationships
    owner: Optional[UserMinimal] = None
    members: Optional[List[TeamMemberRead]] = None
    member_count: int = 0
    
    model_config = {"from_attributes": True}


class TeamMinimal(BaseModel):
    """Minimal team schema for nested responses."""
    id: UUID
    name: str
    
    model_config = {"from_attributes": True}


# Team invitation schema
class TeamInvitationRequest(BaseModel):
    """Schema for inviting a user to a team."""
    user_id: UUID
    role: str = "member"


# Team member role update schema
class TeamMemberRoleUpdate(BaseModel):
    """Schema for updating a team member's role."""
    role: str = Field(..., pattern="^(member|manager)$")
