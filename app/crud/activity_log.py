"""
CRUD operations for ActivityLog model.
"""

from typing import List
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.activity_log import ActivityLog
from app.schemas.activity_log import ActivityLogCreate


class CRUDActivityLog(CRUDBase[ActivityLog, ActivityLogCreate, None]):
    """CRUD operations for ActivityLog model."""
    
    async def get_multi_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ActivityLog]:
        """
        Get activity logs for a user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            List of activity logs
        """
        result = await db.execute(
            select(ActivityLog)
            .where(ActivityLog.user_id == user_id)
            .order_by(ActivityLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_multi_by_entity(
        self,
        db: AsyncSession,
        *,
        entity_type: str,
        entity_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[ActivityLog]:
        """
        Get activity logs for an entity.
        
        Args:
            db: Database session
            entity_type: Entity type
            entity_id: Entity ID
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            List of activity logs
        """
        result = await db.execute(
            select(ActivityLog)
            .where(
                and_(
                    ActivityLog.entity_type == entity_type,
                    ActivityLog.entity_id == entity_id
                )
            )
            .order_by(ActivityLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_multi_by_action(
        self,
        db: AsyncSession,
        *,
        action: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[ActivityLog]:
        """
        Get activity logs by action type.
        
        Args:
            db: Database session
            action: Action type
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            List of activity logs
        """
        result = await db.execute(
            select(ActivityLog)
            .where(ActivityLog.action == action)
            .order_by(ActivityLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


activity_log = CRUDActivityLog(ActivityLog)
