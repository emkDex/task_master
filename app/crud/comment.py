"""
CRUD operations for Comment model.
"""

from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.comment import Comment
from app.schemas.comment import CommentCreate, CommentUpdate


class CRUDComment(CRUDBase[Comment, CommentCreate, CommentUpdate]):
    """CRUD operations for Comment model."""
    
    async def get_multi_by_task(
        self,
        db: AsyncSession,
        *,
        task_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Comment]:
        """
        Get comments by task ID.
        
        Args:
            db: Database session
            task_id: Task ID
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            List of comments for the task
        """
        result = await db.execute(
            select(Comment)
            .where(Comment.task_id == task_id)
            .order_by(Comment.created_at.desc())
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
        Count comments for a task.
        
        Args:
            db: Database session
            task_id: Task ID
        
        Returns:
            Number of comments
        """
        from sqlalchemy import func
        
        result = await db.execute(
            select(func.count(Comment.id))
            .where(Comment.task_id == task_id)
        )
        return result.scalar()
    
    async def get_multi_by_author(
        self,
        db: AsyncSession,
        *,
        author_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Comment]:
        """
        Get comments by author ID.
        
        Args:
            db: Database session
            author_id: Author user ID
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            List of comments by the author
        """
        result = await db.execute(
            select(Comment)
            .where(Comment.author_id == author_id)
            .order_by(Comment.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


comment = CRUDComment(Comment)
