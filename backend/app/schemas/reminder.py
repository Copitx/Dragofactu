"""
Reminder schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.schemas.base import BaseSchema, TimestampMixin, PaginatedResponse


class ReminderBase(BaseModel):
    """Base reminder fields."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str = Field("normal", pattern="^(low|normal|high)$")


class ReminderCreate(ReminderBase):
    """Reminder creation schema."""
    pass


class ReminderUpdate(BaseModel):
    """Reminder update - all fields optional."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = Field(None, pattern="^(low|normal|high)$")
    is_completed: Optional[bool] = None


class ReminderResponse(BaseSchema, TimestampMixin):
    """Reminder response."""
    id: UUID
    company_id: UUID
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: str
    is_completed: bool
    is_overdue: bool
    created_by: Optional[UUID] = None


class ReminderList(PaginatedResponse[ReminderResponse]):
    """Paginated reminder list."""
    pass
