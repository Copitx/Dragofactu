"""
Worker and Course schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.schemas.base import BaseSchema, TimestampMixin, PaginatedResponse


class CourseBase(BaseModel):
    """Base course fields."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    provider: Optional[str] = Field(None, max_length=200)
    issue_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None


class CourseCreate(CourseBase):
    """Course creation schema."""
    pass


class CourseResponse(BaseSchema, TimestampMixin):
    """Course response."""
    id: UUID
    worker_id: UUID
    name: str
    description: Optional[str] = Field(None, max_length=2000)
    provider: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    is_valid: bool
    certificate_path: Optional[str] = None


class WorkerBase(BaseModel):
    """Base worker fields."""
    code: str = Field(..., min_length=1, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    position: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    hire_date: Optional[datetime] = None
    salary: Optional[float] = Field(None, ge=0)


class WorkerCreate(WorkerBase):
    """Worker creation schema."""
    pass


class WorkerUpdate(BaseModel):
    """Worker update - all fields optional."""
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = Field(None, max_length=500)
    position: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    hire_date: Optional[datetime] = None
    salary: Optional[float] = Field(None, ge=0)


class WorkerResponse(BaseSchema, TimestampMixin):
    """Worker response."""
    id: UUID
    company_id: UUID
    code: str
    first_name: str
    last_name: str
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = Field(None, max_length=500)
    position: Optional[str] = None
    department: Optional[str] = None
    hire_date: Optional[datetime] = None
    salary: Optional[float] = None
    is_active: bool
    courses: List[CourseResponse] = Field(default_factory=list)


class WorkerSummary(BaseSchema):
    """Worker summary for lists."""
    id: UUID
    code: str
    first_name: str
    last_name: str
    full_name: str
    position: Optional[str] = None
    department: Optional[str] = None
    is_active: bool


class WorkerList(PaginatedResponse[WorkerSummary]):
    """Paginated worker list."""
    pass
