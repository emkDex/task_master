"""
CRUD operations for User model.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD operations for User model."""
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            db: Database session
            email: User email
        
        Returns:
            User instance or None
        """
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            db: Database session
            username: User username
        
        Returns:
            User instance or None
        """
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email_or_username(
        self,
        db: AsyncSession,
        *,
        email: Optional[str] = None,
        username: Optional[str] = None
    ) -> Optional[User]:
        """
        Get a user by email or username.
        
        Args:
            db: Database session
            email: User email
            username: User username
        
        Returns:
            User instance or None
        """
        query = select(User)
        
        if email and username:
            query = query.where(
                or_(User.email == email, User.username == username)
            )
        elif email:
            query = query.where(User.email == email)
        elif username:
            query = query.where(User.username == username)
        else:
            return None
        
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """
        Create a new user with hashed password.
        
        Args:
            db: Database session
            obj_in: User create schema
        
        Returns:
            Created user instance
        """
        db_obj = User(
            email=obj_in.email,
            username=obj_in.username,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            avatar_url=obj_in.avatar_url,
            role="user",
            is_active=True,
            is_verified=False,
        )
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: User,
        obj_in: UserUpdate
    ) -> User:
        """
        Update a user.
        
        Args:
            db: Database session
            db_obj: Existing user instance
            obj_in: User update schema
        
        Returns:
            Updated user instance
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj
    
    async def update_password(
        self,
        db: AsyncSession,
        *,
        db_obj: User,
        new_password: str
    ) -> User:
        """
        Update user password.
        
        Args:
            db: Database session
            db_obj: User instance
            new_password: New plain password
        
        Returns:
            Updated user instance
        """
        db_obj.hashed_password = get_password_hash(new_password)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj
    
    async def authenticate(
        self,
        db: AsyncSession,
        *,
        username_or_email: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate a user by username/email and password.
        
        Args:
            db: Database session
            username_or_email: Username or email
            password: Plain password
        
        Returns:
            User instance if authentication succeeds, None otherwise
        """
        user = await self.get_by_email_or_username(
            db,
            email=username_or_email if "@" in username_or_email else None,
            username=username_or_email if "@" not in username_or_email else None
        )
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def is_active(self, user: User) -> bool:
        """Check if user is active."""
        return user.is_active
    
    async def is_admin(self, user: User) -> bool:
        """Check if user is admin."""
        return user.role == "admin"
    
    async def update_refresh_token_hash(
        self,
        db: AsyncSession,
        *,
        user: User,
        refresh_token_hash: Optional[str]
    ) -> User:
        """
        Update user's refresh token hash.
        
        Args:
            db: Database session
            user: User instance
            refresh_token_hash: New refresh token hash or None to clear
        
        Returns:
            Updated user instance
        """
        user.refresh_token_hash = refresh_token_hash
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user


user = CRUDUser(User)
