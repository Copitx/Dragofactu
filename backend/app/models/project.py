"""
Project (Obra) models — core workflow for construction company.
Tracks active projects, expenses, and linked documents.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Date, Text, Float, ForeignKey, Enum, UniqueConstraint, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base, GUID
import enum
import uuid


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExpenseCategory(str, enum.Enum):
    MATERIAL = "material"
    LABOR = "labor"
    SUBCONTRACT = "subcontract"
    OTHER = "other"


class Project(Base):
    """
    Represents a construction project / obra.
    Has estimated value, actual expenses, and linked invoices to track margin.
    """
    __tablename__ = "projects"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False, index=True)

    # Auto-generated code: Obra-2026-001
    code = Column(String(20), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    client_id = Column(GUID(), ForeignKey("clients.id"), nullable=True, index=True)
    address = Column(String(300))               # Address of the work site
    status = Column(Enum(ProjectStatus), default=ProjectStatus.ACTIVE)

    start_date = Column(Date)
    end_date = Column(Date)
    estimated_value = Column(Float, default=0.0)  # Budget approved (€)

    notes = Column(Text)
    is_active = Column(Boolean, default=True)

    # Audit
    created_by = Column(GUID(), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company")
    client = relationship("Client")
    creator = relationship("User")
    expenses = relationship("ProjectExpense", back_populates="project", cascade="all, delete-orphan")
    project_documents = relationship("ProjectDocument", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('company_id', 'code', name='uq_project_company_code'),
    )

    def __repr__(self):
        return f"<Project {self.code}: {self.name}>"


class ProjectExpense(Base):
    """
    An expense line on a project — material, labor, subcontract, or other.
    """
    __tablename__ = "project_expenses"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID(), ForeignKey("projects.id"), nullable=False, index=True)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False, index=True)

    date = Column(Date, nullable=False)
    description = Column(String(300), nullable=False)
    supplier = Column(String(150))         # Supplier name (free text)
    document_ref = Column(String(50))      # Supplier's delivery note / invoice ref
    amount = Column(Float, default=0.0)
    category = Column(Enum(ExpenseCategory), default=ExpenseCategory.OTHER)
    worker_id = Column(GUID(), ForeignKey("workers.id"), nullable=True)  # Optional worker assignment
    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="expenses")
    worker = relationship("Worker")

    def __repr__(self):
        return f"<ProjectExpense {self.date} {self.description[:30]}>"


class ProjectDocument(Base):
    """
    Links a Document (quote, delivery note, invoice) to a Project.
    """
    __tablename__ = "project_documents"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID(), ForeignKey("projects.id"), nullable=False)
    document_id = Column(GUID(), ForeignKey("documents.id"), nullable=False)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False)
    linked_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="project_documents")
    document = relationship("Document")

    __table_args__ = (
        UniqueConstraint('project_id', 'document_id', name='uq_project_document'),
    )
