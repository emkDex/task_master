"""
Admin API routes for TaskMaster Pro.
"""

from typing import List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_admin
from app.models.user import User
from app.schemas.task import TaskRead, TaskListItem
from app.schemas.user import UserAdminRead
from app.schemas.pagination import PaginatedResponse
from app.crud.user import user as user_crud
from app.crud.task import task as task_crud
from app.crud.team import team as team_crud

router = APIRouter()


@router.get(
    "/stats",
    response_model=Dict[str, Any],
    summary="Dashboard stats",
    description="Get dashboard statistics. Admin only."
)
async def get_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get dashboard statistics (admin only).
    
    Returns:
        - Total users
        - Tasks by status
        - Active teams count
        - Recent activity summary
    """
    from sqlalchemy import func
    from app.models.user import User
    from app.models.task import Task
    from app.models.team import Team
    
    # Get total users
    total_users = await user_crud.count(db)
    active_users = await user_crud.count(db, is_active=True)
    
    # Get tasks by status
    task_status_counts = await task_crud.count_by_status(db)
    total_tasks = sum(task_status_counts.values())
    
    # Get active teams count
    teams_result = await db.execute(select(func.count(Team.id)))
    total_teams = teams_result.scalar()
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": total_users - active_users
        },
        "tasks": {
            "total": total_tasks,
            "by_status": task_status_counts
        },
        "teams": {
            "total": total_teams
        }
    }


@router.get(
    "/users",
    response_model=PaginatedResponse[UserAdminRead],
    summary="All users (Admin)",
    description="Get all users with statistics. Admin only."
)
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[UserAdminRead]:
    """
    Get all users with statistics (admin only).
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records
    """
    users = await user_crud.get_multi(db, skip=skip, limit=limit)
    
    # Get total count
    total = await user_crud.count(db)
    
    pages = (total + limit - 1) // limit if limit > 0 else 1
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return PaginatedResponse(
        items=users,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


@router.get(
    "/tasks",
    response_model=PaginatedResponse[TaskListItem],
    summary="All tasks (Admin)",
    description="Get all tasks across the system. Admin only."
)
async def get_all_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None, description="Filter by status"),
    priority: str = Query(None, description="Filter by priority"),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[TaskListItem]:
    """
    Get all tasks across the system (admin only).
    
    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records
    - **status**: Optional filter by status
    - **priority**: Optional filter by priority
    """
    from sqlalchemy import select, func, and_
    from app.models.task import Task
    
    query = select(Task)
    count_query = select(func.count(Task.id))
    
    conditions = []
    
    if status:
        conditions.append(Task.status == status)
    
    if priority:
        conditions.append(Task.priority == priority)
    
    if conditions:
        query = query.where(and_(*conditions))
        count_query = count_query.where(and_(*conditions))
    
    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    # Apply pagination
    query = query.order_by(Task.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    pages = (total + limit - 1) // limit if limit > 0 else 1
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return PaginatedResponse(
        items=list(tasks),
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


@router.get(
    "/user-stats/{user_id}",
    response_model=Dict[str, Any],
    summary="User stats (Admin)",
    description="Get detailed statistics for a specific user. Admin only."
)
async def get_user_stats(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed statistics for a user (admin only).
    
    - **user_id**: UUID of the user
    """
    from app.core.exceptions import NotFoundException
    from app.models.task import Task
    from sqlalchemy import func
    
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise NotFoundException("User", str(user_id))
    
    # Get task statistics
    owned_tasks_count = await db.execute(
        select(func.count(Task.id)).where(Task.owner_id == user_id)
    )
    owned_tasks = owned_tasks_count.scalar()
    
    assigned_tasks_count = await db.execute(
        select(func.count(Task.id)).where(Task.assigned_to_id == user_id)
    )
    assigned_tasks = assigned_tasks_count.scalar()
    
    # Get task status breakdown for owned tasks
    task_status_result = await db.execute(
        select(Task.status, func.count(Task.id))
        .where(Task.owner_id == user_id)
        .group_by(Task.status)
    )
    task_status_counts = {row[0]: row[1] for row in task_status_result.all()}
    
    return {
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None
        },
        "tasks": {
            "owned": owned_tasks,
            "assigned": assigned_tasks,
            "by_status": task_status_counts
        }
    }
