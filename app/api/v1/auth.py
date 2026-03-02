"""
Authentication API routes for TaskMaster Pro.
"""

from fastapi import APIRouter, Depends, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db, get_current_user
from app.core.exceptions import AuthenticationException, ValidationException
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserRead,
    Token,
    LoginRequest,
    RefreshTokenRequest
)
from app.services.auth_service import auth_service

router = APIRouter()

# Rate limiter - only enabled when RATELIMIT_ENABLED=True in settings
limiter = Limiter(key_func=get_remote_address, enabled=settings.RATELIMIT_ENABLED)

# Conditional rate-limit decorator helper
def _rate_limit(limit: str):
    """Apply rate limit only when rate limiting is enabled."""
    if settings.RATELIMIT_ENABLED:
        return limiter.limit(limit)
    # Return a no-op decorator when rate limiting is disabled
    def _noop(func):
        return func
    return _noop


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email, username, and password."
)
async def register(
    request: Request,
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserRead:
    """
    Register a new user.
    
    - **email**: Valid email address (must be unique)
    - **username**: Unique username (3-100 characters)
    - **password**: Password (min 8 chars, 1 uppercase, 1 number)
    - **full_name**: Optional full name
    """
    user = await auth_service.register_user(
        db,
        user_in=user_in,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="User login",
    description="Authenticate user and receive access and refresh tokens."
)
@_rate_limit("5/minute")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Login to get access token.
    
    - **username**: Username or email
    - **password**: User password
    
    Rate limited to 5 attempts per minute per IP.
    """
    _, token = await auth_service.authenticate_user(
        db,
        username_or_email=login_data.username,
        password=login_data.password,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return token


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Get a new access token using a valid refresh token."
)
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Refresh access token.
    
    - **refresh_token**: Valid refresh token received during login
    """
    token = await auth_service.refresh_access_token(
        db,
        refresh_token=refresh_data.refresh_token
    )
    return token


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="User logout",
    description="Invalidate refresh token and logout user."
)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Logout current user.
    Invalidates the refresh token.
    """
    await auth_service.logout(
        db,
        user=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
