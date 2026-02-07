"""
Audit log model for tracking entity changes.
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base, GUID
import uuid


class AuditLog(Base):
    """
    Audit log entry - tracks create/update/delete actions on entities.
    Scoped per company for multi-tenancy.
    """
    __tablename__ = "audit_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Company association (tenant)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False, index=True)

    # Who performed the action
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)

    # What happened
    action = Column(String(20), nullable=False, index=True)  # create, update, delete
    entity_type = Column(String(50), nullable=False, index=True)  # client, product, document, etc.
    entity_id = Column(String(32))  # UUID hex of the affected entity

    # Details (JSON string with changes)
    details = Column(Text)

    # When
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    company = relationship("Company")
    user = relationship("User")

    def __repr__(self):
        return f"<AuditLog {self.action} {self.entity_type} by user {self.user_id}>"
