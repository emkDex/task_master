"""
Base CRUD class for TaskMaster Pro.
Provides generic CRUD operations for all models.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic CRUD class with default methods to Create, Read, Update, Delete (CRUD).
    
    **Parameters**
    * `model`: A SQLAlchemy model class
    * `schema`: A Pydantic model (schema) class
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        
        **Parameters**
        * `model`: A SQLAlchemy model class
        """
        self.model = model
    
    async def get(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            db: Database session
            id: Record ID
        
        Returns:
            Model instance or None
        """
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of model instances
        """
        result = await db.execute(
            select(self.model)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_all(self, db: AsyncSession) -> List[ModelType]:
        """
        Get all records.
        
        Args:
            db: Database session
        
        Returns:
            List of all model instances
        """
        result = await db.execute(select(self.model))
        return result.scalars().all()
    
    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: CreateSchemaType
    ) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: Database session
            obj_in: Create schema with data
        
        Returns:
            Created model instance
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj
    
    async def create_multi(
        self,
        db: AsyncSession,
        *,
        objs_in: List[CreateSchemaType]
    ) -> List[ModelType]:
        """
        Create multiple records.
        
        Args:
            db: Database session
            objs_in: List of create schemas
        
        Returns:
            List of created model instances
        """
        db_objs = []
        for obj_in in objs_in:
            obj_in_data = jsonable_encoder(obj_in)
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            db_objs.append(db_obj)
        await db.flush()
        return db_objs
    
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update a record.
        
        Args:
            db: Database session
            db_obj: Existing model instance
            obj_in: Update schema or dict with data
        
        Returns:
            Updated model instance
        """
        obj_data = jsonable_encoder(db_obj)
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj
    
    async def remove(self, db: AsyncSession, *, id: UUID) -> Optional[ModelType]:
        """
        Delete a record by ID.
        
        Args:
            db: Database session
            id: Record ID
        
        Returns:
            Deleted model instance or None
        """
        obj = await self.get(db, id=id)
        if obj:
            await db.delete(obj)
            await db.flush()
        return obj
    
    async def exists(self, db: AsyncSession, **filters) -> bool:
        """
        Check if a record exists with given filters.
        
        Args:
            db: Database session
            **filters: Filter criteria
        
        Returns:
            True if record exists, False otherwise
        """
        query = select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None
    
    async def count(self, db: AsyncSession, **filters) -> int:
        """
        Count records with optional filters.
        
        Args:
            db: Database session
            **filters: Optional filter criteria
        
        Returns:
            Number of matching records
        """
        query = select(func.count(self.model.id))
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await db.execute(query)
        return result.scalar()
    
    async def get_by_filters(
        self,
        db: AsyncSession,
        **filters
    ) -> List[ModelType]:
        """
        Get records by filter criteria.
        
        Args:
            db: Database session
            **filters: Filter criteria
        
        Returns:
            List of matching model instances
        """
        query = select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_one_by_filters(
        self,
        db: AsyncSession,
        **filters
    ) -> Optional[ModelType]:
        """
        Get a single record by filter criteria.
        
        Args:
            db: Database session
            **filters: Filter criteria
        
        Returns:
            Matching model instance or None
        """
        query = select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
