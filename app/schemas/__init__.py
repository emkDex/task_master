"""
Schemas module for TaskMaster Pro.
"""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserUpdatePassword,
    UserRead,
    UserMinimal,
    UserAdminRead,
    Token,
    TokenPayload,
    RefreshTokenRequest,
    LoginRequest,
)
from app.schemas.task import (
    TaskBase,
    TaskCreate,
    TaskUpdate,
    TaskRead,
    TaskListItem,
    TaskFilter,
    TaskAssignRequest,
    TaskStatusUpdate,
)
from app.schemas.team import (
    TeamBase,
    TeamCreate,
    TeamUpdate,
    TeamRead,
    TeamMinimal,
    TeamMemberBase,
    TeamMemberCreate,
    TeamMemberRead,
    TeamInvitationRequest,
    TeamMemberRoleUpdate,
)
from app.schemas.comment import (
    CommentBase,
    CommentCreate,
    CommentUpdate,
    CommentRead,
)
from app.schemas.attachment import (
    AttachmentBase,
    AttachmentCreate,
    AttachmentRead,
    FileUploadResponse,
)
from app.schemas.notification import (
    NotificationBase,
    NotificationCreate,
    NotificationRead,
    MarkAsReadRequest,
    NotificationFilter,
)
from app.schemas.activity_log import (
    ActivityLogBase,
    ActivityLogCreate,
    ActivityLogRead,
    ActivityLogFilter,
)
from app.schemas.pagination import (
    PaginatedResponse,
    PaginationParams,
    PageInfo,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserUpdatePassword",
    "UserRead",
    "UserMinimal",
    "UserAdminRead",
    "Token",
    "TokenPayload",
    "RefreshTokenRequest",
    "LoginRequest",
    # Task schemas
    "TaskBase",
    "TaskCreate",
    "TaskUpdate",
    "TaskRead",
    "TaskListItem",
    "TaskFilter",
    "TaskAssignRequest",
    "TaskStatusUpdate",
    # Team schemas
    "TeamBase",
    "TeamCreate",
    "TeamUpdate",
    "TeamRead",
    "TeamMinimal",
    "TeamMemberBase",
    "TeamMemberCreate",
    "TeamMemberRead",
    "TeamInvitationRequest",
    "TeamMemberRoleUpdate",
    # Comment schemas
    "CommentBase",
    "CommentCreate",
    "CommentUpdate",
    "CommentRead",
    # Attachment schemas
    "AttachmentBase",
    "AttachmentCreate",
    "AttachmentRead",
    "FileUploadResponse",
    # Notification schemas
    "NotificationBase",
    "NotificationCreate",
    "NotificationRead",
    "MarkAsReadRequest",
    "NotificationFilter",
    # Activity log schemas
    "ActivityLogBase",
    "ActivityLogCreate",
    "ActivityLogRead",
    "ActivityLogFilter",
    # Pagination schemas
    "PaginatedResponse",
    "PaginationParams",
    "PageInfo",
]
