"""
CRUD operations for Notification model.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationFilter


class CRUDNotification(CRUDBase[Notification, NotificationCreate, None]):
    """CRUD operations for Notification model."""
    
    async def get_multi_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        unread_only: bool = False
    ) -> List[Notification]:
        """
        Get notifications for a user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records
            unread_only: If True, only return unread notifications
        
        Returns:
            List of notifications
        """
        query = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            query = query.where(Notification.is_read == False)
        
        query = query.order_by(Notification.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_with_filters(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        filters: NotificationFilter,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Notification], int]:
        """
        Get notifications with filters.
        
        Args:
            db: Database session
            user_id: User ID
            filters: NotificationFilter with filter criteria
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            Tuple of (list of notifications, total count)
        """
        query = select(Notification).where(Notification.user_id == user_id)
        
        # Apply filters
        if filters.is_read is not None:
            query = query.where(Notification.is_read == filters.is_read)
        
        if filters.type:
            query = query.where(Notification.type == filters.type)
        
        # Get total count
        count_query = select(func.count(Notification.id)).where(Notification.user_id == user_id)
        if filters.is_read is not None:
            count_query = count_query.where(Notification.is_read == filters.is_read)
        if filters.type:
            count_query = count_query.where(Notification.type == filters.type)
        
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # Apply pagination
        query = query.order_by(Notification.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all()), total
    
    async def count_unread(
        self,
        db: AsyncSession,
        *,
        user_id: UUID
    ) -> int:
        """
        Count unread notifications for a user.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            Number of unread notifications
        """
        result = await db.execute(
            select(func.count(Notification.id))
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
        )
        return result.scalar()
    
    async def mark_as_read(
        self,
        db: AsyncSession,
        *,
        notification_id: UUID,
        user_id: UUID
    ) -> Optional[Notification]:
        """
        Mark a notification as read.
        
        Args:
            db: Database session
            notification_id: Notification ID
            user_id: User ID (for verification)
        
        Returns:
            Updated notification or None
        """
        result = await db.execute(
            select(Notification)
            .where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == user_id
                )
            )
        )
        notification = result.scalar_one_or_none()
        
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.add(notification)
            await db.flush()
            await db.refresh(notification)
        
        return notification
    
    async def mark_all_as_read(
        self,
        db: AsyncSession,
        *,
        user_id: UUID
    ) -> int:
        """
        Mark all notifications as read for a user.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            Number of notifications marked as read
        """
        result = await db.execute(
            select(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
        )
        notifications = result.scalars().all()
        
        now = datetime.utcnow()
        for notification in notifications:
            notification.is_read = True
            notification.read_at = now
            db.add(notification)
        
        await db.flush()
        return len(notifications)
    
    async def get_by_reference(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        reference_type: str,
        reference_id: UUID
    ) -> List[Notification]:
        """
        Get notifications by reference.
        
        Args:
            db: Database session
            user_id: User ID
            reference_type: Reference entity type
            reference_id: Reference entity ID
        
        Returns:
            List of notifications
        """
        result = await db.execute(
            select(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.reference_type == reference_type,
                    Notification.reference_id == reference_id
                )
            )
            .order_by(Notification.created_at.desc())
        )
        return result.scalars().all()


notification = CRUDNotification(Notification)
