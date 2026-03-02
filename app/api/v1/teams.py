"""
Team API routes for TaskMaster Pro.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.team import (
    TeamCreate,
    TeamRead,
    TeamUpdate,
    TeamMemberRead,
    TeamInvitationRequest,
    TeamMemberRoleUpdate
)
from app.services.team_service import team_service

router = APIRouter()


@router.post(
    "/",
    response_model=TeamRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create team",
    description="Create a new team."
)
async def create_team(
    request: Request,
    team_in: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TeamRead:
    """
    Create a new team.
    
    - **name**: Team name (required)
    - **description**: Team description (optional)
    """
    team = await team_service.create_team(
        db,
        team_in=team_in,
        owner=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return team


@router.get(
    "/",
    response_model=List[TeamRead],
    summary="List my teams",
    description="Get a list of teams the current user is a member of."
)
async def list_teams(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[TeamRead]:
    """
    List teams for the current user.
    Includes teams owned by the user and teams they are a member of.
    """
    teams = await team_service.list_user_teams(
        db, user=current_user, skip=skip, limit=limit
    )
    return teams


@router.get(
    "/{team_id}",
    response_model=TeamRead,
    summary="Get team",
    description="Get a specific team by ID."
)
async def get_team(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TeamRead:
    """
    Get team by ID.
    
    - **team_id**: UUID of the team
    """
    team = await team_service.get_team(
        db, team_id=team_id, current_user=current_user
    )
    return team


@router.put(
    "/{team_id}",
    response_model=TeamRead,
    summary="Update team",
    description="Update a team. Only team owner can update."
)
async def update_team(
    request: Request,
    team_id: UUID,
    team_in: TeamUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TeamRead:
    """
    Update a team.
    
    - **team_id**: UUID of the team to update
    - All fields are optional
    """
    team = await team_service.update_team(
        db,
        team_id=team_id,
        team_in=team_in,
        current_user=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return team


@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete team",
    description="Delete a team. Only team owner can delete."
)
async def delete_team(
    request: Request,
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a team.
    
    - **team_id**: UUID of the team to delete
    """
    await team_service.delete_team(
        db,
        team_id=team_id,
        current_user=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )


# Team member routes

@router.post(
    "/{team_id}/members",
    response_model=TeamMemberRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add member",
    description="Add a member to a team."
)
async def add_member(
    request: Request,
    team_id: UUID,
    invitation: TeamInvitationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TeamMemberRead:
    """
    Add a member to a team.
    
    - **team_id**: UUID of the team
    - **user_id**: UUID of the user to add
    - **role**: member or manager (default: member)
    """
    member = await team_service.invite_member(
        db,
        team_id=team_id,
        user_id=invitation.user_id,
        role=invitation.role,
        current_user=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return member


@router.delete(
    "/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove member",
    description="Remove a member from a team."
)
async def remove_member(
    request: Request,
    team_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Remove a member from a team.
    
    - **team_id**: UUID of the team
    - **user_id**: UUID of the user to remove
    """
    await team_service.remove_member(
        db,
        team_id=team_id,
        user_id=user_id,
        current_user=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )


@router.put(
    "/{team_id}/members/{user_id}/role",
    response_model=TeamMemberRead,
    summary="Update member role",
    description="Update a team member's role. Only team owner can update roles."
)
async def update_member_role(
    request: Request,
    team_id: UUID,
    user_id: UUID,
    role_update: TeamMemberRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TeamMemberRead:
    """
    Update a team member's role.
    
    - **team_id**: UUID of the team
    - **user_id**: UUID of the member
    - **role**: member or manager
    """
    member = await team_service.update_member_role(
        db,
        team_id=team_id,
        user_id=user_id,
        role_update=role_update,
        current_user=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return member
