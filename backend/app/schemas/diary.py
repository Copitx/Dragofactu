"""
DiaryEntry schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.schemas.base import BaseSchema, TimestampMixin, PaginatedResponse


class DiaryEntryBase(BaseModel):
    """Base diary entry fields."""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    entry_date: datetime
    tags: Optional[str] = None  # JSON array as string
    related_document_id: Optional[UUID] = None
    is_pinned: bool = False


class DiaryEntryCreate(DiaryEntryBase):
    """Diary entry creation schema."""
    pass


class DiaryEntryUpdate(BaseModel):
    """Diary entry update - all fields optional."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    entry_date: Optional[datetime] = None
    tags: Optional[str] = None
    related_document_id: Optional[UUID] = None
    is_pinned: Optional[bool] = None


class DiaryEntryResponse(BaseSchema, TimestampMixin):
    """Diary entry response."""
    id: UUID
    company_id: UUID
    title: str
    content: str
    entry_date: datetime
    user_id: UUID
    tags: Optional[str] = None
    related_document_id: Optional[UUID] = None
    is_pinned: bool


class DiaryEntryList(PaginatedResponse[DiaryEntryResponse]):
    """Paginated diary entry list."""
    pass
