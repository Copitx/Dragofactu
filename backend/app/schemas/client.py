"""
Client schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.schemas.base import BaseSchema, TimestampMixin, PaginatedResponse


class ClientBase(BaseModel):
    """Base client fields."""
    code: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=200)
    tax_id: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    province: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field("Espana", max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=2000)
    # Business fields
    payment_method: Optional[str] = Field(None, max_length=50)
    payment_days: Optional[int] = Field(30, ge=0, le=365)
    contact_person: Optional[str] = Field(None, max_length=100)
    bank_iban: Optional[str] = Field(None, max_length=34)
    default_discount: Optional[float] = Field(0.0, ge=0.0, le=100.0)
    notes_internal: Optional[str] = Field(None, max_length=2000)


class ClientCreate(ClientBase):
    """Client creation schema."""
    is_active: bool = True


class ClientUpdate(BaseModel):
    """Client update - all fields optional."""
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    tax_id: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    province: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=2000)
    is_active: Optional[bool] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    payment_days: Optional[int] = Field(None, ge=0, le=365)
    contact_person: Optional[str] = Field(None, max_length=100)
    bank_iban: Optional[str] = Field(None, max_length=34)
    default_discount: Optional[float] = Field(None, ge=0.0, le=100.0)
    notes_internal: Optional[str] = Field(None, max_length=2000)


class ClientResponse(BaseSchema, TimestampMixin):
    """Client response with all details."""
    id: UUID
    company_id: UUID
    code: str
    name: str
    tax_id: Optional[str] = None
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = None
    postal_code: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)
    is_active: bool
    payment_method: Optional[str] = None
    payment_days: Optional[int] = 30
    contact_person: Optional[str] = None
    bank_iban: Optional[str] = None   # Returned as-is (encrypted in DB, but masked here)
    default_discount: Optional[float] = 0.0
    notes_internal: Optional[str] = None


class ClientList(PaginatedResponse[ClientResponse]):
    """Paginated client list."""
    pass
