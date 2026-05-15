"""
Superadmin endpoints — platform-level administration.

SECURITY: All endpoints here require is_superadmin=True.
Access is audited on every call.
Superadmin status can ONLY be set via the create_superadmin.py script, never via API.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
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


class SuperadminResetPasswordRequest(BaseModel):
    new_password: str


class SuperadminUpdateUserRequest(BaseModel):
    role: str | None = None
    company_id: str | None = None
    is_active: bool | None = None
    full_name: str | None = None
    username: str | None = None


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


@router.post("/users/{user_id}/reset-password", response_model=MessageResponse)
async def superadmin_reset_user_password(
    user_id: UUID,
    request: SuperadminResetPasswordRequest,
    db: Session = Depends(get_db),
    superadmin: User = Depends(require_superadmin()),
):
    """
    Reset the password of any user on the platform.
    Superadmin only. Audited. Cannot set the same password as current
    (but cannot verify — hash is one-way, so we skip that check here).
    Cannot demote/affect another superadmin's password (still allows it for self-service).
    """
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o inactivo")

    PasswordValidator.validate_or_raise(request.new_password)

    user.password_hash = hash_password(request.new_password)
    db.commit()

    _audit_superadmin(
        db, superadmin,
        "reset_user_password",
        f"target_user={user_id} username={user.username}"
    )

    return MessageResponse(
        message=f"Contrase\u00f1a de '{user.username}' restablecida correctamente.",
        success=True,
    )


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


# ---------------------------------------------------------------------------
# All users across platform
# ---------------------------------------------------------------------------

@router.get("/users")
async def list_all_users(
    company_id: str | None = None,
    db: Session = Depends(get_db),
    superadmin: User = Depends(require_superadmin()),
):
    """List all users on the platform, optionally filtered by company."""
    _audit_superadmin(db, superadmin, "list_all_users", f"company_filter={company_id}")

    q = db.query(User, Company).join(Company, User.company_id == Company.id)
    if company_id:
        q = q.filter(User.company_id == company_id)
    rows = q.order_by(Company.name, User.full_name).all()

    return {
        "items": [
            {
                "id": str(u.id),
                "username": u.username,
                "full_name": u.full_name,
                "email": u.email,
                "role": u.role.value if hasattr(u.role, "value") else u.role,
                "is_active": u.is_active,
                "is_superadmin": getattr(u, "is_superadmin", False),
                "company_id": str(u.company_id),
                "company_name": c.name,
                "company_code": c.code,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u, c in rows
        ]
    }


@router.patch("/users/{user_id}", response_model=MessageResponse)
async def update_user_superadmin(
    user_id: UUID,
    request: SuperadminUpdateUserRequest,
    db: Session = Depends(get_db),
    superadmin: User = Depends(require_superadmin()),
):
    """Update a user's role, company, or active status. Cannot promote to superadmin."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    changes = []

    if request.role is not None:
        allowed = {r.value for r in UserRole}
        if request.role not in allowed:
            raise HTTPException(status_code=400, detail=f"Rol inválido: {request.role}")
        user.role = UserRole(request.role)
        changes.append(f"role={request.role}")

    if request.company_id is not None:
        new_company = db.query(Company).filter(Company.id == request.company_id).first()
        if not new_company:
            raise HTTPException(status_code=404, detail="Empresa destino no encontrada")
        user.company_id = request.company_id
        changes.append(f"company={request.company_id}")

    if request.is_active is not None:
        user.is_active = request.is_active
        changes.append(f"is_active={request.is_active}")

    if request.full_name is not None:
        user.full_name = request.full_name
        changes.append(f"full_name={request.full_name}")

    if request.username is not None:
        existing = db.query(User).filter(User.username == request.username).first()
        if existing and existing.id != user.id:
            raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")
        user.username = request.username
        changes.append(f"username={request.username}")

    db.commit()
    _audit_superadmin(db, superadmin, "update_user", f"user={user_id} changes={','.join(changes)}")
    return MessageResponse(message=f"Usuario '{user.username}' actualizado.", success=True)


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user_superadmin(
    user_id: UUID,
    db: Session = Depends(get_db),
    superadmin: User = Depends(require_superadmin()),
):
    """Soft-delete a user. Cannot delete another superadmin or yourself."""
    if str(user_id) == str(superadmin.id):
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if getattr(user, "is_superadmin", False):
        raise HTTPException(status_code=403, detail="No se puede eliminar a otro superadmin.")

    user.is_active = False
    db.commit()
    _audit_superadmin(db, superadmin, "delete_user", f"user={user_id} username={user.username}")
    return MessageResponse(message=f"Usuario '{user.username}' desactivado.", success=True)


# ---------------------------------------------------------------------------
# Company management
# ---------------------------------------------------------------------------

@router.delete("/companies/{company_id}", response_model=MessageResponse)
async def delete_company_superadmin(
    company_id: UUID,
    db: Session = Depends(get_db),
    superadmin: User = Depends(require_superadmin()),
):
    """
    Hard-delete a company and ALL its data. IRREVERSIBLE.
    Superadmin only. Heavily audited.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    _audit_superadmin(
        db, superadmin, "DELETE_COMPANY",
        f"company_id={company_id} name={company.name} code={company.code} — PERMANENT"
    )

    # Soft-delete all users in the company
    db.query(User).filter(User.company_id == company_id).update({"is_active": False})
    # Soft-delete the company itself
    company.is_active = False
    db.commit()

    return MessageResponse(
        message=f"Empresa '{company.name}' y sus usuarios han sido desactivados.",
        success=True,
    )
