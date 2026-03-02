"""
Core configuration module for TaskMaster Pro.
Uses Pydantic BaseSettings for environment variable management.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App Configuration
    APP_NAME: str = "TaskMaster Pro"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"
    
    # Database Configuration
    DATABASE_URL: str

    ENV: str = "development"
    
    # Security Configuration
    SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB: int = 10
    UPLOAD_DIR: str = "uploads/"
    
    # Rate Limiting
    RATELIMIT_ENABLED: bool = True
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from string or list."""
        if isinstance(v, str):
            # Handle JSON-like string format
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                # Remove brackets and split by comma
                v = v[1:-1]
                if not v:
                    return []
                return [origin.strip().strip('"').strip("'") for origin in v.split(",")]
            return [v]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
