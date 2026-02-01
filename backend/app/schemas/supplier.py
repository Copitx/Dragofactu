"""
Supplier schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from app.schemas.base import BaseSchema, TimestampMixin, PaginatedResponse


class SupplierBase(BaseModel):
    """Base supplier fields."""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    tax_id: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    province: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field("Espana", max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class SupplierCreate(SupplierBase):
    """Supplier creation schema."""
    pass


class SupplierUpdate(BaseModel):
    """Supplier update - all fields optional."""
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    tax_id: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    province: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = None


class SupplierResponse(BaseSchema, TimestampMixin):
    """Supplier response."""
    id: UUID
    company_id: UUID
    code: str
    name: str
    tax_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool


class SupplierList(PaginatedResponse[SupplierResponse]):
    """Paginated supplier list."""
    pass
