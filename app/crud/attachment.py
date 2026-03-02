"""
CRUD operations for Attachment model.
"""

from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.attachment import Attachment
from app.schemas.attachment import AttachmentCreate


class CRUDAttachment(CRUDBase[Attachment, AttachmentCreate, None]):
    """CRUD operations for Attachment model."""
    
    async def get_multi_by_task(
        self,
        db: AsyncSession,
        *,
        task_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Attachment]:
        """
        Get attachments by task ID.
        
        Args:
            db: Database session
            task_id: Task ID
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            List of attachments for the task
        """
        result = await db.execute(
            select(Attachment)
            .where(Attachment.task_id == task_id)
            .order_by(Attachment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def count_by_task(
        self,
        db: AsyncSession,
        *,
        task_id: UUID
    ) -> int:
        """
        Count attachments for a task.
        
        Args:
            db: Database session
            task_id: Task ID
        
        Returns:
            Number of attachments
        """
        from sqlalchemy import func
        
        result = await db.execute(
            select(func.count(Attachment.id))
            .where(Attachment.task_id == task_id)
        )
        return result.scalar()
    
    async def get_multi_by_uploader(
        self,
        db: AsyncSession,
        *,
        uploaded_by: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Attachment]:
        """
        Get attachments by uploader ID.
        
        Args:
            db: Database session
            uploaded_by: Uploader user ID
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            List of attachments uploaded by the user
        """
        result = await db.execute(
            select(Attachment)
            .where(Attachment.uploaded_by == uploaded_by)
            .order_by(Attachment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


attachment = CRUDAttachment(Attachment)
