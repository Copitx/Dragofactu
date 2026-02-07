"""
Product schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from app.schemas.base import BaseSchema, TimestampMixin, PaginatedResponse


class ProductBase(BaseModel):
    """Base product fields."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=100)
    purchase_price: Optional[float] = Field(0, ge=0)
    sale_price: Optional[float] = Field(0, ge=0)
    current_stock: Optional[int] = Field(0, ge=0)
    minimum_stock: Optional[int] = Field(0, ge=0)
    stock_unit: Optional[str] = Field("unidades", max_length=20)
    supplier_id: Optional[UUID] = None


class ProductCreate(ProductBase):
    """Product creation schema."""
    pass


class ProductUpdate(BaseModel):
    """Product update - all fields optional."""
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = Field(None, max_length=100)
    purchase_price: Optional[float] = Field(None, ge=0)
    sale_price: Optional[float] = Field(None, ge=0)
    current_stock: Optional[int] = Field(None, ge=0)
    minimum_stock: Optional[int] = Field(None, ge=0)
    stock_unit: Optional[str] = Field(None, max_length=20)
    supplier_id: Optional[UUID] = None


class ProductResponse(BaseSchema, TimestampMixin):
    """Product response."""
    id: UUID
    company_id: UUID
    code: str
    name: str
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = None
    purchase_price: float
    sale_price: float
    current_stock: int
    minimum_stock: int
    stock_unit: str
    supplier_id: Optional[UUID] = None
    is_active: bool
    is_low_stock: bool


class ProductList(PaginatedResponse[ProductResponse]):
    """Paginated product list."""
    pass


class StockAdjustment(BaseModel):
    """Stock adjustment request."""
    product_id: UUID
    quantity: int = Field(..., description="Positive to add, negative to remove")
    reason: str = Field(..., min_length=1, max_length=200)
