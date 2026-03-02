"""
Team service for TaskMaster Pro.
Handles business logic for team operations.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    ConflictException
)
from app.crud.team import team as team_crud, team_member as team_member_crud
from app.crud.user import user as user_crud
from app.models.team import Team, TeamMember
from app.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate, TeamMemberCreate, TeamMemberRoleUpdate
from app.services.notification_service import notification_service
from app.services.activity_service import activity_service


class TeamService:
    """Service for team operations."""
    
    async def create_team(
        self,
        db: AsyncSession,
        *,
        team_in: TeamCreate,
        owner: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Team:
        """
        Create a new team.
        
        Args:
            db: Database session
            team_in: Team creation data
            owner: Team owner
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            Created team
        """
        # Create team directly with owner_id (don't re-wrap in TeamCreate which drops owner_id)
        from app.models.team import Team
        from uuid import uuid4
        team_data = team_in.model_dump()
        db_team = Team(
            id=uuid4(),
            owner_id=owner.id,
            name=team_data.get("name"),
            description=team_data.get("description")
        )
        db.add(db_team)
        await db.flush()
        team_id = db_team.id
        
        # Re-fetch with eager-loaded relationships to avoid MissingGreenlet during response serialization
        from app.crud.team import team as team_crud
        team = await team_crud.get(db, id=team_id)
        
        # Log activity
        await activity_service.log(
            db,
            user_id=owner.id,
            action="team_created",
            entity_type="team",
            entity_id=team.id,
            meta={"name": team.name},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return team
    
    async def update_team(
        self,
        db: AsyncSession,
        *,
        team_id: UUID,
        team_in: TeamUpdate,
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Team:
        """
        Update a team.
        
        Args:
            db: Database session
            team_id: Team ID
            team_in: Team update data
            current_user: Current user
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            Updated team
        
        Raises:
            NotFoundException: If team not found
            PermissionDeniedException: If user cannot update team
        """
        team = await team_crud.get(db, id=team_id)
        
        if not team:
            raise NotFoundException("Team", str(team_id))
        
        # Only owner or admin can update
        if team.owner_id != current_user.id and current_user.role != "admin":
            raise PermissionDeniedException("Only team owner can update the team")
        
        team = await team_crud.update(db, db_obj=team, obj_in=team_in)
        
        # Log activity
        await activity_service.log(
            db,
            user_id=current_user.id,
            action="team_updated",
            entity_type="team",
            entity_id=team.id,
            meta={"name": team.name},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return team
    
    async def delete_team(
        self,
        db: AsyncSession,
        *,
        team_id: UUID,
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Team:
        """
        Delete a team.
        
        Args:
            db: Database session
            team_id: Team ID
            current_user: Current user
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            Deleted team
        
        Raises:
            NotFoundException: If team not found
            PermissionDeniedException: If user cannot delete team
        """
        team = await team_crud.get(db, id=team_id)
        
        if not team:
            raise NotFoundException("Team", str(team_id))
        
        # Only owner or admin can delete
        if team.owner_id != current_user.id and current_user.role != "admin":
            raise PermissionDeniedException("Only team owner can delete the team")
        
        await team_crud.remove(db, id=team_id)
        
        # Log activity
        await activity_service.log(
            db,
            user_id=current_user.id,
            action="team_deleted",
            entity_type="team",
            entity_id=team_id,
            meta={"name": team.name},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return team
    
    async def invite_member(
        self,
        db: AsyncSession,
        *,
        team_id: UUID,
        user_id: UUID,
        role: str = "member",
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TeamMember:
        """
        Invite a member to a team.
        
        Args:
            db: Database session
            team_id: Team ID
            user_id: User ID to invite
            role: Member role (member/manager)
            current_user: Current user
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            Created team member
        
        Raises:
            NotFoundException: If team or user not found
            PermissionDeniedException: If user cannot invite members
            ConflictException: If user is already a member
        """
        team = await team_crud.get(db, id=team_id)
        
        if not team:
            raise NotFoundException("Team", str(team_id))
        
        # Check if user to invite exists
        user_to_invite = await user_crud.get(db, id=user_id)
        if not user_to_invite:
            raise NotFoundException("User", str(user_id))
        
        # Only owner or manager can invite
        can_invite = (
            team.owner_id == current_user.id or
            current_user.role == "admin" or
            await team_member_crud.is_manager(db, team_id=team_id, user_id=current_user.id)
        )
        
        if not can_invite:
            raise PermissionDeniedException("You don't have permission to invite members")
        
        # Check if already a member
        existing_member = await team_member_crud.get(db, team_id=team_id, user_id=user_id)
        if existing_member:
            raise ConflictException("User is already a team member")
        
        # Add member
        member = await team_member_crud.create(
            db,
            obj_in=TeamMemberCreate(team_id=team_id, user_id=user_id, role=role)
        )
        
        # Notify invited user
        await notification_service.notify_user(
            db,
            user_id=user_id,
            message=f"You have been invited to join team: {team.name}",
            type="team_invitation",
            reference_id=team.id,
            reference_type="team"
        )
        
        # Log activity
        await activity_service.log(
            db,
            user_id=current_user.id,
            action="team_member_invited",
            entity_type="team_member",
            entity_id=team_id,
            meta={
                "team_id": str(team_id),
                "user_id": str(user_id),
                "role": role
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return member
    
    async def remove_member(
        self,
        db: AsyncSession,
        *,
        team_id: UUID,
        user_id: UUID,
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[TeamMember]:
        """
        Remove a member from a team.
        
        Args:
            db: Database session
            team_id: Team ID
            user_id: User ID to remove
            current_user: Current user
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            Removed team member or None
        
        Raises:
            NotFoundException: If team not found
            PermissionDeniedException: If user cannot remove members
        """
        team = await team_crud.get(db, id=team_id)
        
        if not team:
            raise NotFoundException("Team", str(team_id))
        
        # Owner can remove anyone, users can remove themselves
        can_remove = (
            team.owner_id == current_user.id or
            current_user.role == "admin" or
            current_user.id == user_id or
            await team_member_crud.is_manager(db, team_id=team_id, user_id=current_user.id)
        )
        
        if not can_remove:
            raise PermissionDeniedException("You don't have permission to remove members")
        
        # Cannot remove owner
        if user_id == team.owner_id:
            raise PermissionDeniedException("Cannot remove team owner")
        
        member = await team_member_crud.remove(db, team_id=team_id, user_id=user_id)
        
        if member:
            # Log activity
            await activity_service.log(
                db,
                user_id=current_user.id,
                action="team_member_removed",
                entity_type="team_member",
                entity_id=team_id,
                meta={
                    "team_id": str(team_id),
                    "user_id": str(user_id)
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
        
        return member
    
    async def update_member_role(
        self,
        db: AsyncSession,
        *,
        team_id: UUID,
        user_id: UUID,
        role_update: TeamMemberRoleUpdate,
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[TeamMember]:
        """
        Update a team member's role.
        
        Args:
            db: Database session
            team_id: Team ID
            user_id: User ID
            role_update: Role update data
            current_user: Current user
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            Updated team member or None
        
        Raises:
            NotFoundException: If team not found
            PermissionDeniedException: If user cannot update roles
        """
        team = await team_crud.get(db, id=team_id)
        
        if not team:
            raise NotFoundException("Team", str(team_id))
        
        # Only owner or admin can update roles
        if team.owner_id != current_user.id and current_user.role != "admin":
            raise PermissionDeniedException("Only team owner can update member roles")
        
        # Cannot update owner's role
        if user_id == team.owner_id:
            raise PermissionDeniedException("Cannot change team owner's role")
        
        member = await team_member_crud.update_role(
            db,
            team_id=team_id,
            user_id=user_id,
            new_role=role_update.role
        )
        
        if member:
            # Log activity
            await activity_service.log(
                db,
                user_id=current_user.id,
                action="team_member_role_updated",
                entity_type="team_member",
                entity_id=team_id,
                meta={
                    "team_id": str(team_id),
                    "user_id": str(user_id),
                    "new_role": role_update.role
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
        
        return member
    
    async def get_team(
        self,
        db: AsyncSession,
        *,
        team_id: UUID,
        current_user: User
    ) -> Team:
        """
        Get a team by ID.
        
        Args:
            db: Database session
            team_id: Team ID
            current_user: Current user
        
        Returns:
            Team
        
        Raises:
            NotFoundException: If team not found
            PermissionDeniedException: If user cannot view team
        """
        team = await team_crud.get(db, id=team_id)
        
        if not team:
            raise NotFoundException("Team", str(team_id))
        
        # Check if user is owner or member
        is_member = await team_member_crud.is_member(
            db, team_id=team_id, user_id=current_user.id
        )
        
        if team.owner_id != current_user.id and not is_member and current_user.role != "admin":
            raise PermissionDeniedException("You don't have access to this team")
        
        return team
    
    async def list_user_teams(
        self,
        db: AsyncSession,
        *,
        user: User,
        skip: int = 0,
        limit: int = 100
    ) -> List[Team]:
        """
        List teams for a user.
        
        Args:
            db: Database session
            user: User
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            List of teams
        """
        return await team_crud.get_user_teams(
            db, user_id=user.id, skip=skip, limit=limit
        )


# Global instance
team_service = TeamService()
