"""
FastAPI dependencies for TaskMaster Pro.
Provides database sessions, authentication, and authorization.
"""

from typing import AsyncGenerator, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.crud.user import user as user_crud
from app.models.user import User

# Security scheme for Swagger UI
security_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency that validates JWT token and returns current user.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Authorization credentials
        db: Database session
    
    Returns:
        User: Current authenticated user
    
    Raises:
        HTTPException: If authentication fails
    """
    # Check for token in WebSocket query params first
    token = request.query_params.get("token") if hasattr(request, "query_params") else None
    
    # Fall back to Authorization header
    if not token and credentials:
        token = credentials.credentials
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode and validate token
    payload = decode_access_token(token)
    user_id: Optional[str] = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = await user_crud.get(db, id=UUID(user_id))
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency that ensures user is active.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User: Current active user
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency that ensures user has admin role.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User: Current admin user
    
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def optional_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Dependency that optionally returns current user if authenticated.
    Does not raise exception if not authenticated.
    
    Args:
        request: FastAPI request object
        credentials: HTTP Authorization credentials
        db: Database session
    
    Returns:
        Optional[User]: Current user if authenticated, None otherwise
    """
    try:
        # Check for token in WebSocket query params first
        token = request.query_params.get("token") if hasattr(request, "query_params") else None
        
        # Fall back to Authorization header
        if not token and credentials:
            token = credentials.credentials
        
        if not token:
            return None
        
        # Decode and validate token
        payload = decode_access_token(token)
        user_id: Optional[str] = payload.get("sub")
        
        if user_id is None:
            return None
        
        # Get user from database
        user = await user_crud.get(db, id=UUID(user_id))
        
        if user is None or not user.is_active:
            return None
        
        return user
    
    except Exception:
        return None
