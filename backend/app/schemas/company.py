"""
Company schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.schemas.base import BaseSchema, TimestampMixin


class CompanyBase(BaseModel):
    """Base company fields."""
    name: str = Field(..., min_length=2, max_length=200)
    legal_name: Optional[str] = Field(None, max_length=200)
    tax_id: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    province: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field("Espana", max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    website: Optional[str] = Field(None, max_length=200)
    default_language: Optional[str] = Field("es", max_length=5)
    default_currency: Optional[str] = Field("EUR", max_length=3)
    tax_rate: Optional[float] = Field(21.0, ge=0, le=100)
    pdf_footer_text: Optional[str] = None
    logo_base64: Optional[str] = None


class CompanyUpdate(CompanyBase):
    """Company update - all fields optional."""
    name: Optional[str] = Field(None, min_length=2, max_length=200)


class CompanyEmailSettingsUpdate(BaseModel):
    """Per-company SMTP settings update."""
    smtp_host: Optional[str] = Field(None, max_length=200)
    smtp_port: Optional[int] = Field(587, ge=1, le=65535)
    smtp_user: Optional[str] = Field(None, max_length=200)
    smtp_password: Optional[str] = Field(None, max_length=500)
    smtp_use_tls: Optional[bool] = True
    smtp_from_email: Optional[str] = Field(None, max_length=200)
    smtp_from_name: Optional[str] = Field(None, max_length=200)
    email_subject_template: Optional[str] = Field(None, max_length=300)
    email_body_template: Optional[str] = Field(None, max_length=5000)


class CompanyEmailSettingsResponse(BaseModel):
    """Per-company SMTP settings (safe response, no password)."""
    configured: bool
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_use_tls: bool = True
    smtp_from_email: Optional[str] = None
    smtp_from_name: Optional[str] = None
    email_subject_template: Optional[str] = None
    email_body_template: Optional[str] = None


class CompanyResponse(BaseSchema, TimestampMixin):
    """Company response with all details."""
    id: UUID
    code: str
    name: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    logo_path: Optional[str] = None
    logo_base64: Optional[str] = None
    pdf_footer_text: Optional[str] = None
    default_language: str
    default_currency: str
    tax_rate: float
    plan_type: str
    max_users: int
    max_documents_month: int
    is_active: bool
