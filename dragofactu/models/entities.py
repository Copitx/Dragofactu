from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import enum
import uuid


class UserRole(enum.Enum):
    ADMIN = "admin"
    MANAGEMENT = "management"
    WAREHOUSE = "warehouse"
    READ_ONLY = "read_only"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.READ_ONLY)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    created_documents = relationship("Document", foreign_keys="Document.created_by", back_populates="creator")
    document_histories = relationship("DocumentHistory", back_populates="user")
    diary_entries = relationship("DiaryEntry", back_populates="user")


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    permissions = Column(Text)  # JSON string of permissions
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    resource = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(Text)


class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    tax_id = Column(String(50))  # CIF/NIF
    address = Column(Text)
    city = Column(String(100))
    postal_code = Column(String(20))
    province = Column(String(100))
    country = Column(String(100))
    phone = Column(String(50))
    email = Column(String(100))
    website = Column(String(200))
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    documents = relationship("Document", back_populates="client")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    tax_id = Column(String(50))
    address = Column(Text)
    city = Column(String(100))
    postal_code = Column(String(20))
    province = Column(String(100))
    country = Column(String(100))
    phone = Column(String(50))
    email = Column(String(100))
    website = Column(String(200))
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    supplier_invoices = relationship("SupplierInvoice", back_populates="supplier")
    products = relationship("Product", back_populates="supplier")


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    purchase_price = Column(DECIMAL(10, 2))
    sale_price = Column(DECIMAL(10, 2))
    current_stock = Column(Integer, default=0)
    minimum_stock = Column(Integer, default=0)
    stock_unit = Column(String(20), default="units")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign Keys
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id"))
    
    # Relationships
    supplier = relationship("Supplier", back_populates="products")
    document_lines = relationship("DocumentLine", back_populates="product")
    stock_movements = relationship("StockMovement", back_populates="product")


class DocumentType(enum.Enum):
    QUOTE = "quote"
    DELIVERY_NOTE = "delivery_note"
    INVOICE = "invoice"


class DocumentStatus(enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)
    type = Column(Enum(DocumentType), nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.DRAFT)
    
    # Document dates
    issue_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True))
    
    # Client and references
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    parent_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    
    # Financial data
    subtotal = Column(DECIMAL(12, 2), default=0)
    tax_amount = Column(DECIMAL(12, 2), default=0)
    total = Column(DECIMAL(12, 2), default=0)
    
    # Custom tax configuration (JSON)
    tax_config = Column(Text)  # JSON with tax rates, retention, etc.
    
    # Notes and metadata
    notes = Column(Text)
    internal_notes = Column(Text)
    terms = Column(Text)
    
    # Audit fields
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client = relationship("Client", back_populates="documents")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_documents")
    lines = relationship("DocumentLine", back_populates="document", cascade="all, delete-orphan")
    histories = relationship("DocumentHistory", back_populates="document", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="document", cascade="all, delete-orphan")
    
    # Self-referential relationship for document lineage
    parent_document = relationship("Document", remote_side=[id], backref="child_documents")


class DocumentLine(Base):
    __tablename__ = "document_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    
    # Line type
    line_type = Column(String(20), default="product")  # "product" or "text"
    
    # Product reference (for product lines)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    
    # Description (for text lines or custom product names)
    description = Column(Text, nullable=False)
    
    # Quantity and pricing
    quantity = Column(DECIMAL(10, 2), default=1)
    unit_price = Column(DECIMAL(10, 2), default=0)
    discount_percent = Column(DECIMAL(5, 2), default=0)
    subtotal = Column(DECIMAL(10, 2), default=0)
    
    # Custom tax configuration per line (JSON)
    tax_config = Column(Text)
    
    # Order
    order_index = Column(Integer, default=0)
    
    # Relationships
    document = relationship("Document", back_populates="lines")
    product = relationship("Product", back_populates="document_lines")


class Worker(Base):
    __tablename__ = "workers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)
    
    # Personal data
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(200), nullable=False)
    
    # Contact information
    phone = Column(String(50))
    email = Column(String(100))
    address = Column(Text)
    
    # Employment information
    position = Column(String(100))
    department = Column(String(100))
    hire_date = Column(DateTime(timezone=True))
    salary = Column(DECIMAL(10, 2))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    courses = relationship("Course", back_populates="worker")


class Course(Base):
    __tablename__ = "courses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=False)
    
    # Course information
    name = Column(String(200), nullable=False)
    description = Column(Text)
    provider = Column(String(200))
    
    # Dates
    issue_date = Column(DateTime(timezone=True))
    expiration_date = Column(DateTime(timezone=True))
    
    # Status
    is_valid = Column(Boolean, default=True)
    
    # Documentation
    certificate_path = Column(String(500))  # Path to PDF file
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    worker = relationship("Worker", back_populates="courses")


class DiaryEntry(Base):
    __tablename__ = "diary_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Entry content
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    
    # Date and time
    entry_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # User who created the entry
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Tags and categorization
    tags = Column(Text)  # JSON array of tags
    
    # Related entities
    related_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    related_payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"))
    
    # Status
    is_pinned = Column(Boolean, default=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="diary_entries")


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Email details
    to_email = Column(String(200), nullable=False)
    subject = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    
    # Attachments
    attachments = Column(Text)  # JSON array of file paths
    
    # Status
    status = Column(String(20), default="pending")  # pending, sent, failed
    
    # Dates
    sent_at = Column(DateTime(timezone=True))
    
    # Related entity
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Error information
    error_message = Column(Text)