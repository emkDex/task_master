"""
Attachment API routes for TaskMaster Pro.
"""

import os
import uuid
from typing import List
from uuid import UUID as PyUUID

from fastapi import APIRouter, Depends, Request, Query, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db, get_current_user
from app.core.exceptions import NotFoundException, PermissionDeniedException, FileUploadException
from app.crud.attachment import attachment as attachment_crud
from app.crud.task import task as task_crud
from app.models.user import User
from app.schemas.attachment import AttachmentRead, FileUploadResponse
from app.services.activity_service import activity_service

router = APIRouter()


async def check_task_access(
    db: AsyncSession,
    task_id: PyUUID,
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
    response_model=List[AttachmentRead],
    summary="List attachments",
    description="Get attachments for a task."
)
async def list_attachments(
    task_id: PyUUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[AttachmentRead]:
    """
    List attachments for a task.
    
    - **task_id**: UUID of the task (from path)
    """
    # Check task access
    await check_task_access(db, task_id=task_id, user=current_user)
    
    attachments = await attachment_crud.get_multi_by_task(
        db, task_id=task_id, skip=skip, limit=limit
    )
    return attachments


@router.post(
    "/",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file",
    description="Upload a file attachment to a task."
)
async def upload_file(
    request: Request,
    task_id: PyUUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> FileUploadResponse:
    """
    Upload a file attachment.
    
    - **task_id**: UUID of the task (from path)
    - **file**: File to upload (max 10MB)
    """
    # Check task access
    await check_task_access(db, task_id=task_id, user=current_user)
    
    # Validate file size
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Convert to bytes
    
    # Read file content
    content = await file.read()
    
    if len(content) > max_size:
        raise FileUploadException(
            f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(settings.UPLOAD_DIR, str(task_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, unique_filename)
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create attachment record
    from app.models.attachment import Attachment
    
    attachment = Attachment(
        filename=file.filename,
        file_url=file_path,
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        task_id=task_id,
        uploaded_by=current_user.id
    )
    db.add(attachment)
    await db.flush()
    await db.refresh(attachment)
    
    # Log activity
    await activity_service.log(
        db,
        user_id=current_user.id,
        action="attachment_uploaded",
        entity_type="attachment",
        entity_id=attachment.id,
        meta={
            "task_id": str(task_id),
            "filename": file.filename,
            "size": len(content)
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    return FileUploadResponse(
        success=True,
        message="File uploaded successfully",
        attachment=attachment
    )


@router.get(
    "/{attachment_id}/download",
    summary="Download file",
    description="Download an attachment file."
)
async def download_file(
    task_id: PyUUID,
    attachment_id: PyUUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download an attachment file.
    
    - **task_id**: UUID of the task (from path)
    - **attachment_id**: UUID of the attachment
    """
    # Check task access
    await check_task_access(db, task_id=task_id, user=current_user)
    
    # Get attachment
    attachment = await attachment_crud.get(db, id=attachment_id)
    
    if not attachment:
        raise NotFoundException("Attachment", str(attachment_id))
    
    if attachment.task_id != task_id:
        raise NotFoundException("Attachment", str(attachment_id))
    
    # Check if file exists
    if not os.path.exists(attachment.file_url):
        raise NotFoundException("File", attachment.filename)
    
    return FileResponse(
        path=attachment.file_url,
        filename=attachment.filename,
        media_type=attachment.mime_type
    )


@router.delete(
    "/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete attachment",
    description="Delete an attachment. Only uploader or admin can delete."
)
async def delete_attachment(
    request: Request,
    task_id: PyUUID,
    attachment_id: PyUUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete an attachment.
    
    - **task_id**: UUID of the task (from path)
    - **attachment_id**: UUID of the attachment
    """
    # Check task access
    await check_task_access(db, task_id=task_id, user=current_user)
    
    # Get attachment
    attachment = await attachment_crud.get(db, id=attachment_id)
    
    if not attachment:
        raise NotFoundException("Attachment", str(attachment_id))
    
    if attachment.task_id != task_id:
        raise NotFoundException("Attachment", str(attachment_id))
    
    # Only uploader or admin can delete
    if attachment.uploaded_by != current_user.id and current_user.role != "admin":
        raise PermissionDeniedException("Only the uploader or admin can delete this attachment")
    
    # Delete file from disk
    if os.path.exists(attachment.file_url):
        os.remove(attachment.file_url)
    
    # Delete attachment record
    await attachment_crud.remove(db, id=attachment_id)
    
    # Log activity
    await activity_service.log(
        db,
        user_id=current_user.id,
        action="attachment_deleted",
        entity_type="attachment",
        entity_id=attachment_id,
        meta={
            "task_id": str(task_id),
            "filename": attachment.filename
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
