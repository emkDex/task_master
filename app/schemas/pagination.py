"""
Pagination schemas for TaskMaster Pro.
"""

from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response schema.
    
    Usage:
        PaginatedResponse[TaskRead]
        PaginatedResponse[UserRead]
    """
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
    
    model_config = {"from_attributes": True}


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    page: int = 1
    size: int = 20
    
    model_config = {"extra": "ignore"}


class PageInfo(BaseModel):
    """Page information for pagination."""
    page: int
    size: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool
    next_page: int = 0
    prev_page: int = 0
