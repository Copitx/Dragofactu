"""
Authentication endpoints: login, register, refresh, logout, password management.
"""
import hashlib
import html
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import uuid

from app.api.deps import get_db, get_current_user, security, require_permission
from app.config import get_settings
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    verify_refresh_token
)
from app.core.security_utils import (
    PasswordValidator, check_login_rate_limit, check_register_rate_limit,
    token_blacklist, sanitize_username
)
from app.models import User, Company, UserRole, PasswordResetToken
from app.models.company import Company as CompanyModel
from app.core.email import send_plain_email, get_company_smtp_config
from app.schemas import (
    LoginRequest, LoginResponse, TokenResponse,
    RefreshRequest, RefreshResponse,
    RegisterCompanyRequest, UserResponse, MessageResponse, LogoutRequest
)
from app.schemas.auth import CreateUserRequest

router = APIRouter(prefix="/auth", tags=["Autenticacion"])
settings = get_settings()

REFRESH_COOKIE_NAME = "dragofactu_refresh_token"


def _set_refresh_cookie(response: Response, refresh_token: str):
    """Store refresh token in HttpOnly cookie for web clients."""
    max_age = 60 * 60 * 24 * 7
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=max_age,
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response):
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/api/v1/auth")


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Iniciar sesion con usuario y contraseña.
    Retorna access token y refresh token.
    """
    # Rate limiting - prevent brute force
    check_login_rate_limit(http_request)

    # Sanitize username
    username = sanitize_username(request.username)

    # Find user by username
    user = db.query(User).filter(
        User.username == username,
        User.is_active == True
    ).first()

    # SECURITY: Use constant-time comparison and same error for user not found
    # This prevents user enumeration attacks
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos"
        )

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    # Create tokens
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    _set_refresh_cookie(response, refresh_token)

    user_response = UserResponse.model_validate(user)
    # Add company name
    company = db.query(Company).filter(Company.id == user.company_id).first()
    if company:
        user_response.company_name = company.name

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user_response
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    request: Optional[RefreshRequest] = None,
    refresh_cookie: Optional[str] = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    db: Session = Depends(get_db)
):
    """
    Obtener nuevo access token usando refresh token.
    """
    refresh_token = request.refresh_token if request and request.refresh_token else refresh_cookie

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token ausente"
        )

    if token_blacklist.is_blacklisted(refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalidado"
        )

    user_id = verify_refresh_token(refresh_token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido o expirado"
        )

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido"
        )

    user = db.query(User).filter(
        User.id == user_uuid,
        User.is_active == True
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )

    # Create new access token
    access_token = create_access_token({"sub": str(user.id)})

    return RefreshResponse(
        access_token=access_token,
        token_type="bearer"
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_company(
    request: RegisterCompanyRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Registrar nueva empresa con usuario administrador.
    Este endpoint es publico para permitir auto-registro.
    """
    # Rate limiting - prevent spam registrations
    check_register_rate_limit(http_request)

    # Validate password complexity
    PasswordValidator.validate_or_raise(request.password)

    # Sanitize username
    username = sanitize_username(request.username)
    if len(username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario debe tener al menos 3 caracteres"
        )

    # Check if company code exists
    existing_company = db.query(Company).filter(
        Company.code == request.company_code
    ).first()

    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El codigo de empresa ya existe"
        )

    # Check if username exists (globally, for simplicity)
    existing_user = db.query(User).filter(
        User.username == username
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya existe"
        )

    # Create company
    company = Company(
        id=uuid.uuid4(),
        code=request.company_code,
        name=request.company_name,
        tax_id=request.company_tax_id,
        email=request.email
    )
    db.add(company)
    db.flush()  # Get company.id

    # Create admin user
    full_name = f"{request.first_name or ''} {request.last_name or ''}".strip()
    if not full_name:
        full_name = username

    user = User(
        id=uuid.uuid4(),
        company_id=company.id,
        username=username,
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=full_name,
        first_name=request.first_name,
        last_name=request.last_name,
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener informacion del usuario autenticado.
    """
    response = UserResponse.model_validate(current_user)
    # Add company name
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    if company:
        response.company_name = company.name
    return response


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_company_user(
    request: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admin"))
):
    """
    Crear un nuevo usuario en la misma empresa del admin.
    Solo el rol ADMIN puede crear usuarios. No crea empresa nueva.
    El nuevo usuario NO puede ser superadmin.
    """
    # Validate password
    PasswordValidator.validate_or_raise(request.password)

    username = sanitize_username(request.username)
    if len(username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario debe tener al menos 3 caracteres"
        )

    # Validate role — superadmin cannot be assigned via API
    allowed_roles = {r.value for r in UserRole}
    if request.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol inválido. Opciones: {', '.join(allowed_roles)}"
        )

    # Check username uniqueness within company
    existing = db.query(User).filter(
        User.company_id == current_user.company_id,
        User.username == username
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya existe en esta empresa"
        )

    # Check email uniqueness within company
    existing_email = db.query(User).filter(
        User.company_id == current_user.company_id,
        User.email == request.email
    ).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está en uso en esta empresa"
        )

    new_user = User(
        id=uuid.uuid4(),
        company_id=current_user.company_id,
        username=username,
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        first_name=request.first_name,
        last_name=request.last_name,
        role=UserRole(request.role),
        is_active=True,
        is_superadmin=False,  # Hardcoded — never via API
    )
    db.add(new_user)

    # Audit log
    try:
        from app.models.audit_log import AuditLog
        audit = AuditLog(
            company_id=current_user.company_id,
            user_id=current_user.id,
            action="create",
            entity_type="user",
            entity_id=str(new_user.id),
            details=f'{{"created_username": "{username}", "role": "{request.role}"}}',
        )
        db.add(audit)
    except Exception:
        pass

    db.commit()
    db.refresh(new_user)
    return UserResponse.model_validate(new_user)


@router.get("/users", response_model=list[UserResponse])
async def list_company_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admin"))
):
    """
    Listar todos los usuarios de la empresa del admin actual.
    """
    users = db.query(User).filter(
        User.company_id == current_user.company_id,
        User.is_active == True
    ).order_by(User.full_name).all()
    return [UserResponse.model_validate(u) for u in users]


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def deactivate_company_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admin"))
):
    """
    Desactivar (soft delete) un usuario de la empresa. El admin no puede desactivarse a sí mismo.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propio usuario"
        )

    user = db.query(User).filter(
        User.id == user_id,
        User.company_id == current_user.company_id,
        User.is_active == True
    ).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    user.is_active = False
    db.commit()
    return MessageResponse(message="Usuario desactivado correctamente", success=True)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    request: Optional[LogoutRequest] = None,
    refresh_cookie: Optional[str] = Cookie(default=None, alias=REFRESH_COOKIE_NAME),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user)
):
    """
    Cerrar sesion e invalidar el token actual.
    """
    if credentials:
        # Add token to blacklist so it can't be reused
        token_blacklist.add(credentials.credentials)

    # Best-effort refresh token revocation from payload or HttpOnly cookie
    refresh_token = request.refresh_token if request and request.refresh_token else refresh_cookie
    if refresh_token:
        token_blacklist.add(refresh_token, ttl_seconds=7 * 24 * 3600)

    _clear_refresh_cookie(response)

    return MessageResponse(
        message="Sesion cerrada correctamente",
        success=True
    )


