"""
Notification API routes for TaskMaster Pro.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.core.exceptions import NotFoundException
from app.crud.notification import notification as notification_crud
from app.models.user import User
from app.schemas.notification import NotificationRead
from app.schemas.pagination import PaginatedResponse
from app.services.notification_service import notification_service

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedResponse[NotificationRead],
    summary="List notifications",
    description="Get a paginated list of notifications for the current user."
)
async def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False, description="Only show unread notifications"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[NotificationRead]:
    """
    List notifications for the current user.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records
    - **unread_only**: If True, only return unread notifications
    """
    notifications = await notification_crud.get_multi_by_user(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only
    )
    
    total = await notification_crud.count_unread(db, user_id=current_user.id)
    if not unread_only:
        # Get total count including read notifications
        from sqlalchemy import func
        from app.models.notification import Notification
        
        result = await db.execute(
            select(func.count(Notification.id))
            .where(Notification.user_id == current_user.id)
        )
        total = result.scalar()
    
    pages = (total + limit - 1) // limit if limit > 0 else 1
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return PaginatedResponse(
        items=notifications,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


@router.get(
    "/unread-count",
    response_model=dict,
    summary="Get unread count",
    description="Get the number of unread notifications."
)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get count of unread notifications."""
    count = await notification_crud.count_unread(db, user_id=current_user.id)
    return {"unread_count": count}


@router.put(
    "/{notification_id}/read",
    response_model=NotificationRead,
    summary="Mark as read",
    description="Mark a notification as read."
)
async def mark_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationRead:
    """
    Mark a notification as read.
    
    - **notification_id**: UUID of the notification
    """
    notification = await notification_service.mark_as_read(
        db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not notification:
        raise NotFoundException("Notification", str(notification_id))
    
    return notification


@router.put(
    "/read-all",
    response_model=dict,
    summary="Mark all as read",
    description="Mark all notifications as read."
)
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Mark all notifications as read."""
    count = await notification_service.mark_all_as_read(
        db, user_id=current_user.id
    )
    return {"marked_as_read": count}


# Need to import select for the count query
from sqlalchemy import select, func
from app.models.notification import Notification
