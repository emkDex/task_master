"""
Notification service for TaskMaster Pro.
Handles notification creation and WebSocket push.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.notification import notification as notification_crud
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate
from app.services.websocket_service import websocket_manager


class NotificationService:
    """Service for notification operations."""
    
    async def notify_user(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        message: str,
        type: str,
        reference_id: Optional[UUID] = None,
        reference_type: Optional[str] = None
    ) -> Notification:
        """
        Create a notification for a user and push via WebSocket if connected.
        
        Args:
            db: Database session
            user_id: User ID to notify
            message: Notification message
            type: Notification type
            reference_id: Optional reference entity ID
            reference_type: Optional reference entity type
        
        Returns:
            Created notification
        """
        # Create notification in database
        notification = await notification_crud.create(
            db,
            obj_in=NotificationCreate(
                user_id=user_id,
                message=message,
                type=type,
                reference_id=reference_id,
                reference_type=reference_type
            )
        )
        
        # Push via WebSocket if user is connected
        await self._push_websocket_notification(user_id, notification)
        
        return notification
    
    async def notify_multiple_users(
        self,
        db: AsyncSession,
        *,
        user_ids: List[UUID],
        message: str,
        type: str,
        reference_id: Optional[UUID] = None,
        reference_type: Optional[str] = None
    ) -> List[Notification]:
        """
        Create notifications for multiple users.
        
        Args:
            db: Database session
            user_ids: List of user IDs to notify
            message: Notification message
            type: Notification type
            reference_id: Optional reference entity ID
            reference_type: Optional reference entity type
        
        Returns:
            List of created notifications
        """
        notifications = []
        
        for user_id in user_ids:
            notification = await self.notify_user(
                db,
                user_id=user_id,
                message=message,
                type=type,
                reference_id=reference_id,
                reference_type=reference_type
            )
            notifications.append(notification)
        
        return notifications
    
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
        return await notification_crud.mark_as_read(
            db, notification_id=notification_id, user_id=user_id
        )
    
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
        return await notification_crud.mark_all_as_read(db, user_id=user_id)
    
    async def get_user_notifications(
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
        return await notification_crud.get_multi_by_user(
            db,
            user_id=user_id,
            skip=skip,
            limit=limit,
            unread_only=unread_only
        )
    
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
        return await notification_crud.count_unread(db, user_id=user_id)
    
    async def _push_websocket_notification(
        self,
        user_id: UUID,
        notification: Notification
    ) -> None:
        """
        Push notification to user via WebSocket if connected.
        
        Args:
            user_id: User ID
            notification: Notification to push
        """
        message = {
            "type": "notification",
            "data": {
                "id": str(notification.id),
                "message": notification.message,
                "notification_type": notification.type,
                "reference_id": str(notification.reference_id) if notification.reference_id else None,
                "reference_type": notification.reference_type,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat() if notification.created_at else None
            }
        }
        
        await websocket_manager.send_personal_message(message, str(user_id))


# Global instance
notification_service = NotificationService()
