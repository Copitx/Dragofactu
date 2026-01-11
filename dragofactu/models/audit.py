from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, UUID, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import uuid


class DocumentHistory(Base):
    __tablename__ = "document_histories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Action information
    action = Column(String(50), nullable=False)  # created, updated, deleted, converted, status_changed
    description = Column(Text)
    
    # Change tracking
    field_name = Column(String(100))  # Which field was changed
    old_value = Column(Text)
    new_value = Column(Text)
    
    # Full snapshots (for major changes)
    before_snapshot = Column(Text)  # JSON representation of the document before change
    after_snapshot = Column(Text)   # JSON representation of the document after change
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="histories")
    user = relationship("User", back_populates="document_histories")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    # Movement details
    movement_type = Column(String(20), nullable=False)  # "in", "out", "adjustment"
    quantity = Column(Integer, nullable=False)
    reason = Column(String(100))
    
    # Reference to related document
    reference_type = Column(String(50))  # "document", "supplier_invoice", "manual_adjustment"
    reference_id = Column(UUID(as_uuid=True))
    
    # Stock before and after
    stock_before = Column(Integer, nullable=False)
    stock_after = Column(Integer, nullable=False)
    
    # User who performed the movement
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Notes
    notes = Column(Text)
    
    # Relationships
    product = relationship("Product", back_populates="stock_movements")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Payment details
    amount = Column(DECIMAL(12, 2), nullable=False)
    payment_method = Column(String(50))  # cash, transfer, card, etc.
    payment_date = Column(DateTime(timezone=True), nullable=False)
    
    # Status
    status = Column(String(20), default="pending")  # pending, paid, cancelled
    
    # Reference information
    reference = Column(String(100))  # Bank reference, check number, etc.
    
    # User who registered the payment
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Notes
    notes = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="payments")


class SupplierInvoice(Base):
    __tablename__ = "supplier_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    
    # Invoice details
    invoice_number = Column(String(100), nullable=False)
    invoice_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True))
    
    # Financial data
    subtotal = Column(DECIMAL(12, 2), default=0)
    tax_amount = Column(DECIMAL(12, 2), default=0)
    total = Column(DECIMAL(12, 2), default=0)
    
    # Status
    status = Column(String(20), default="pending")  # pending, received, paid, cancelled
    
    # Notes
    notes = Column(Text)
    
    # PDF file path
    pdf_path = Column(String(500))
    
    # User who registered it
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="supplier_invoices")