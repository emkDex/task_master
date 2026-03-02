"""
Activity Log API routes for TaskMaster Pro.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, require_admin
from app.models.user import User
from app.schemas.activity_log import ActivityLogRead
from app.schemas.pagination import PaginatedResponse
from app.services.activity_service import activity_service
from app.crud.activity_log import activity_log as activity_log_crud

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedResponse[ActivityLogRead],
    summary="My activity",
    description="Get activity logs for the current user."
)
async def get_my_activity(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[ActivityLogRead]:
    """
    Get activity logs for the current user.
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records
    """
    activities = await activity_log_crud.get_multi_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    
    # Get total count
    from sqlalchemy import func
    from app.models.activity_log import ActivityLog
    
    result = await db.execute(
        select(func.count(ActivityLog.id))
        .where(ActivityLog.user_id == current_user.id)
    )
    total = result.scalar()
    
    pages = (total + limit - 1) // limit if limit > 0 else 1
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return PaginatedResponse(
        items=activities,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


@router.get(
    "/task/{task_id}",
    response_model=PaginatedResponse[ActivityLogRead],
    summary="Task activity",
    description="Get activity logs for a specific task."
)
async def get_task_activity(
    task_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[ActivityLogRead]:
    """
    Get activity logs for a task.
    
    - **task_id**: UUID of the task
    """
    # Check if user has access to task
    from app.crud.task import task as task_crud
    from app.core.exceptions import NotFoundException, PermissionDeniedException
    from app.crud.team import team_member as team_member_crud
    
    task = await task_crud.get(db, id=task_id)
    if not task:
        raise NotFoundException("Task", str(task_id))
    
    # Check access
    has_access = (
        task.owner_id == current_user.id or
        task.assigned_to_id == current_user.id or
        current_user.role == "admin"
    )
    
    if task.team_id:
        is_member = await team_member_crud.is_member(
            db, team_id=task.team_id, user_id=current_user.id
        )
        if is_member:
            has_access = True
    
    if not has_access:
        raise PermissionDeniedException("You don't have access to this task")
    
    activities = await activity_log_crud.get_multi_by_entity(
        db, entity_type="task", entity_id=task_id, skip=skip, limit=limit
    )
    
    # Get total count
    from sqlalchemy import func, and_
    from app.models.activity_log import ActivityLog
    
    result = await db.execute(
        select(func.count(ActivityLog.id))
        .where(
            and_(
                ActivityLog.entity_type == "task",
                ActivityLog.entity_id == task_id
            )
        )
    )
    total = result.scalar()
    
    pages = (total + limit - 1) // limit if limit > 0 else 1
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return PaginatedResponse(
        items=activities,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


@router.get(
    "/admin",
    response_model=PaginatedResponse[ActivityLogRead],
    summary="All activity (Admin)",
    description="Get all activity logs. Admin only."
)
async def get_all_activity(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_id: UUID = Query(None, description="Filter by user"),
    entity_type: str = Query(None, description="Filter by entity type"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[ActivityLogRead]:
    """
    Get all activity logs (admin only).
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records
    - **user_id**: Optional filter by user
    - **entity_type**: Optional filter by entity type
    """
    from sqlalchemy import select, func, and_
    from app.models.activity_log import ActivityLog
    
    query = select(ActivityLog)
    count_query = select(func.count(ActivityLog.id))
    
    conditions = []
    
    if user_id:
        conditions.append(ActivityLog.user_id == user_id)
    
    if entity_type:
        conditions.append(ActivityLog.entity_type == entity_type)
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    # Apply pagination
    query = query.order_by(ActivityLog.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    activities = result.scalars().all()
    
    pages = (total + limit - 1) // limit if limit > 0 else 1
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return PaginatedResponse(
        items=list(activities),
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


# Need to import select for queries
from sqlalchemy import select, func, and_
