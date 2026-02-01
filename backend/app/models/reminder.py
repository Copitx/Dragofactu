"""
Reminder model with multi-tenant support.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base, GUID
import uuid
import enum


class ReminderPriority(str, enum.Enum):
    """Reminder priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class Reminder(Base):
    """
    Reminder/Task for users.
    Appears in dashboard.
    """
    __tablename__ = "reminders"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Company association (tenant)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False, index=True)

    # Content
    title = Column(String(200), nullable=False)
    description = Column(Text)

    # Due date
    due_date = Column(DateTime(timezone=True))

    # Priority
    priority = Column(String(20), default="normal")

    # Status
    is_completed = Column(Boolean, default=False)

    # User who created
    created_by = Column(GUID(), ForeignKey("users.id"))

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="reminders")
    creator = relationship("User")

    @property
    def is_overdue(self) -> bool:
        """Check if reminder is overdue."""
        if self.due_date and not self.is_completed:
            from datetime import datetime, timezone
            return datetime.now(timezone.utc) > self.due_date
        return False

    def __repr__(self):
        return f"<Reminder {self.title[:30]}...>"
