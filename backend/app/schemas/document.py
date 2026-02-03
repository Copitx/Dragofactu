"""
Document schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.schemas.base import BaseSchema, TimestampMixin, PaginatedResponse


class DocumentLineBase(BaseModel):
    """Base document line fields."""
    line_type: str = Field("product", pattern="^(product|text)$")
    product_id: Optional[UUID] = None
    description: str = Field(..., min_length=1)
    quantity: float = Field(1, gt=0)
    unit_price: float = Field(0, ge=0)
    discount_percent: float = Field(0, ge=0, le=100)


class DocumentLineCreate(DocumentLineBase):
    """Document line creation schema."""
    pass


class DocumentLineResponse(BaseSchema):
    """Document line response."""
    id: UUID
    document_id: UUID
    line_type: str
    product_id: Optional[UUID] = None
    description: str
    quantity: float
    unit_price: float
    discount_percent: float
    subtotal: float
    order_index: int


class DocumentBase(BaseModel):
    """Base document fields."""
    type: str = Field(..., pattern="^(quote|delivery_note|invoice)$")
    client_id: UUID
    issue_date: datetime
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    terms: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Document creation with lines."""
    lines: List[DocumentLineCreate] = Field(default_factory=list)


class DocumentUpdate(BaseModel):
    """Document update - limited fields."""
    client_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    terms: Optional[str] = None
    lines: Optional[List[DocumentLineCreate]] = None


class StatusChange(BaseModel):
    """Change document status."""
    new_status: str = Field(
        ...,
        pattern="^(draft|not_sent|sent|accepted|rejected|paid|partially_paid|cancelled)$"
    )


class DocumentResponse(BaseSchema, TimestampMixin):
    """Document response with all details."""
    id: UUID
    company_id: UUID
    code: str
    type: str
    status: str
    issue_date: datetime
    due_date: Optional[datetime] = None
    client_id: UUID
    parent_document_id: Optional[UUID] = None
    subtotal: float
    tax_amount: float
    total: float
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    terms: Optional[str] = None
    created_by: UUID
    lines: List[DocumentLineResponse] = Field(default_factory=list)


class DocumentSummary(BaseSchema):
    """Document summary for lists."""
    id: UUID
    code: str
    type: str
    status: str
    issue_date: datetime
    due_date: Optional[datetime] = None
    client_id: UUID
    client_name: Optional[str] = None  # Added for dashboard display
    total: float
    created_at: Optional[datetime] = None


class DocumentList(PaginatedResponse[DocumentSummary]):
    """Paginated document list."""
    pass
