"""
Pydantic schemas for User model.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.security import validate_password_strength


# Base schema with common attributes
class UserBase(BaseModel):
    """Base user schema with common attributes."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=500)


# Create schema
class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


# Update schema
class UserUpdate(BaseModel):
    """Schema for updating a user."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=500)


# Update password schema
class UserUpdatePassword(BaseModel):
    """Schema for updating user password."""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        is_valid, error_msg = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


# Read schema (response)
class UserRead(UserBase):
    """Schema for reading user data (response)."""
    id: UUID
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Minimal user schema (for relationships)
class UserMinimal(BaseModel):
    """Minimal user schema for nested responses."""
    id: UUID
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    
    model_config = {"from_attributes": True}


# Admin user read schema
class UserAdminRead(UserRead):
    """Extended user schema for admin views."""
    pass


# Token schemas
class Token(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenPayload(BaseModel):
    """Schema for token payload."""
    sub: Optional[str] = None  # user id
    exp: Optional[datetime] = None
    type: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class LoginRequest(BaseModel):
    """Schema for login request."""
    username: str  # Can be username or email
    password: str
