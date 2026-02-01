"""
Document and DocumentLine models with multi-tenant support.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Integer, Float, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base, GUID
import enum
import uuid


class DocumentType(str, enum.Enum):
    """Types of documents in the system."""
    QUOTE = "quote"
    DELIVERY_NOTE = "delivery_note"
    INVOICE = "invoice"


class DocumentStatus(str, enum.Enum):
    """
    Document status workflow.
    Flow: DRAFT -> NOT_SENT -> SENT -> ACCEPTED -> PAID
    """
    DRAFT = "draft"
    NOT_SENT = "not_sent"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    CANCELLED = "cancelled"


# Valid status transitions
STATUS_TRANSITIONS = {
    DocumentStatus.DRAFT: [DocumentStatus.NOT_SENT],
    DocumentStatus.NOT_SENT: [DocumentStatus.SENT, DocumentStatus.CANCELLED],
    DocumentStatus.SENT: [DocumentStatus.ACCEPTED, DocumentStatus.REJECTED, DocumentStatus.CANCELLED],
    DocumentStatus.ACCEPTED: [DocumentStatus.PAID, DocumentStatus.PARTIALLY_PAID, DocumentStatus.CANCELLED],
    DocumentStatus.PARTIALLY_PAID: [DocumentStatus.PAID, DocumentStatus.CANCELLED],
    DocumentStatus.REJECTED: [DocumentStatus.CANCELLED],
    DocumentStatus.PAID: [],
    DocumentStatus.CANCELLED: [],
}


class Document(Base):
    """
    Document model - Quotes, Delivery Notes, and Invoices.
    Code is unique per company and type.
    """
    __tablename__ = "documents"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Company association (tenant)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False, index=True)

    # Identification
    code = Column(String(20), nullable=False, index=True)
    type = Column(Enum(DocumentType), nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.DRAFT)

    # Dates
    issue_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True))

    # Client reference
    client_id = Column(GUID(), ForeignKey("clients.id"), nullable=False)

    # Document lineage (for conversions Quote -> Invoice)
    parent_document_id = Column(GUID(), ForeignKey("documents.id"))

    # Financial totals
    subtotal = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    total = Column(Float, default=0)

    # Tax configuration (JSON string)
    tax_config = Column(Text)

    # Notes
    notes = Column(Text)
    internal_notes = Column(Text)
    terms = Column(Text)

    # Audit
    created_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="documents")
    client = relationship("Client", back_populates="documents")
    creator = relationship("User")
    lines = relationship("DocumentLine", back_populates="document", cascade="all, delete-orphan", order_by="DocumentLine.order_index")
    parent_document = relationship("Document", remote_side=[id], backref="child_documents")

    # Unique constraint: code unique per company
    __table_args__ = (
        UniqueConstraint('company_id', 'code', name='uq_document_company_code'),
    )

    def can_transition_to(self, new_status: DocumentStatus) -> bool:
        """Check if transition to new status is allowed."""
        allowed = STATUS_TRANSITIONS.get(self.status, [])
        return new_status in allowed

    def calculate_totals(self):
        """Recalculate document totals from lines."""
        self.subtotal = sum(line.subtotal or 0 for line in self.lines)
        # Default 21% IVA if no tax_config
        tax_rate = 21.0
        self.tax_amount = self.subtotal * (tax_rate / 100)
        self.total = self.subtotal + self.tax_amount

    def __repr__(self):
        return f"<Document {self.code} ({self.type.value})>"


class DocumentLine(Base):
    """
    Document line item.
    Can be product-based or free text.
    """
    __tablename__ = "document_lines"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Document reference
    document_id = Column(GUID(), ForeignKey("documents.id"), nullable=False)

    # Line type
    line_type = Column(String(20), default="product")  # "product" or "text"

    # Product reference (for product lines)
    product_id = Column(GUID(), ForeignKey("products.id"))

    # Description (for text lines or custom product names)
    description = Column(Text, nullable=False)

    # Quantity and pricing
    quantity = Column(Float, default=1)
    unit_price = Column(Float, default=0)
    discount_percent = Column(Float, default=0)
    subtotal = Column(Float, default=0)

    # Tax per line (JSON string, optional)
    tax_config = Column(Text)

    # Order in document
    order_index = Column(Integer, default=0)

    # Relationships
    document = relationship("Document", back_populates="lines")
    product = relationship("Product", back_populates="document_lines")

    def calculate_subtotal(self):
        """Calculate line subtotal with discount."""
        base = self.quantity * self.unit_price
        discount = base * (self.discount_percent / 100)
        self.subtotal = base - discount

    def __repr__(self):
        return f"<DocumentLine {self.description[:30]}...>"
