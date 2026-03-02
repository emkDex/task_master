"""
API v1 router for TaskMaster Pro.
Aggregates all v1 routes.
"""

from fastapi import APIRouter

from app.api.v1 import auth, users, tasks, teams, comments, attachments, notifications, activity_logs, admin, websocket

api_router = APIRouter()

# Auth routes
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# User routes
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

# Task routes
api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["Tasks"]
)

# Team routes
api_router.include_router(
    teams.router,
    prefix="/teams",
    tags=["Teams"]
)

# Comment routes (nested under tasks)
api_router.include_router(
    comments.router,
    prefix="/tasks/{task_id}/comments",
    tags=["Comments"]
)

# Attachment routes (nested under tasks)
api_router.include_router(
    attachments.router,
    prefix="/tasks/{task_id}/attachments",
    tags=["Attachments"]
)

# Notification routes
api_router.include_router(
    notifications.router,
    prefix="/notifications",
    tags=["Notifications"]
)

# Activity log routes
api_router.include_router(
    activity_logs.router,
    prefix="/activity",
    tags=["Activity Logs"]
)

# Admin routes
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"]
)

# WebSocket routes
api_router.include_router(
    websocket.router,
    prefix="",
    tags=["WebSocket"]
)
