"""
Custom exceptions and exception handlers for TaskMaster Pro.
"""

from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


class TaskMasterException(Exception):
    """Base exception for TaskMaster Pro."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(TaskMasterException):
    """Exception for resource not found."""
    
    def __init__(self, resource: str, resource_id: Optional[str] = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )


class ConflictException(TaskMasterException):
    """Exception for resource conflicts."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT
        )


class PermissionDeniedException(TaskMasterException):
    """Exception for permission denied."""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ValidationException(TaskMasterException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details or {}
        )


class AuthenticationException(TaskMasterException):
    """Exception for authentication errors."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class RateLimitException(TaskMasterException):
    """Exception for rate limiting."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


class FileUploadException(TaskMasterException):
    """Exception for file upload errors."""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )


# Exception handlers

async def taskmaster_exception_handler(
    request: Request,
    exc: TaskMasterException
) -> JSONResponse:
    """Handler for TaskMaster exceptions."""
    response = {
        "success": False,
        "error": {
            "message": exc.message,
            "code": exc.status_code,
            **exc.details
        }
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=response
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handler for request validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "message": "Validation error",
                "code": 422,
                "details": errors
            }
        }
    )


async def integrity_error_handler(
    request: Request,
    exc: IntegrityError
) -> JSONResponse:
    """Handler for database integrity errors."""
    # Extract meaningful message from integrity error
    error_msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)
    
    # Check for common constraint violations
    if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
        message = "A resource with this information already exists"
    elif "foreign key" in error_msg.lower():
        message = "Referenced resource does not exist"
    else:
        message = "Database constraint violation"
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "success": False,
            "error": {
                "message": message,
                "code": 409
            }
        }
    )


async def sqlalchemy_error_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """Handler for general SQLAlchemy errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "message": "Database error occurred",
                "code": 500
            }
        }
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handler for unhandled exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "message": "An unexpected error occurred",
                "code": 500
            }
        }
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(TaskMasterException, taskmaster_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)
