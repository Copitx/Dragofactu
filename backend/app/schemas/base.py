"""
Base schemas and common utilities.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Generic, TypeVar
from datetime import datetime
from uuid import UUID

# Generic type for paginated responses
T = TypeVar('T')


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(from_attributes=True)


class TimestampMixin(BaseModel):
    """Mixin for audit timestamps."""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: List[T]
    total: int
    skip: int
    limit: int

    @property
    def has_more(self) -> bool:
        return self.skip + len(self.items) < self.total


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str
    success: bool = True
