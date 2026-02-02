"""
DiaryEntry model with multi-tenant support.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base, GUID
import uuid


class DiaryEntry(Base):
    """
    Diary/Journal entry for daily notes.
    """
    __tablename__ = "diary_entries"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Company association (tenant)
    company_id = Column(GUID(), ForeignKey("companies.id"), nullable=False, index=True)

    # Content
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)

    # Date
    entry_date = Column(DateTime(timezone=True), nullable=False, index=True)

    # User who created
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)

    # Tags (JSON array)
    tags = Column(Text)

    # Related entities (optional)
    related_document_id = Column(GUID(), ForeignKey("documents.id"))

    # Status
    is_pinned = Column(Boolean, default=False)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="diary_entries")
    user = relationship("User")

    def __repr__(self):
        return f"<DiaryEntry {self.title[:30]}...>"
