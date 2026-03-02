"""
Comment API routes for TaskMaster Pro.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.core.exceptions import NotFoundException, PermissionDeniedException
from app.crud.comment import comment as comment_crud
from app.crud.task import task as task_crud
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentRead, CommentUpdate
from app.services.notification_service import notification_service
from app.services.activity_service import activity_service

router = APIRouter()


async def check_task_access(
    db: AsyncSession,
    task_id: UUID,
    user: User
) -> None:
    """
    Check if user has access to a task.
    
    Raises:
        NotFoundException: If task not found
        PermissionDeniedException: If user cannot access task
    """
    task = await task_crud.get(db, id=task_id)
    
    if not task:
        raise NotFoundException("Task", str(task_id))
    
    # Check access
    has_access = (
        task.owner_id == user.id or
        task.assigned_to_id == user.id or
        user.role == "admin"
    )
    
    if task.team_id:
        from app.crud.team import team_member as team_member_crud
        is_member = await team_member_crud.is_member(
            db, team_id=task.team_id, user_id=user.id
        )
        if is_member:
            has_access = True
    
    if not has_access:
        raise PermissionDeniedException("You don't have access to this task")


@router.get(
    "/",
    response_model=List[CommentRead],
    summary="List comments",
    description="Get comments for a task."
)
async def list_comments(
    task_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[CommentRead]:
    """
    List comments for a task.
    
    - **task_id**: UUID of the task (from path)
    """
    # Check task access
    await check_task_access(db, task_id=task_id, user=current_user)
    
    comments = await comment_crud.get_multi_by_task(
        db, task_id=task_id, skip=skip, limit=limit
    )
    return comments


@router.post(
    "/",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment",
    description="Add a comment to a task."
)
async def create_comment(
    request: Request,
    task_id: UUID,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CommentRead:
    """
    Add a comment to a task.
    
    - **task_id**: UUID of the task (from path)
    - **content**: Comment content
    """
    # Check task access
    await check_task_access(db, task_id=task_id, user=current_user)
    
    # Create comment
    from app.models.comment import Comment
    
    comment = Comment(
        content=comment_in.content,
        task_id=task_id,
        author_id=current_user.id
    )
    db.add(comment)
    await db.flush()
    await db.refresh(comment)
    
    # Notify task owner and assignee
    task = await task_crud.get(db, id=task_id)
    if task:
        if task.owner_id != current_user.id:
            await notification_service.notify_user(
                db,
                user_id=task.owner_id,
                message=f"New comment on task: {task.title}",
                type="comment_added",
                reference_id=task.id,
                reference_type="task"
            )
        
        if task.assigned_to_id and task.assigned_to_id != current_user.id:
            await notification_service.notify_user(
                db,
                user_id=task.assigned_to_id,
                message=f"New comment on task: {task.title}",
                type="comment_added",
                reference_id=task.id,
                reference_type="task"
            )
    
    # Log activity
    await activity_service.log(
        db,
        user_id=current_user.id,
        action="comment_created",
        entity_type="comment",
        entity_id=comment.id,
        meta={"task_id": str(task_id)},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    return comment


@router.put(
    "/{comment_id}",
    response_model=CommentRead,
    summary="Edit comment",
    description="Edit a comment. Only author can edit."
)
async def update_comment(
    request: Request,
    task_id: UUID,
    comment_id: UUID,
    comment_in: CommentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CommentRead:
    """
    Update a comment.
    
    - **task_id**: UUID of the task (from path)
    - **comment_id**: UUID of the comment
    - **content**: New comment content
    """
    # Check task access
    await check_task_access(db, task_id=task_id, user=current_user)
    
    # Get comment
    comment = await comment_crud.get(db, id=comment_id)
    
    if not comment:
        raise NotFoundException("Comment", str(comment_id))
    
    if comment.task_id != task_id:
        raise NotFoundException("Comment", str(comment_id))
    
    # Only author can edit
    if comment.author_id != current_user.id:
        raise PermissionDeniedException("Only the author can edit this comment")
    
    # Update comment
    comment = await comment_crud.update(db, db_obj=comment, obj_in=comment_in)
    
    # Log activity
    await activity_service.log(
        db,
        user_id=current_user.id,
        action="comment_updated",
        entity_type="comment",
        entity_id=comment.id,
        meta={"task_id": str(task_id)},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    return comment


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete comment",
    description="Delete a comment. Only author or admin can delete."
)
async def delete_comment(
    request: Request,
    task_id: UUID,
    comment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a comment.
    
    - **task_id**: UUID of the task (from path)
    - **comment_id**: UUID of the comment
    """
    # Check task access
    await check_task_access(db, task_id=task_id, user=current_user)
    
    # Get comment
    comment = await comment_crud.get(db, id=comment_id)
    
    if not comment:
        raise NotFoundException("Comment", str(comment_id))
    
    if comment.task_id != task_id:
        raise NotFoundException("Comment", str(comment_id))
    
    # Only author or admin can delete
    if comment.author_id != current_user.id and current_user.role != "admin":
        raise PermissionDeniedException("Only the author or admin can delete this comment")
    
    # Delete comment
    await comment_crud.remove(db, id=comment_id)
    
    # Log activity
    await activity_service.log(
        db,
        user_id=current_user.id,
        action="comment_deleted",
        entity_type="comment",
        entity_id=comment_id,
        meta={"task_id": str(task_id)},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
