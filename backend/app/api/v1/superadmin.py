"""
Superadmin endpoints — platform-level administration.

SECURITY: All endpoints here require is_superadmin=True.
Access is audited on every call.
Superadmin status can ONLY be set via the create_superadmin.py script, never via API.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
import uuid

from app.api.deps import get_db, require_superadmin
from app.models import User, Company, Document, Client, AuditLog
from app.schemas.auth import UserResponse, CreateUserRequest
from app.schemas.base import PaginatedResponse, MessageResponse
from app.core.security import hash_password
from app.core.security_utils import PasswordValidator, sanitize_username
from app.models.user import UserRole

router = APIRouter(prefix="/superadmin", tags=["Superadmin"])


def _audit_superadmin(db: Session, actor: User, action: str, detail: str):
    """Log every superadmin access action."""
    try:
        audit = AuditLog(
            company_id=actor.company_id,
            user_id=actor.id,
            action="superadmin_access",
            entity_type="platform",
            entity_id=str(actor.id),
            details=f'{{"action": "{action}", "detail": "{detail}"}}',
        )
        db.add(audit)
        db.commit()
    except Exception:
        db.rollback()


# ---------------------------------------------------------------------------
# Company listing
# ---------------------------------------------------------------------------

@router.get("/companies")
async def list_all_companies(
    db: Session = Depends(get_db),
    superadmin: User = Depends(require_superadmin())
):
    """List all companies registered on the platform."""
    _audit_superadmin(db, superadmin, "list_companies", "")

    companies = db.query(Company).order_by(Company.created_at.desc()).all()
    result = []
    for c in companies:
        user_count = db.query(func.count(User.id)).filter(
            User.company_id == c.id, User.is_active == True
        ).scalar()
        doc_count = db.query(func.count(Document.id)).filter(
            Document.company_id == c.id
        ).scalar()
        client_count = db.query(func.count(Client.id)).filter(
            Client.company_id == c.id, Client.is_active == True
        ).scalar()
        result.append({
            "id": str(c.id),
            "code": c.code,
            "name": c.name,
            "trade_name": getattr(c, "trade_name", None),
            "tax_id": c.tax_id,
            "email": c.email,
            "is_active": c.is_active,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "user_count": user_count,
            "document_count": doc_count,
            "client_count": client_count,
        })
    return {"items": result, "total": len(result)}


@router.get("/companies/{company_id}/stats")
async def get_company_stats(
    company_id: UUID,
    db: Session = Depends(get_db),
    superadmin: User = Depends(require_superadmin())
):
    """Get detailed stats for a specific company."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    _audit_superadmin(db, superadmin, "view_company_stats", str(company_id))

    user_count = db.query(func.count(User.id)).filter(
        User.company_id == company_id, User.is_active == True
    ).scalar()
    doc_count = db.query(func.count(Document.id)).filter(
        Document.company_id == company_id
    ).scalar()
    client_count = db.query(func.count(Client.id)).filter(
        Client.company_id == company_id, Client.is_active == True
    ).scalar()

    return {
        "company": {
            "id": str(company.id),
            "code": company.code,
            "name": company.name,
            "trade_name": getattr(company, "trade_name", None),
            "tax_id": company.tax_id,
            "email": company.email,
            "is_active": company.is_active,
            "created_at": company.created_at.isoformat() if company.created_at else None,
        },
        "stats": {
            "users": user_count,
            "documents": doc_count,
            "clients": client_count,
        }
    }


# ---------------------------------------------------------------------------
# User management across companies
# ---------------------------------------------------------------------------

@router.get("/companies/{company_id}/users", response_model=list[UserResponse])
async def list_company_users_superadmin(
    company_id: UUID,
    db: Session = Depends(get_db),
    superadmin: User = Depends(require_superadmin())
):
    """List all users of any company."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    _audit_superadmin(db, superadmin, "list_company_users", str(company_id))

    users = db.query(User).filter(
        User.company_id == company_id
    ).order_by(User.full_name).all()
    return [UserResponse.model_validate(u) for u in users]


@router.post("/companies/{company_id}/users", response_model=UserResponse, status_code=201)
async def create_user_in_company(
    company_id: UUID,
    request: CreateUserRequest,
    db: Session = Depends(get_db),
    superadmin: User = Depends(require_superadmin())
):
    """Create a user in any company. Superadmin only. Cannot create another superadmin."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    PasswordValidator.validate_or_raise(request.password)
    username = sanitize_username(request.username)

    allowed_roles = {r.value for r in UserRole}
    if request.role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Rol inválido. Opciones: {', '.join(allowed_roles)}"
        )

    existing = db.query(User).filter(
        User.company_id == company_id, User.username == username
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Nombre de usuario ya existe en esta empresa")

    new_user = User(
        id=uuid.uuid4(),
        company_id=company_id,
        username=username,
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        first_name=request.first_name,
        last_name=request.last_name,
        role=UserRole(request.role),
        is_active=True,
        is_superadmin=False,  # Never via API
    )
    db.add(new_user)

    _audit_superadmin(db, superadmin, "create_user", f"company={company_id} user={username}")
    db.commit()
    db.refresh(new_user)
    return UserResponse.model_validate(new_user)


# ---------------------------------------------------------------------------
# Global audit log
# ---------------------------------------------------------------------------

@router.get("/audit")
async def get_global_audit(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    superadmin: User = Depends(require_superadmin())
):
    """Global audit log — all companies, no tenant filter."""
    _audit_superadmin(db, superadmin, "view_global_audit", "")

    total = db.query(func.count(AuditLog.id)).scalar()
    logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(min(limit, 500))
        .all()
    )
    return {
        "total": total,
        "items": [
            {
                "id": str(log.id),
                "company_id": str(log.company_id),
                "user_id": str(log.user_id) if log.user_id else None,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "details": log.details,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    }
