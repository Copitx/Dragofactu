"""
SQLAlchemy models package.
All models with multi-tenant support (company_id).
"""
from app.models.base import Base, GUID

# Core models
from app.models.company import Company
from app.models.user import User, UserRole

# Business entities
from app.models.client import Client
from app.models.supplier import Supplier
from app.models.product import Product

# Documents
from app.models.document import (
    Document,
    DocumentLine,
    DocumentType,
    DocumentStatus,
    STATUS_TRANSITIONS
)

# Workers
from app.models.worker import Worker, Course

# Auxiliary
from app.models.diary import DiaryEntry
from app.models.reminder import Reminder, ReminderPriority
from app.models.audit_log import AuditLog

__all__ = [
    # Base
    'Base',
    'GUID',
    # Core
    'Company',
    'User',
    'UserRole',
    # Entities
    'Client',
    'Supplier',
    'Product',
    # Documents
    'Document',
    'DocumentLine',
    'DocumentType',
    'DocumentStatus',
    'STATUS_TRANSITIONS',
    # Workers
    'Worker',
    'Course',
    # Auxiliary
    'DiaryEntry',
    'Reminder',
    'ReminderPriority',
    'AuditLog',
]
