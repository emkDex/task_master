"""
CRUD operations for Task model.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskFilter


class CRUDTask(CRUDBase[Task, TaskCreate, TaskUpdate]):
    """CRUD operations for Task model with filtering."""
    
    async def get_multi_by_owner(
        self,
        db: AsyncSession,
        *,
        owner_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """
        Get tasks by owner ID.
        
        Args:
            db: Database session
            owner_id: Owner user ID
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            List of tasks owned by the user
        """
        result = await db.execute(
            select(Task)
            .where(Task.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_multi_by_assignee(
        self,
        db: AsyncSession,
        *,
        assigned_to_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """
        Get tasks assigned to a user.
        
        Args:
            db: Database session
            assigned_to_id: Assigned user ID
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            List of tasks assigned to the user
        """
        result = await db.execute(
            select(Task)
            .where(Task.assigned_to_id == assigned_to_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_multi_by_team(
        self,
        db: AsyncSession,
        *,
        team_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """
        Get tasks by team ID.
        
        Args:
            db: Database session
            team_id: Team ID
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            List of tasks in the team
        """
        result = await db.execute(
            select(Task)
            .where(Task.team_id == team_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_with_filters(
        self,
        db: AsyncSession,
        *,
        filters: TaskFilter,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Task], int]:
        """
        Get tasks with filters and pagination.
        
        Args:
            db: Database session
            filters: TaskFilter with filter criteria
            user_id: Optional user ID to filter by ownership/assignment
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            Tuple of (list of tasks, total count)
        """
        query = select(Task)
        
        # Build filter conditions
        conditions = []
        
        if filters.status:
            conditions.append(Task.status == filters.status)
        
        if filters.priority:
            conditions.append(Task.priority == filters.priority)
        
        if filters.assigned_to_id:
            conditions.append(Task.assigned_to_id == filters.assigned_to_id)
        
        if filters.team_id:
            conditions.append(Task.team_id == filters.team_id)
        
        if filters.is_archived is not None:
            conditions.append(Task.is_archived == filters.is_archived)
        
        if filters.due_before:
            conditions.append(Task.due_date <= filters.due_before)
        
        if filters.due_after:
            conditions.append(Task.due_date >= filters.due_after)
        
        if filters.tags:
            # Check if any of the specified tags are in the task's tags array
            for tag in filters.tags:
                conditions.append(Task.tags.contains([tag]))
        
        if filters.search:
            search_pattern = f"%{filters.search}%"
            conditions.append(
                or_(
                    Task.title.ilike(search_pattern),
                    Task.description.ilike(search_pattern)
                )
            )
        
        # If user_id is provided, filter tasks owned by or assigned to the user
        if user_id:
            conditions.append(
                or_(
                    Task.owner_id == user_id,
                    Task.assigned_to_id == user_id
                )
            )
        
        # Apply conditions
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count(Task.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        return list(tasks), total
    
    async def get_user_tasks(
        self,
        db: AsyncSession,
        *,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Task]:
        """
        Get all tasks related to a user (owned or assigned).
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            List of tasks
        """
        result = await db.execute(
            select(Task)
            .where(
                or_(
                    Task.owner_id == user_id,
                    Task.assigned_to_id == user_id
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def count_by_status(
        self,
        db: AsyncSession,
        *,
        user_id: Optional[UUID] = None
    ) -> dict:
        """
        Count tasks by status.
        
        Args:
            db: Database session
            user_id: Optional user ID to filter
        
        Returns:
            Dictionary with status counts
        """
        query = select(Task.status, func.count(Task.id)).group_by(Task.status)
        
        if user_id:
            query = query.where(
                or_(
                    Task.owner_id == user_id,
                    Task.assigned_to_id == user_id
                )
            )
        
        result = await db.execute(query)
        counts = {row[0]: row[1] for row in result.all()}
        
        # Ensure all statuses are present
        all_statuses = ["pending", "in_progress", "completed", "cancelled"]
        for status in all_statuses:
            if status not in counts:
                counts[status] = 0
        
        return counts
    
    async def archive(self, db: AsyncSession, *, task_id: UUID) -> Optional[Task]:
        """
        Soft delete (archive) a task.
        
        Args:
            db: Database session
            task_id: Task ID
        
        Returns:
            Archived task or None
        """
        task = await self.get(db, id=task_id)
        if task:
            task.is_archived = True
            db.add(task)
            await db.flush()
            await db.refresh(task)
        return task


task = CRUDTask(Task)
