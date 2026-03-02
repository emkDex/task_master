"""
Task API routes for TaskMaster Pro.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskRead,
    TaskUpdate,
    TaskFilter,
    TaskAssignRequest,
    TaskListItem
)
from app.schemas.pagination import PaginatedResponse
from app.services.task_service import task_service

router = APIRouter()


@router.get(
    "/",
    response_model=PaginatedResponse[TaskListItem],
    summary="List tasks",
    description="Get a paginated list of tasks with optional filtering."
)
async def list_tasks(
    request: Request,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records"),
    status: str = Query(None, description="Filter by status"),
    priority: str = Query(None, description="Filter by priority"),
    assigned_to_id: UUID = Query(None, description="Filter by assignee"),
    team_id: UUID = Query(None, description="Filter by team"),
    search: str = Query(None, description="Search in title and description"),
    is_archived: bool = Query(False, description="Include archived tasks"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[TaskListItem]:
    """
    List tasks with filtering and pagination.
    
    - Regular users see only their own tasks (owned or assigned)
    - Admins see all tasks
    """
    filters = TaskFilter(
        status=status,
        priority=priority,
        assigned_to_id=assigned_to_id,
        team_id=team_id,
        search=search,
        is_archived=is_archived
    )
    
    tasks, total = await task_service.list_tasks(
        db,
        filters=filters,
        current_user=current_user,
        skip=skip,
        limit=limit
    )
    
    pages = (total + limit - 1) // limit if limit > 0 else 1
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return PaginatedResponse(
        items=tasks,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )


@router.post(
    "/",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create task",
    description="Create a new task."
)
async def create_task(
    request: Request,
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskRead:
    """
    Create a new task.
    
    - **title**: Task title (required)
    - **description**: Task description (optional)
    - **status**: pending, in_progress, completed, cancelled (default: pending)
    - **priority**: low, medium, high, critical (default: medium)
    - **due_date**: Due date in ISO format (optional)
    - **assigned_to_id**: UUID of assignee (optional)
    - **team_id**: UUID of team (optional)
    - **tags**: List of tags (optional)
    """
    task = await task_service.create_task(
        db,
        task_in=task_in,
        owner=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return task


@router.get(
    "/{task_id}",
    response_model=TaskRead,
    summary="Get task",
    description="Get a specific task by ID."
)
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskRead:
    """
    Get task by ID.
    
    - **task_id**: UUID of the task
    """
    task = await task_service.get_task(
        db,
        task_id=task_id,
        current_user=current_user
    )
    return task


@router.put(
    "/{task_id}",
    response_model=TaskRead,
    summary="Update task",
    description="Update a task. Only owner, team managers, or admins can update."
)
async def update_task(
    request: Request,
    task_id: UUID,
    task_in: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskRead:
    """
    Update a task.
    
    - **task_id**: UUID of the task to update
    - All fields are optional - only provided fields will be updated
    """
    task = await task_service.update_task(
        db,
        task_id=task_id,
        task_in=task_in,
        current_user=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive task",
    description="Soft delete (archive) a task. Only owner or admins can delete."
)
async def delete_task(
    request: Request,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Archive a task (soft delete).
    
    - **task_id**: UUID of the task to archive
    """
    await task_service.delete_task(
        db,
        task_id=task_id,
        current_user=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )


@router.post(
    "/{task_id}/assign",
    response_model=TaskRead,
    summary="Assign task",
    description="Assign a task to a user."
)
async def assign_task(
    request: Request,
    task_id: UUID,
    assign_data: TaskAssignRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskRead:
    """
    Assign a task to a user.
    
    - **task_id**: UUID of the task
    - **assigned_to_id**: UUID of the user to assign to
    """
    task = await task_service.assign_task(
        db,
        task_id=task_id,
        assign_data=assign_data,
        current_user=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return task


@router.get(
    "/team/{team_id}",
    response_model=PaginatedResponse[TaskListItem],
    summary="List team tasks",
    description="Get tasks for a specific team."
)
async def list_team_tasks(
    team_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[TaskListItem]:
    """
    List tasks for a team.
    
    - **team_id**: UUID of the team
    """
    from app.crud.task import task as task_crud
    from app.services.team_service import team_service
    
    # Verify user has access to team
    await team_service.get_team(db, team_id=team_id, current_user=current_user)
    
    tasks = await task_crud.get_multi_by_team(
        db, team_id=team_id, skip=skip, limit=limit
    )
    
    total = len(tasks)  # Simplified - in production, use count query
    pages = (total + limit - 1) // limit if limit > 0 else 1
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return PaginatedResponse(
        items=tasks,
        total=total,
        page=page,
        size=limit,
        pages=pages
    )
