"""
Main application module for TaskMaster Pro.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.api.v1.router import api_router
from app.services.websocket_service import websocket_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    print(f"Starting {settings.APP_NAME}...")
    
    # Start WebSocket heartbeat checker in background
    heartbeat_task = asyncio.create_task(websocket_manager.heartbeat_checker())
    
    yield
    
    # Shutdown
    print(f"Shutting down {settings.APP_NAME}...")
    
    # Cancel heartbeat task
    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass
    
    # Close database connections
    from app.db.session import close_db_connections
    await close_db_connections()


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="""
        TaskMaster Pro - A comprehensive task management REST API.
        
        ## Features
        
        - **User Management**: Registration, authentication, profile management
        - **Task Management**: Create, update, assign, and track tasks
        - **Team Collaboration**: Create teams, invite members, collaborate
        - **Comments**: Discuss tasks with team members
        - **File Attachments**: Upload and download task attachments
        - **Notifications**: Real-time notifications via WebSocket
        - **Activity Logging**: Track all actions for audit
        
        ## Authentication
        
        Most endpoints require authentication. Use the `/api/v1/auth/login` endpoint
        to obtain an access token, then include it in the Authorization header:
        
        ```
        Authorization: Bearer <your_access_token>
        ```
        """,
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    app.include_router(
        api_router,
        prefix=settings.API_V1_STR
    )
    
    # Mount static files for uploads
    app.mount(
        "/uploads",
        StaticFiles(directory=settings.UPLOAD_DIR),
        name="uploads"
    )
    
    return app


# Create application instance
app = create_application()


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API information."""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else None,
        "api": settings.API_V1_STR
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME
    }
