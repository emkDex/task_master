"""
Authentication service for TaskMaster Pro.
Handles user registration, login, token refresh, and logout.
"""

from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_token_hash,
    verify_token_hash,
    validate_password_strength
)
from app.core.exceptions import (
    AuthenticationException,
    ConflictException,
    ValidationException
)
from app.crud.user import user as user_crud
from app.models.user import User
from app.schemas.user import UserCreate, Token
from app.services.activity_service import activity_service


class AuthService:
    """Service for authentication operations."""
    
    async def register_user(
        self,
        db: AsyncSession,
        *,
        user_in: UserCreate,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> User:
        """
        Register a new user.
        
        Args:
            db: Database session
            user_in: User creation data
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            Created user
        
        Raises:
            ConflictException: If email or username already exists
        """
        # Check if email already exists
        existing_user = await user_crud.get_by_email(db, email=user_in.email)
        if existing_user:
            raise ConflictException("Email already registered")
        
        # Check if username already exists
        existing_user = await user_crud.get_by_username(db, username=user_in.username)
        if existing_user:
            raise ConflictException("Username already taken")
        
        # Validate password strength
        is_valid, error_msg = validate_password_strength(user_in.password)
        if not is_valid:
            raise ValidationException(error_msg)
        
        # Create user
        db_user = await user_crud.create(db, obj_in=user_in)
        
        # Log activity
        await activity_service.log(
            db,
            user_id=db_user.id,
            action="user_registered",
            entity_type="user",
            entity_id=db_user.id,
            meta={"email": user_in.email, "username": user_in.username},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return db_user
    
    async def authenticate_user(
        self,
        db: AsyncSession,
        *,
        username_or_email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, Token]:
        """
        Authenticate a user and generate tokens.
        
        Args:
            db: Database session
            username_or_email: Username or email
            password: Plain password
            ip_address: Client IP address
            user_agent: Client user agent
        
        Returns:
            Tuple of (user, token)
        
        Raises:
            AuthenticationException: If authentication fails
        """
        # Authenticate user
        db_user = await user_crud.authenticate(
            db,
            username_or_email=username_or_email,
            password=password
        )
        
        if not db_user:
            raise AuthenticationException("Invalid credentials")
        
        if not db_user.is_active:
            raise AuthenticationException("User account is deactivated")
        
        # Generate tokens
        token = await self._generate_token_pair(db, user=db_user)
        
        # Log activity
        await activity_service.log(
            db,
            user_id=db_user.id,
            action="user_login",
            entity_type="user",
            entity_id=db_user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return db_user, token
    
    async def refresh_access_token(
        self,
        db: AsyncSession,
        *,
        refresh_token: str
    ) -> Token:
        """
        Refresh access token using refresh token.
        
        Args:
            db: Database session
            refresh_token: Refresh token string
        
        Returns:
            New token pair
        
        Raises:
            AuthenticationException: If refresh token is invalid
        """
        try:
            # Decode refresh token
            payload = decode_refresh_token(refresh_token)
            user_id = payload.get("sub")
            
            if not user_id:
                raise AuthenticationException("Invalid refresh token")
            
            from uuid import UUID
            user = await user_crud.get(db, id=UUID(user_id))
            
            if not user or not user.is_active:
                raise AuthenticationException("Invalid refresh token")
            
            # Verify refresh token hash
            if not user.refresh_token_hash:
                raise AuthenticationException("Refresh token revoked")
            
            if not verify_token_hash(refresh_token, user.refresh_token_hash):
                raise AuthenticationException("Invalid refresh token")
            
            # Generate new token pair
            token = await self._generate_token_pair(db, user=user)
            
            return token
        
        except Exception as e:
            if isinstance(e, AuthenticationException):
                raise
            raise AuthenticationException("Invalid refresh token")
    
    async def logout(
        self,
        db: AsyncSession,
        *,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Logout user by invalidating refresh token.
        
        Args:
            db: Database session
            user: Current user
            ip_address: Client IP address
            user_agent: Client user agent
        """
        # Clear refresh token hash
        await user_crud.update_refresh_token_hash(db, user=user, refresh_token_hash=None)
        
        # Log activity
        await activity_service.log(
            db,
            user_id=user.id,
            action="user_logout",
            entity_type="user",
            entity_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    async def _generate_token_pair(
        self,
        db: AsyncSession,
        *,
        user: User
    ) -> Token:
        """
        Generate access and refresh token pair.
        
        Args:
            db: Database session
            user: User to generate tokens for
        
        Returns:
            Token pair
        """
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Store refresh token hash
        refresh_token_hash = get_token_hash(refresh_token)
        await user_crud.update_refresh_token_hash(
            db,
            user=user,
            refresh_token_hash=refresh_token_hash
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )


# Global instance
auth_service = AuthService()
