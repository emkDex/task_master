"""
Task service for TaskMaster Pro.
Handles business logic for task operations.
"""

from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
    PermissionDeniedException,
    ValidationException
)
from app.crud.task import task as task_crud
from app.crud.team import team as team_crud, team_member as team_member_crud
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskFilter, TaskAssignRequest
from app.services.notification_service import notification_service
from app.services.activity_service import activity_service


class TaskService:
    """Service for task operations."""
    
    async def create_task(
        self,
        db: AsyncSession,
        *,
        task_in: TaskCreate,
        owner: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Task:
        """
        Create a new task.
        
        Args:
            db: Database session
            task_in: Task creation data
            owner: Task owner
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            Created task
        
        Raises:
            ValidationException: If team_id is invalid
            PermissionDeniedException: If user is not a team member
        """
        # Validate team if provided
        if task_in.team_id:
            team = await team_crud.get(db, id=task_in.team_id)
            if not team:
                raise ValidationException("Invalid team_id")
            
            # Check if user is team member or owner
            is_member = await team_member_crud.is_member(
                db, team_id=task_in.team_id, user_id=owner.id
            )
            if team.owner_id != owner.id and not is_member:
                raise PermissionDeniedException("You are not a member of this team")
        
        # Create task data
        task_data = task_in.model_dump()
        task_data["owner_id"] = owner.id
        
        # Create task directly with owner_id (don't re-wrap in TaskCreate which drops owner_id)
        from app.models.task import Task
        from uuid import uuid4
        db_task = Task(
            id=uuid4(),
            owner_id=owner.id,
            title=task_data.get("title"),
            description=task_data.get("description"),
            status=task_data.get("status", "pending"),
            priority=task_data.get("priority", "medium"),
            due_date=task_data.get("due_date"),
            assigned_to_id=task_data.get("assigned_to_id"),
            team_id=task_data.get("team_id"),
            tags=task_data.get("tags", []),
            is_archived=False
        )
        db.add(db_task)
        await db.flush()
        await db.refresh(db_task)
        task = db_task
        
        # Notify assignee if different from owner
        if task.assigned_to_id and task.assigned_to_id != owner.id:
            await notification_service.notify_user(
                db,
                user_id=task.assigned_to_id,
                message=f"You have been assigned a new task: {task.title}",
                type="task_assigned",
                reference_id=task.id,
                reference_type="task"
            )
        
        # Log activity
        await activity_service.log(
            db,
            user_id=owner.id,
            action="task_created",
            entity_type="task",
            entity_id=task.id,
            meta={"title": task.title, "status": task.status},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return task
    
    async def update_task(
        self,
        db: AsyncSession,
        *,
        task_id: UUID,
        task_in: TaskUpdate,
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Task:
        """
        Update a task.
        
        Args:
            db: Database session
            task_id: Task ID
            task_in: Task update data
            current_user: Current user
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            Updated task
        
        Raises:
            NotFoundException: If task not found
            PermissionDeniedException: If user cannot modify task
        """
        task = await task_crud.get(db, id=task_id)
        
        if not task:
            raise NotFoundException("Task", str(task_id))
        
        # Check permissions
        can_modify = await self._can_modify_task(db, task=task, user=current_user)
        if not can_modify:
            raise PermissionDeniedException("You don't have permission to update this task")
        
        # Track old assignee for notification
        old_assignee_id = task.assigned_to_id
        
        # Update task
        task = await task_crud.update(db, db_obj=task, obj_in=task_in)
        
        # Notify new assignee if changed
        if (task.assigned_to_id and 
            task.assigned_to_id != old_assignee_id and 
            task.assigned_to_id != current_user.id):
            await notification_service.notify_user(
                db,
                user_id=task.assigned_to_id,
                message=f"You have been assigned to task: {task.title}",
                type="task_assigned",
                reference_id=task.id,
                reference_type="task"
            )
        
        # Log activity
        await activity_service.log(
            db,
            user_id=current_user.id,
            action="task_updated",
            entity_type="task",
            entity_id=task.id,
            meta={"title": task.title, "changes": task_in.model_dump(exclude_unset=True)},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return task
    
    async def delete_task(
        self,
        db: AsyncSession,
        *,
        task_id: UUID,
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Task:
        """
        Soft delete (archive) a task.
        
        Args:
            db: Database session
            task_id: Task ID
            current_user: Current user
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            Archived task
        
        Raises:
            NotFoundException: If task not found
            PermissionDeniedException: If user cannot delete task
        """
        task = await task_crud.get(db, id=task_id)
        
        if not task:
            raise NotFoundException("Task", str(task_id))
        
        # Check permissions - only owner or admin can delete
        if task.owner_id != current_user.id and current_user.role != "admin":
            raise PermissionDeniedException("You don't have permission to delete this task")
        
        # Archive task
        task = await task_crud.archive(db, task_id=task_id)
        
        # Log activity
        await activity_service.log(
            db,
            user_id=current_user.id,
            action="task_archived",
            entity_type="task",
            entity_id=task_id,
            meta={"title": task.title},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return task
    
    async def list_tasks(
        self,
        db: AsyncSession,
        *,
        filters: TaskFilter,
        current_user: User,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Task], int]:
        """
        List tasks with filters and pagination.
        
        Args:
            db: Database session
            filters: Task filter criteria
            current_user: Current user
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            Tuple of (list of tasks, total count)
        """
        # Admin can see all tasks, regular users only their own
        user_id = None if current_user.role == "admin" else current_user.id
        
        tasks, total = await task_crud.get_with_filters(
            db,
            filters=filters,
            user_id=user_id,
            skip=skip,
            limit=limit
        )
        
        return tasks, total
    
    async def get_task(
        self,
        db: AsyncSession,
        *,
        task_id: UUID,
        current_user: User
    ) -> Task:
        """
        Get a task by ID.
        
        Args:
            db: Database session
            task_id: Task ID
            current_user: Current user
        
        Returns:
            Task
        
        Raises:
            NotFoundException: If task not found
            PermissionDeniedException: If user cannot view task
        """
        task = await task_crud.get(db, id=task_id)
        
        if not task:
            raise NotFoundException("Task", str(task_id))
        
        # Check permissions
        can_view = await self._can_view_task(db, task=task, user=current_user)
        if not can_view:
            raise PermissionDeniedException("You don't have permission to view this task")
        
        return task
    
    async def assign_task(
        self,
        db: AsyncSession,
        *,
        task_id: UUID,
        assign_data: TaskAssignRequest,
        current_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Task:
        """
        Assign a task to a user.
        
        Args:
            db: Database session
            task_id: Task ID
            assign_data: Assignment data
            current_user: Current user
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            Updated task
        
        Raises:
            NotFoundException: If task not found
            PermissionDeniedException: If user cannot assign task
        """
        task = await task_crud.get(db, id=task_id)
        
        if not task:
            raise NotFoundException("Task", str(task_id))
        
        # Check permissions
        can_modify = await self._can_modify_task(db, task=task, user=current_user)
        if not can_modify:
            raise PermissionDeniedException("You don't have permission to assign this task")
        
        # Update assignment
        from app.schemas.task import TaskUpdate
        task = await task_crud.update(
            db,
            db_obj=task,
            obj_in=TaskUpdate(assigned_to_id=assign_data.assigned_to_id)
        )
        
        # Notify new assignee
        if assign_data.assigned_to_id and assign_data.assigned_to_id != current_user.id:
            await notification_service.notify_user(
                db,
                user_id=assign_data.assigned_to_id,
                message=f"You have been assigned to task: {task.title}",
                type="task_assigned",
                reference_id=task.id,
                reference_type="task"
            )
        
        # Log activity
        await activity_service.log(
            db,
            user_id=current_user.id,
            action="task_assigned",
            entity_type="task",
            entity_id=task.id,
            meta={
                "title": task.title,
                "assigned_to": str(assign_data.assigned_to_id)
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return task
    
    async def _can_modify_task(
        self,
        db: AsyncSession,
        *,
        task: Task,
        user: User
    ) -> bool:
        """
        Check if user can modify a task.
        
        Args:
            db: Database session
            task: Task to check
            user: User to check
        
        Returns:
            True if user can modify task
        """
        # Owner can always modify
        if task.owner_id == user.id:
            return True
        
        # Admin can modify any task
        if user.role == "admin":
            return True
        
        # Team managers can modify team tasks
        if task.team_id:
            is_manager = await team_member_crud.is_manager(
                db, team_id=task.team_id, user_id=user.id
            )
            if is_manager:
                return True
        
        return False
    
    async def _can_view_task(
        self,
        db: AsyncSession,
        *,
        task: Task,
        user: User
    ) -> bool:
        """
        Check if user can view a task.
        
        Args:
            db: Database session
            task: Task to check
            user: User to check
        
        Returns:
            True if user can view task
        """
        # Owner can always view
        if task.owner_id == user.id:
            return True
        
        # Assignee can view
        if task.assigned_to_id == user.id:
            return True
        
        # Admin can view any task
        if user.role == "admin":
            return True
        
        # Team members can view team tasks
        if task.team_id:
            is_member = await team_member_crud.is_member(
                db, team_id=task.team_id, user_id=user.id
            )
            if is_member:
                return True
        
        return False


# Global instance
task_service = TaskService()
