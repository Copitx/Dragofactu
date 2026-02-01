"""
FastAPI dependencies for authentication and database access.
"""
from typing import Generator, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import SessionLocal
from app.core.security import verify_access_token, create_access_token, verify_refresh_token
from app.models import User

# Security scheme for Swagger UI
security = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.
    Yields a session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from the JWT token.

    Raises:
        HTTPException 401: If token is missing, invalid, or user not found
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionaron credenciales",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials
    user_id = verify_access_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        user_uuid = UUID(user_id)
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
            detail="Usuario no encontrado o inactivo"
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify that the current user is active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    return current_user


def require_permission(permission: str) -> Callable:
    """
    Dependency factory that checks if user has a specific permission.

    Usage:
        @router.get("/", dependencies=[Depends(require_permission("clients.read"))])
        async def list_clients(...):

    Or:
        current_user: User = Depends(require_permission("clients.create"))
    """
    async def permission_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permiso para: {permission}"
            )
        return current_user

    return permission_checker


def get_company_id(current_user: User = Depends(get_current_user)) -> UUID:
    """
    Get the company ID from the current user.
    Useful for filtering queries by tenant.
    """
    return current_user.company_id
