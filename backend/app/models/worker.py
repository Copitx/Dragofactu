"""
Worker and Course models with multi-tenant support.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base, GUID
import uuid


class Worker(Base):
    """
    Worker/Employee model.
    Code is unique per company.
    """
    __tablename__ = "workers"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Company association (tenant)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False, index=True)

    # Identification
    code = Column(String(20), nullable=False, index=True)

    # Personal data
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    # Contact
    phone = Column(String(50))
    email = Column(String(100))
    address = Column(Text)

    # Employment
    position = Column(String(100))
    department = Column(String(100))
    hire_date = Column(DateTime(timezone=True))
    salary = Column(Float)

    # Status
    is_active = Column(Boolean, default=True)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="workers")
    courses = relationship("Course", back_populates="worker", cascade="all, delete-orphan")

    # Unique constraint: code unique per company
    __table_args__ = (
        UniqueConstraint('company_id', 'code', name='uq_worker_company_code'),
    )

    @property
    def full_name(self) -> str:
        """Get full name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Worker {self.code}: {self.full_name}>"


class Course(Base):
    """
    Training course/certification for a worker.
    """
    __tablename__ = "courses"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Worker reference
    worker_id = Column(GUID(), ForeignKey("workers.id"), nullable=False)

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
    certificate_path = Column(String(500))

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    worker = relationship("Worker", back_populates="courses")

    @property
    def is_expired(self) -> bool:
        """Check if course is expired."""
        if self.expiration_date:
            from datetime import datetime
            return datetime.now(self.expiration_date.tzinfo) > self.expiration_date
        return False

    def __repr__(self):
        return f"<Course {self.name}>"
