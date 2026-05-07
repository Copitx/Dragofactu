"""
Project (Obra) schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from app.schemas.base import BaseSchema, PaginatedResponse


class ProjectExpenseBase(BaseModel):
    date: date
    description: str = Field(..., min_length=1, max_length=300)
    supplier: Optional[str] = Field(None, max_length=150)
    document_ref: Optional[str] = Field(None, max_length=50)
    amount: float = Field(0.0, ge=0)
    category: str = Field("other", pattern="^(material|labor|subcontract|other)$")
    worker_id: Optional[UUID] = None
    notes: Optional[str] = None


class ProjectExpenseCreate(ProjectExpenseBase):
    pass


class ProjectExpenseUpdate(BaseModel):
    date: Optional[date] = None
    description: Optional[str] = Field(None, min_length=1, max_length=300)
    supplier: Optional[str] = Field(None, max_length=150)
    document_ref: Optional[str] = Field(None, max_length=50)
    amount: Optional[float] = Field(None, ge=0)
    category: Optional[str] = Field(None, pattern="^(material|labor|subcontract|other)$")
    worker_id: Optional[UUID] = None
    notes: Optional[str] = None


class ProjectExpenseResponse(BaseSchema):
    id: UUID
    project_id: UUID
    company_id: UUID
    date: date
    description: str
    supplier: Optional[str] = None
    document_ref: Optional[str] = None
    amount: float
    category: str
    worker_id: Optional[UUID] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    worker_name: Optional[str] = None  # denormalized


class ProjectDocumentResponse(BaseSchema):
    id: UUID
    project_id: UUID
    document_id: UUID
    company_id: UUID
    linked_at: Optional[datetime] = None
    # Denormalized document info
    doc_code: Optional[str] = None
    doc_type: Optional[str] = None
    doc_status: Optional[str] = None
    doc_total: Optional[float] = None


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    client_id: Optional[UUID] = None
    address: Optional[str] = Field(None, max_length=300)
    status: str = Field("active", pattern="^(active|paused|completed|cancelled)$")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    estimated_value: float = Field(0.0, ge=0)
    notes: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    client_id: Optional[UUID] = None
    address: Optional[str] = Field(None, max_length=300)
    status: Optional[str] = Field(None, pattern="^(active|paused|completed|cancelled)$")
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    estimated_value: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class ProjectResponse(BaseSchema):
    id: UUID
    company_id: UUID
    code: str
    name: str
    client_id: Optional[UUID] = None
    client_name: Optional[str] = None  # denormalized
    address: Optional[str] = None
    status: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    estimated_value: float
    notes: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # KPIs
    total_expenses: Optional[float] = None
    total_invoiced: Optional[float] = None


class ProjectDetail(ProjectResponse):
    """Full project detail with expenses and linked documents."""
    expenses: List[ProjectExpenseResponse] = Field(default_factory=list)
    documents: List[ProjectDocumentResponse] = Field(default_factory=list)


class ProjectSummaryKPIs(BaseModel):
    """Financial summary for a project."""
    estimated_value: float
    total_expenses: float
    total_invoiced: float
    margin: float            # estimated_value - total_expenses
    margin_pct: Optional[float] = None  # margin / estimated_value * 100


class ProjectList(PaginatedResponse[ProjectResponse]):
    pass
