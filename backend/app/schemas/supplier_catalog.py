"""
SupplierProduct (catalog) schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.schemas.base import BaseSchema


class SupplierProductBase(BaseModel):
    """Base catalog entry fields."""
    product_id: UUID
    supplier_ref: Optional[str] = Field(None, max_length=50)
    purchase_price: float = Field(0.0, ge=0)
    lead_time_days: int = Field(0, ge=0)
    min_order_qty: float = Field(1.0, gt=0)
    notes: Optional[str] = None
    is_active: bool = True


class SupplierProductCreate(SupplierProductBase):
    """Create a catalog entry for a supplier."""
    pass


class SupplierProductUpdate(BaseModel):
    """Update a catalog entry — all fields optional."""
    supplier_ref: Optional[str] = Field(None, max_length=50)
    purchase_price: Optional[float] = Field(None, ge=0)
    lead_time_days: Optional[int] = Field(None, ge=0)
    min_order_qty: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierProductResponse(BaseSchema):
    """Catalog entry response with product details."""
    id: UUID
    company_id: UUID
    supplier_id: UUID
    product_id: UUID
    supplier_ref: Optional[str] = None
    purchase_price: float
    lead_time_days: int
    min_order_qty: float
    notes: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Denormalized product fields for display
    product_code: Optional[str] = None
    product_name: Optional[str] = None
    product_sale_price: Optional[float] = None
    product_category: Optional[str] = None


class CatalogSearchResult(BaseSchema):
    """Result from global catalog search across all suppliers."""
    id: UUID
    supplier_id: UUID
    supplier_name: str
    supplier_code: str
    product_id: UUID
    product_code: str
    product_name: str
    supplier_ref: Optional[str] = None
    purchase_price: float
    sale_price: float
    margin_pct: Optional[float] = None  # (sale - purchase) / purchase * 100
    lead_time_days: int