# ---------------------------------------------------------------------------
# Password management
# ---------------------------------------------------------------------------

PASSWORD_RESET_TTL_MINUTES = 60


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _build_reset_email_html(reset_url: str, company_name: str) -> str:
    safe_company = html.escape(company_name)
    safe_url = html.escape(reset_url)
    return f"""
    <html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1D1D1F;padding:20px;">
      <h2 style="color:#007AFF;">{safe_company} \u2014 Recuperaci\u00f3n de contrase\u00f1a</h2>
      <p>Hemos recibido una solicitud para restablecer tu contrase\u00f1a.</p>
      <p>Haz clic en el enlace para establecer una nueva contrase\u00f1a.
         El enlace caduca en {PASSWORD_RESET_TTL_MINUTES} minutos.</p>
      <p style="margin:24px 0;">
        <a href="{safe_url}"
           style="background:#007AFF;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;">
          Restablecer contrase\u00f1a
        </a>
      </p>
      <p style="color:#6E6E73;font-size:12px;">
        Si no solicitaste este cambio, ignora este correo. Tu contrase\u00f1a no se modificar\u00e1.
      </p>
      <p style="color:#6E6E73;font-size:12px;">
        O copia este enlace en tu navegador:<br>{safe_url}
      </p>
    </body></html>
    """


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    req: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Request a password reset link.
    Always returns success to prevent email enumeration.
    """
    import logging as _log
    _logger = _log.getLogger(__name__)

    GENERIC = MessageResponse(
        message="Si el email existe en el sistema, recibir\u00e1s las instrucciones en breve.",
        success=True,
    )

    user = db.query(User).filter(
        User.email == req.email,
        User.is_active == True,
    ).first()

    if not user:
        return GENERIC

    # Invalidate previous unused tokens
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at == None,
    ).delete()

    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_TTL_MINUTES)

    db.add(PasswordResetToken(
        id=uuid.uuid4(),
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    ))
    db.commit()

    app_url = getattr(settings, "APP_URL", "http://localhost:5173")
    reset_url = f"{app_url}/reset-password?token={raw_token}"

    company = db.query(Company).filter(Company.id == user.company_id).first()
    smtp_config = get_company_smtp_config(company) if company else None
    company_name = company.name if company else "Dragofactu"

    try:
        send_plain_email(
            recipient_email=user.email,
            subject=f"{company_name} \u2014 Restablecer contrase\u00f1a",
            body_html=_build_reset_email_html(reset_url, company_name),
            smtp_config=smtp_config,
        )
    except Exception as exc:
        _logger.warning("Password reset email failed for %s: %s", user.email, exc)

    return GENERIC


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    req: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Set a new password using a valid reset token (single-use, 60 min TTL).
    """
    token_hash = _hash_token(req.token)
    now = datetime.now(timezone.utc)

    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at == None,
        PasswordResetToken.expires_at > now,
    ).first()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace de recuperaci\u00f3n no es v\u00e1lido o ha expirado."
        )

    PasswordValidator.validate_or_raise(req.new_password)

    user = db.query(User).filter(
        User.id == reset_token.user_id,
        User.is_active == True,
    ).first()
    if not user:
        raise HTTPException(status_code=400, detail="Usuario no encontrado o inactivo.")

    user.password_hash = hash_password(req.new_password)
    reset_token.used_at = now
    db.commit()

    return MessageResponse(message="Contrase\u00f1a restablecida correctamente.", success=True)


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change own password. Requires current password to be correct.
    """
    if not verify_password(req.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contrase\u00f1a actual es incorrecta."
        )

    PasswordValidator.validate_or_raise(req.new_password)

    if verify_password(req.new_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contrase\u00f1a debe ser diferente a la actual."
        )

    current_user.password_hash = hash_password(req.new_password)
    db.commit()

    return MessageResponse(message="Contrase\u00f1a cambiada correctamente.", success=True)
