"""
User API routes for TaskMaster Pro.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user, require_admin
from app.core.exceptions import NotFoundException, ValidationException
from app.crud.user import user as user_crud
from app.models.user import User
from app.schemas.user import (
    UserRead,
    UserUpdate,
    UserUpdatePassword,
    UserAdminRead
)
from app.services.activity_service import activity_service

router = APIRouter()


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user",
    description="Get the currently authenticated user's profile."
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
) -> UserRead:
    """Get current user profile."""
    return current_user


@router.put(
    "/me",
    response_model=UserRead,
    summary="Update current user",
    description="Update the currently authenticated user's profile."
)
async def update_current_user(
    request: Request,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserRead:
    """
    Update current user profile.
    
    - **email**: Optional new email (must be unique)
    - **username**: Optional new username (must be unique)
    - **full_name**: Optional full name
    - **avatar_url**: Optional avatar URL
    """
    # Check if email is being changed and if it's already taken
    if user_in.email and user_in.email != current_user.email:
        existing = await user_crud.get_by_email(db, email=user_in.email)
        if existing:
            raise ValidationException("Email already registered")
    
    # Check if username is being changed and if it's already taken
    if user_in.username and user_in.username != current_user.username:
        existing = await user_crud.get_by_username(db, username=user_in.username)
        if existing:
            raise ValidationException("Username already taken")
    
    user = await user_crud.update(db, db_obj=current_user, obj_in=user_in)
    
    # Log activity
    await activity_service.log(
        db,
        user_id=user.id,
        action="user_profile_updated",
        entity_type="user",
        entity_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    return user


@router.put(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change password",
    description="Change the currently authenticated user's password."
)
async def change_password(
    request: Request,
    password_data: UserUpdatePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Change current user password.
    
    - **current_password**: Current password for verification
    - **new_password**: New password (min 8 chars, 1 uppercase, 1 number)
    """
    from app.core.security import verify_password
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise ValidationException("Current password is incorrect")
    
    # Update password
    await user_crud.update_password(
        db,
        db_obj=current_user,
        new_password=password_data.new_password
    )
    
    # Log activity
    await activity_service.log(
        db,
        user_id=current_user.id,
        action="user_password_changed",
        entity_type="user",
        entity_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )


# Admin-only routes

@router.get(
    "/",
    response_model=List[UserAdminRead],
    summary="List all users (Admin)",
    description="Get a list of all users. Admin only."
)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> List[UserAdminRead]:
    """
    List all users (admin only).
    
    - **skip**: Number of users to skip (pagination)
    - **limit**: Maximum number of users to return
    """
    users = await user_crud.get_multi(db, skip=skip, limit=limit)
    return users


@router.get(
    "/{user_id}",
    response_model=UserAdminRead,
    summary="Get user by ID (Admin)",
    description="Get a specific user by ID. Admin only."
)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> UserAdminRead:
    """
    Get user by ID (admin only).
    
    - **user_id**: UUID of the user
    """
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise NotFoundException("User", str(user_id))
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate user (Admin)",
    description="Deactivate a user account. Admin only."
)
async def deactivate_user(
    request: Request,
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Deactivate a user (admin only).
    
    - **user_id**: UUID of the user to deactivate
    """
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise NotFoundException("User", str(user_id))
    
    # Prevent deactivating yourself
    if user.id == current_user.id:
        raise ValidationException("Cannot deactivate your own account")
    
    # Soft delete by deactivating
    user.is_active = False
    db.add(user)
    await db.flush()
    
    # Log activity
    await activity_service.log(
        db,
        user_id=current_user.id,
        action="user_deactivated",
        entity_type="user",
        entity_id=user_id,
        meta={"deactivated_user_email": user.email},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
