"""
CRUD operations for Team and TeamMember models.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.team import Team, TeamMember
from app.schemas.team import TeamCreate, TeamUpdate, TeamMemberCreate


class CRUDTeam(CRUDBase[Team, TeamCreate, TeamUpdate]):
    """CRUD operations for Team model."""
    
    async def get(self, db: AsyncSession, *, id: UUID) -> Optional[Team]:
        """Get a team by ID with eagerly loaded relationships."""
        result = await db.execute(
            select(Team)
            .where(Team.id == id)
            .options(
                selectinload(Team.owner),
                selectinload(Team.members).selectinload(TeamMember.user),
            )
        )
        return result.scalar_one_or_none()
    
    async def get_multi_by_owner(
        self,
        db: AsyncSession,
        *,
        owner_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Team]:
        """
        Get teams by owner ID.
        """
        result = await db.execute(
            select(Team)
            .where(Team.owner_id == owner_id)
            .options(
                selectinload(Team.owner),
                selectinload(Team.members).selectinload(TeamMember.user),
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_multi_by_member(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Team]:
        """
        Get teams where user is a member.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            List of teams the user is a member of
        """
        result = await db.execute(
            select(Team)
            .join(TeamMember, Team.id == TeamMember.team_id)
            .where(TeamMember.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_user_teams(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Team]:
        """
        Get all teams related to a user (owned or member).
        """
        from sqlalchemy import or_
        
        result = await db.execute(
            select(Team)
            .outerjoin(TeamMember, Team.id == TeamMember.team_id)
            .where(
                or_(
                    Team.owner_id == user_id,
                    TeamMember.user_id == user_id
                )
            )
            .options(
                selectinload(Team.owner),
                selectinload(Team.members).selectinload(TeamMember.user),
            )
            .distinct()
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


class CRUDTeamMember:
    """CRUD operations for TeamMember model."""
    
    async def get(
        self,
        db: AsyncSession,
        *,
        team_id: UUID,
        user_id: UUID
    ) -> Optional[TeamMember]:
        """
        Get a team member by team ID and user ID.
        
        Args:
            db: Database session
            team_id: Team ID
            user_id: User ID
        
        Returns:
            TeamMember instance or None
        """
        result = await db.execute(
            select(TeamMember)
            .where(
                and_(
                    TeamMember.team_id == team_id,
                    TeamMember.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_multi_by_team(
        self,
        db: AsyncSession,
        *,
        team_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TeamMember]:
        """
        Get all members of a team.
        
        Args:
            db: Database session
            team_id: Team ID
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            List of team members
        """
        result = await db.execute(
            select(TeamMember)
            .where(TeamMember.team_id == team_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: TeamMemberCreate
    ) -> TeamMember:
        """
        Add a member to a team.
        """
        db_obj = TeamMember(
            team_id=obj_in.team_id,
            user_id=obj_in.user_id,
            role=obj_in.role
        )
        db.add(db_obj)
        await db.flush()
        
        # Re-fetch with eager-loaded user relationship to avoid MissingGreenlet
        result = await db.execute(
            select(TeamMember)
            .where(
                and_(
                    TeamMember.team_id == obj_in.team_id,
                    TeamMember.user_id == obj_in.user_id
                )
            )
            .options(selectinload(TeamMember.user))
        )
        return result.scalar_one()
    
    async def update_role(
        self,
        db: AsyncSession,
        *,
        team_id: UUID,
        user_id: UUID,
        new_role: str
    ) -> Optional[TeamMember]:
        """
        Update a team member's role.
        
        Args:
            db: Database session
            team_id: Team ID
            user_id: User ID
            new_role: New role value
        
        Returns:
            Updated team member or None
        """
        member = await self.get(db, team_id=team_id, user_id=user_id)
        if member:
            member.role = new_role
            db.add(member)
            await db.flush()
            await db.refresh(member)
        return member
    
    async def remove(
        self,
        db: AsyncSession,
        *,
        team_id: UUID,
        user_id: UUID
    ) -> Optional[TeamMember]:
        """
        Remove a member from a team.
        
        Args:
            db: Database session
            team_id: Team ID
            user_id: User ID
        
        Returns:
            Removed team member or None
        """
        member = await self.get(db, team_id=team_id, user_id=user_id)
        if member:
            await db.delete(member)
            await db.flush()
        return member
    
    async def is_member(
        self,
        db: AsyncSession,
        *,
        team_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Check if a user is a member of a team.
        
        Args:
            db: Database session
            team_id: Team ID
            user_id: User ID
        
        Returns:
            True if user is a member, False otherwise
        """
        member = await self.get(db, team_id=team_id, user_id=user_id)
        return member is not None
    
    async def is_manager(
        self,
        db: AsyncSession,
        *,
        team_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Check if a user is a manager of a team.
        
        Args:
            db: Database session
            team_id: Team ID
            user_id: User ID
        
        Returns:
            True if user is a manager, False otherwise
        """
        member = await self.get(db, team_id=team_id, user_id=user_id)
        return member is not None and member.role == "manager"


team = CRUDTeam(Team)
team_member = CRUDTeamMember()
