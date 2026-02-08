"""
Authentication endpoints: login, register, refresh, logout.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uuid

from app.api.deps import get_db, get_current_user, security
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    verify_refresh_token
)
from app.core.security_utils import (
    PasswordValidator, check_login_rate_limit, check_register_rate_limit,
    token_blacklist, sanitize_username
)
from app.models import User, Company, UserRole
from app.schemas import (
    LoginRequest, LoginResponse, TokenResponse,
    RefreshRequest, RefreshResponse,
    RegisterCompanyRequest, UserResponse, MessageResponse
)

router = APIRouter(prefix="/auth", tags=["Autenticacion"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
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
async def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    """
    Obtener nuevo access token usando refresh token.
    """
    user_id = verify_refresh_token(request.refresh_token)

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


@router.post("/logout", response_model=MessageResponse)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user)
):
    """
    Cerrar sesion e invalidar el token actual.
    """
    if credentials:
        # Add token to blacklist so it can't be reused
        token_blacklist.add(credentials.credentials)

    return MessageResponse(
        message="Sesion cerrada correctamente",
        success=True
    )
