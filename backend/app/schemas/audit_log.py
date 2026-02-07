"""
Audit log schemas.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.schemas.base import BaseSchema, PaginatedResponse


class AuditLogResponse(BaseSchema):
    """Audit log entry response."""
    id: UUID
    company_id: UUID
    user_id: UUID
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    details: Optional[str] = None
    created_at: Optional[datetime] = None


class AuditLogList(PaginatedResponse[AuditLogResponse]):
    """Paginated audit log list."""
    pass
