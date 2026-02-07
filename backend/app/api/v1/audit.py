"""
Audit log endpoints.
View audit trail for the company.
"""
import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func

from app.api.deps import get_db, get_current_user
from app.models import User
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogResponse, AuditLogList

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["Audit Log"])


def log_action(
    db: Session,
    company_id,
    user_id,
    action: str,
    entity_type: str,
    entity_id=None,
    details: dict = None
):
    """
    Helper to create an audit log entry.
    Call this from other endpoints after successful operations.
    """
    entry = AuditLog(
        company_id=company_id,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        details=json.dumps(details) if details else None,
    )
    db.add(entry)
    # Don't commit here - let the caller manage the transaction


@router.get("", response_model=AuditLogList)
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(None, description="Filtrar por accion (create, update, delete)"),
    entity_type: Optional[str] = Query(None, description="Filtrar por tipo de entidad"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List audit log entries for the company."""
    query = db.query(AuditLog).filter(
        AuditLog.company_id == current_user.company_id
    )

    if action:
        query = query.filter(AuditLog.action == action)

    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    total = query.count()
    entries = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    return AuditLogList(
        items=[AuditLogResponse.model_validate(e) for e in entries],
        total=total,
        skip=skip,
        limit=limit
    )
