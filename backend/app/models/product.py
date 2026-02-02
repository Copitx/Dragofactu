"""
Product model with multi-tenant support.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base, GUID
import uuid


class Product(Base):
    """
    Product model with stock management.
    Code is unique per company.
    """
    __tablename__ = "products"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Company association (tenant)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False, index=True)

    # Identification
    code = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))

    # Pricing
    purchase_price = Column(Float, default=0)
    sale_price = Column(Float, default=0)

    # Stock
    current_stock = Column(Integer, default=0)
    minimum_stock = Column(Integer, default=0)
    stock_unit = Column(String(20), default="unidades")

    # Supplier reference
    supplier_id = Column(GUID(), ForeignKey("suppliers.id"))

    # Status
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    document_lines = relationship("DocumentLine", back_populates="product")

    # Unique constraint: code unique per company
    __table_args__ = (
        UniqueConstraint('company_id', 'code', name='uq_product_company_code'),
    )

    @property
    def is_low_stock(self) -> bool:
        """Check if product is below minimum stock."""
        return self.current_stock < self.minimum_stock

    def __repr__(self):
        return f"<Product {self.code}: {self.name}>"
