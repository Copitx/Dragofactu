"""
SupplierProduct model — catalog of products per supplier with purchase prices.
Each supplier can have multiple products with their specific references and prices.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base, GUID
import uuid


class SupplierProduct(Base):
    """
    Links a product to a supplier with supplier-specific data:
    reference code, purchase price, lead time, and min order qty.
    A product can be in many supplier catalogs; a supplier can have many products.
    """
    __tablename__ = "supplier_catalog"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Tenant isolation
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False, index=True)

    # The supplier this entry belongs to
    supplier_id = Column(GUID(), ForeignKey("suppliers.id"), nullable=False, index=True)

    # The product being referenced
    product_id = Column(GUID(), ForeignKey("products.id"), nullable=False, index=True)

    # Supplier-specific data
    supplier_ref = Column(String(50))        # Supplier's part number / reference
    purchase_price = Column(Float, default=0.0)   # Purchase price in this supplier
    lead_time_days = Column(Integer, default=0)   # Delivery lead time in days
    min_order_qty = Column(Float, default=1.0)    # Minimum order quantity
    notes = Column(Text)

    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company")
    supplier = relationship("Supplier", back_populates="catalog_entries")
    product = relationship("Product", back_populates="catalog_entries")

    # A product can only appear once per supplier in a company's catalog
    __table_args__ = (
        UniqueConstraint('company_id', 'supplier_id', 'product_id', name='uq_supplier_catalog_entry'),
    )

    def __repr__(self):
        return f"<SupplierProduct supplier={self.supplier_id} product={self.product_id}>"
