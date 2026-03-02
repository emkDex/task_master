"""
Activity logging service for TaskMaster Pro.
Handles async activity log creation.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.activity_log import ActivityLog
from app.schemas.activity_log import ActivityLogCreate


class ActivityService:
    """Service for activity logging operations."""
    
    async def log(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        action: str,
        entity_type: str,
        entity_id: UUID,
        meta: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """
        Log an activity.
        
        Args:
            db: Database session
            user_id: User ID who performed the action
            action: Action performed (e.g., "task_created")
            entity_type: Type of entity affected (e.g., "task")
            entity_id: ID of entity affected
            meta: Optional additional metadata
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            Created activity log entry
        """
        # Create activity log
        activity_log = ActivityLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            meta=meta or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(activity_log)
        await db.flush()
        await db.refresh(activity_log)
        
        return activity_log
    
    async def get_user_activity(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[ActivityLog]:
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
    
    async def get_entity_activity(
        self,
        db: AsyncSession,
        *,
        entity_type: str,
        entity_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[ActivityLog]:
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
        from sqlalchemy import select, and_
        
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


# Global instance
activity_service = ActivityService()
