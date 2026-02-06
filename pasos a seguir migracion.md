# Plan de Migración: Dragofactu Multi-usuario Online

**Versión:** 1.0
**Fecha:** 2026-02-01
**Autor:** Claude Opus 4.5 (Agente AI)
**Estado:** Planificación Completa

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Arquitectura Actual vs Objetivo](#2-arquitectura-actual-vs-objetivo)
3. [Cambios en Base de Datos](#3-cambios-en-base-de-datos)
4. [Backend API con FastAPI](#4-backend-api-con-fastapi)
5. [Modificaciones al Cliente Desktop](#5-modificaciones-al-cliente-desktop)
6. [Despliegue y Hosting](#6-despliegue-y-hosting)
7. [Fases de Implementación](#7-fases-de-implementación)
8. [Capacidades de Claude](#8-capacidades-de-claude)
9. [Alternativas Consideradas](#9-alternativas-consideradas)
10. [Archivos Críticos del Proyecto](#10-archivos-críticos-del-proyecto)
11. [Glosario](#11-glosario)

---

## 1. Resumen Ejecutivo

### Objetivo
Convertir Dragofactu de una aplicación desktop local (SQLite) a un sistema multi-empresa/multi-usuario con datos centralizados en la nube, manteniendo el cliente desktop PySide6 existente.

### Beneficios
- **Multi-tenancy**: Múltiples empresas con datos aislados
- **Acceso remoto**: Datos accesibles desde cualquier lugar
- **Colaboración**: Múltiples usuarios por empresa trabajando simultáneamente
- **Seguridad centralizada**: Backups automáticos, auditoría centralizada
- **Escalabilidad**: Infraestructura cloud auto-escalable

### Riesgos Principales
- Latencia de red afecta UX
- Dependencia de conectividad
- Costos de hosting recurrentes
- Complejidad de migración de datos existentes

---

## 2. Arquitectura Actual vs Objetivo

### 2.1 Arquitectura Actual

```
┌─────────────────────────────────────────────┐
│             CLIENTE DESKTOP                  │
│  ┌─────────────────────────────────────┐    │
│  │         PySide6 UI                   │    │
│  │  (dragofactu_complete.py)           │    │
│  └──────────────┬──────────────────────┘    │
│                 │                            │
│  ┌──────────────▼──────────────────────┐    │
│  │         Servicios                    │    │
│  │  (ClientService, ProductService...)  │    │
│  └──────────────┬──────────────────────┘    │
│                 │                            │
│  ┌──────────────▼──────────────────────┐    │
│  │       SQLAlchemy ORM                 │    │
│  └──────────────┬──────────────────────┘    │
│                 │                            │
│  ┌──────────────▼──────────────────────┐    │
│  │      SQLite Local                    │    │
│  │   (dragofactu.db)                    │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
     Un usuario, una empresa, un dispositivo
```

### 2.2 Arquitectura Objetivo

```
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│  CLIENTE DESKTOP 1  │  │  CLIENTE DESKTOP 2  │  │  CLIENTE DESKTOP N  │
│    (Empresa A)      │  │    (Empresa A)      │  │    (Empresa B)      │
│  ┌───────────────┐  │  │  ┌───────────────┐  │  │  ┌───────────────┐  │
│  │  PySide6 UI   │  │  │  │  PySide6 UI   │  │  │  │  PySide6 UI   │  │
│  └───────┬───────┘  │  │  └───────┬───────┘  │  │  └───────┬───────┘  │
│  ┌───────▼───────┐  │  │  ┌───────▼───────┐  │  │  ┌───────▼───────┐  │
│  │   APIClient   │  │  │  │   APIClient   │  │  │  │   APIClient   │  │
│  └───────┬───────┘  │  │  └───────┬───────┘  │  │  └───────┬───────┘  │
└──────────┼──────────┘  └──────────┼──────────┘  └──────────┼──────────┘
           │                        │                        │
           │         HTTPS/REST     │                        │
           └────────────────────────┼────────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │         LOAD BALANCER         │
                    │     (Railway/Render/etc)      │
                    └───────────────┬───────────────┘
                                    │
┌───────────────────────────────────▼───────────────────────────────────┐
│                         BACKEND API (CLOUD)                           │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    FastAPI Application                           │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │ │
│  │  │   Auth   │  │  Clients │  │ Products │  │   Documents      │ │ │
│  │  │  Router  │  │  Router  │  │  Router  │  │     Router       │ │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬─────────┘ │ │
│  │       └─────────────┴─────────────┴─────────────────┘           │ │
│  │                              │                                   │ │
│  │  ┌───────────────────────────▼───────────────────────────────┐  │ │
│  │  │              Multi-Tenancy Middleware                      │  │ │
│  │  │         (Aisla datos por company_id)                       │  │ │
│  │  └───────────────────────────┬───────────────────────────────┘  │ │
│  │                              │                                   │ │
│  │  ┌───────────────────────────▼───────────────────────────────┐  │ │
│  │  │                   SQLAlchemy ORM                           │  │ │
│  │  └───────────────────────────┬───────────────────────────────┘  │ │
│  └──────────────────────────────┼───────────────────────────────────┘ │
│                                 │                                      │
│  ┌──────────────────────────────▼───────────────────────────────────┐ │
│  │                    PostgreSQL Database                            │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                  │ │
│  │  │ Company A  │  │ Company B  │  │ Company N  │  (Datos aislados)│ │
│  │  │   Data     │  │   Data     │  │   Data     │                  │ │
│  │  └────────────┘  └────────────┘  └────────────┘                  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
```

---

## 3. Cambios en Base de Datos

### 3.1 Nuevo Modelo: Company (Tenant)

```python
# dragofactu/models/entities.py - NUEVO MODELO

class Company(Base):
    """Representa una empresa/tenant en el sistema multi-empresa"""
    __tablename__ = 'companies'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identificación
    code = Column(String(20), unique=True, nullable=False)  # Ej: "ACME001"
    name = Column(String(200), nullable=False)
    legal_name = Column(String(200))  # Razón social
    tax_id = Column(String(20))  # CIF/NIF

    # Contacto
    address = Column(Text)
    city = Column(String(100))
    postal_code = Column(String(10))
    country = Column(String(100), default='España')
    phone = Column(String(20))
    email = Column(String(100))
    website = Column(String(200))

    # Configuración
    logo_path = Column(String(500))  # URL o path al logo
    default_language = Column(String(5), default='es')
    default_currency = Column(String(3), default='EUR')
    tax_rate = Column(Float, default=21.0)  # IVA por defecto

    # Suscripción/Plan
    plan_type = Column(String(20), default='basic')  # basic, pro, enterprise
    max_users = Column(Integer, default=5)
    max_documents_month = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    subscription_expires = Column(DateTime)

    # Auditoría
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    users = relationship("User", back_populates="company")
    clients = relationship("Client", back_populates="company")
    suppliers = relationship("Supplier", back_populates="company")
    products = relationship("Product", back_populates="company")
    documents = relationship("Document", back_populates="company")
    # ... etc para todas las entidades
```

### 3.2 Modificaciones a Entidades Existentes

Todas las entidades principales deben agregar `company_id`:

```python
# Ejemplo de modificación en User
class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # NUEVO: Relación con Company
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id'), nullable=False)
    company = relationship("Company", back_populates="users")

    # ... resto de campos existentes ...
    username = Column(String(50), nullable=False)
    # NOTA: unique constraint ahora es compuesto (company_id, username)

    __table_args__ = (
        UniqueConstraint('company_id', 'username', name='uq_user_company_username'),
    )
```

### 3.3 Lista de Entidades a Modificar

| Entidad | Archivo | Cambios |
|---------|---------|---------|
| `User` | `entities.py:~50` | + company_id, + unique(company_id, username) |
| `Client` | `entities.py:~100` | + company_id, + unique(company_id, code) |
| `Supplier` | `entities.py:~150` | + company_id, + unique(company_id, code) |
| `Product` | `entities.py:~200` | + company_id, + unique(company_id, code) |
| `Document` | `entities.py:~250` | + company_id, + unique(company_id, code) |
| `DocumentLine` | `entities.py:~300` | Hereda de Document (no necesita) |
| `Worker` | `entities.py:~350` | + company_id |
| `Course` | `entities.py:~400` | Hereda de Worker (no necesita) |
| `DiaryEntry` | `entities.py:~450` | + company_id |
| `Reminder` | `entities.py:~500` | + company_id |
| `StockMovement` | `audit.py` | + company_id |
| `Payment` | `audit.py` | + company_id |
| `DocumentHistory` | `audit.py` | + company_id |

### 3.4 Migraciones Alembic

```bash
# Estructura de migraciones
alembic/
├── versions/
│   ├── 001_create_companies_table.py
│   ├── 002_add_company_id_to_users.py
│   ├── 003_add_company_id_to_clients.py
│   ├── 004_add_company_id_to_products.py
│   ├── 005_add_company_id_to_documents.py
│   ├── 006_add_company_id_to_workers.py
│   ├── 007_add_company_id_to_diary.py
│   ├── 008_add_company_id_to_audit_tables.py
│   └── 009_add_composite_unique_constraints.py
└── env.py
```

**Migración de ejemplo:**

```python
# alembic/versions/001_create_companies_table.py
"""Create companies table

Revision ID: 001
Revises:
Create Date: 2026-02-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'companies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(20), unique=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('legal_name', sa.String(200)),
        sa.Column('tax_id', sa.String(20)),
        sa.Column('address', sa.Text),
        sa.Column('city', sa.String(100)),
        sa.Column('postal_code', sa.String(10)),
        sa.Column('country', sa.String(100), default='España'),
        sa.Column('phone', sa.String(20)),
        sa.Column('email', sa.String(100)),
        sa.Column('website', sa.String(200)),
        sa.Column('logo_path', sa.String(500)),
        sa.Column('default_language', sa.String(5), default='es'),
        sa.Column('default_currency', sa.String(3), default='EUR'),
        sa.Column('tax_rate', sa.Float, default=21.0),
        sa.Column('plan_type', sa.String(20), default='basic'),
        sa.Column('max_users', sa.Integer, default=5),
        sa.Column('max_documents_month', sa.Integer, default=100),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('subscription_expires', sa.DateTime),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
    )

def downgrade():
    op.drop_table('companies')
```

### 3.5 Estrategia de Multi-Tenancy

**Modelo elegido: Row-Level Security (RLS)**

```
Opción 1: Database-per-tenant     ❌ No escalable
Opción 2: Schema-per-tenant       ❌ Complejo de mantener
Opción 3: Row-Level (company_id)  ✅ ELEGIDO - Balance ideal
```

**Implementación:**

```python
# Backend: Filtro automático por company_id
class TenantMixin:
    """Mixin para queries filtradas por tenant"""

    @classmethod
    def query_for_company(cls, db: Session, company_id: UUID):
        return db.query(cls).filter(cls.company_id == company_id)

# Uso en endpoints
@router.get("/clients")
async def get_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Automáticamente filtrado por company_id del usuario
    return Client.query_for_company(db, current_user.company_id).all()
```

---

## 4. Backend API con FastAPI

### 4.1 Estructura de Carpetas

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Settings con Pydantic
│   ├── database.py                # Engine, SessionLocal
│   │
│   ├── models/                    # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── company.py
│   │   ├── user.py
│   │   ├── client.py
│   │   ├── product.py
│   │   ├── document.py
│   │   ├── worker.py
│   │   ├── diary.py
│   │   └── audit.py
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── company.py
│   │   ├── user.py
│   │   ├── client.py
│   │   ├── product.py
│   │   ├── document.py
│   │   ├── worker.py
│   │   ├── diary.py
│   │   └── auth.py
│   │
│   ├── api/                       # Routers
│   │   ├── __init__.py
│   │   ├── deps.py                # Dependencies (get_db, get_current_user)
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── companies.py
│   │   │   ├── users.py
│   │   │   ├── clients.py
│   │   │   ├── products.py
│   │   │   ├── documents.py
│   │   │   ├── inventory.py
│   │   │   ├── workers.py
│   │   │   ├── diary.py
│   │   │   └── reminders.py
│   │   └── router.py              # Agrupa todos los routers
│   │
│   ├── services/                  # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── client_service.py
│   │   ├── product_service.py
│   │   ├── document_service.py
│   │   ├── inventory_service.py
│   │   ├── pdf_service.py
│   │   └── email_service.py
│   │
│   ├── core/                      # Core utilities
│   │   ├── __init__.py
│   │   ├── security.py            # JWT, hashing
│   │   ├── permissions.py         # RBAC
│   │   └── exceptions.py          # Custom exceptions
│   │
│   └── middleware/
│       ├── __init__.py
│       └── tenant.py              # Multi-tenancy middleware
│
├── alembic/                       # Migraciones
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_clients.py
│   └── ...
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── alembic.ini
└── .env.example
```

### 4.2 Configuración Principal

```python
# backend/app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost/dragofactu"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # App
    APP_NAME: str = "Dragofactu API"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # CORS
    ALLOWED_ORIGINS: list[str] = ["*"]

    # Email (opcional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
```

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.config import get_settings
from app.database import engine
from app.models import Base

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    debug=settings.DEBUG
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.on_event("startup")
async def startup():
    # Crear tablas (en producción usar Alembic)
    Base.metadata.create_all(bind=engine)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
```

### 4.3 Sistema de Autenticación

```python
# backend/app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

```python
# backend/app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.core.security import decode_token
from app.models.user import User

security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )

    return user

def require_permission(permission: str):
    """Decorator para verificar permisos"""
    async def permission_checker(current_user: User = Depends(get_current_user)):
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permiso para: {permission}"
            )
        return current_user
    return permission_checker
```

### 4.4 Endpoints por Módulo

#### Auth Router

```python
# backend/app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.schemas.auth import (
    LoginRequest, LoginResponse,
    RefreshRequest, RefreshResponse,
    RegisterRequest, UserResponse
)
from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_token
)
from app.models.user import User
from app.models.company import Company

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login con username y password. Retorna access y refresh tokens."""
    user = db.query(User).filter(
        User.username == request.username,
        User.is_active == True
    ).first()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    """Obtener nuevo access token usando refresh token."""
    payload = decode_token(request.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido"
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    access_token = create_access_token(data={"sub": str(user.id)})

    return RefreshResponse(access_token=access_token, token_type="bearer")

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_company(request: RegisterRequest, db: Session = Depends(get_db)):
    """Registrar nueva empresa y usuario admin."""
    # Verificar que no exista
    existing = db.query(Company).filter(Company.code == request.company_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Código de empresa ya existe")

    # Crear empresa
    company = Company(
        code=request.company_code,
        name=request.company_name,
        tax_id=request.company_tax_id,
        email=request.email
    )
    db.add(company)
    db.flush()

    # Crear usuario admin
    user = User(
        company_id=company.id,
        username=request.username,
        email=request.email,
        password_hash=get_password_hash(request.password),
        role="admin",
        first_name=request.first_name,
        last_name=request.last_name
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse.from_orm(user)

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Obtener información del usuario actual."""
    return UserResponse.from_orm(current_user)

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout (client-side debe eliminar tokens)."""
    # En una implementación completa, invalidar token en blacklist
    return {"message": "Logout exitoso"}
```

#### Clients Router

```python
# backend/app/api/v1/clients.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.api.deps import get_db, get_current_user, require_permission
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse, ClientList
from app.models.client import Client
from app.models.user import User

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("/", response_model=ClientList)
async def list_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None, description="Buscar por nombre, código o CIF"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Listar clientes de la empresa."""
    query = db.query(Client).filter(
        Client.company_id == current_user.company_id,
        Client.is_active == True
    )

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Client.name.ilike(search_filter)) |
            (Client.code.ilike(search_filter)) |
            (Client.tax_id.ilike(search_filter))
        )

    total = query.count()
    clients = query.offset(skip).limit(limit).all()

    return ClientList(
        items=[ClientResponse.from_orm(c) for c in clients],
        total=total,
        skip=skip,
        limit=limit
    )

@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener un cliente por ID."""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.company_id == current_user.company_id,
        Client.is_active == True
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return ClientResponse.from_orm(client)

@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clients.create"))
):
    """Crear nuevo cliente."""
    # Verificar código único en la empresa
    existing = db.query(Client).filter(
        Client.company_id == current_user.company_id,
        Client.code == client_data.code
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Código de cliente ya existe")

    client = Client(
        company_id=current_user.company_id,
        **client_data.dict()
    )
    db.add(client)
    db.commit()
    db.refresh(client)

    return ClientResponse.from_orm(client)

@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    client_data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clients.update"))
):
    """Actualizar cliente existente."""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.company_id == current_user.company_id,
        Client.is_active == True
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    for field, value in client_data.dict(exclude_unset=True).items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)

    return ClientResponse.from_orm(client)

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clients.delete"))
):
    """Eliminar cliente (soft delete)."""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.company_id == current_user.company_id
    ).first()

    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    client.is_active = False
    db.commit()
```

#### Documents Router

```python
# backend/app/api/v1/documents.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import date
from io import BytesIO
from app.api.deps import get_db, get_current_user, require_permission
from app.schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentResponse,
    DocumentList, DocumentLineCreate, StatusChange
)
from app.models.document import Document, DocumentLine, DocumentStatus
from app.models.user import User
from app.services.pdf_service import generate_document_pdf

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.get("/", response_model=DocumentList)
async def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    doc_type: Optional[str] = Query(None, description="QUOTE, DELIVERY_NOTE, INVOICE"),
    status: Optional[str] = Query(None, description="Filtrar por estado"),
    client_id: Optional[UUID] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None, description="Buscar por código"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """Listar documentos con filtros."""
    query = db.query(Document).filter(
        Document.company_id == current_user.company_id,
        Document.is_active == True
    )

    if doc_type:
        query = query.filter(Document.type == doc_type)
    if status:
        query = query.filter(Document.status == status)
    if client_id:
        query = query.filter(Document.client_id == client_id)
    if date_from:
        query = query.filter(Document.issue_date >= date_from)
    if date_to:
        query = query.filter(Document.issue_date <= date_to)
    if search:
        query = query.filter(Document.code.ilike(f"%{search}%"))

    total = query.count()
    documents = query.order_by(Document.issue_date.desc()).offset(skip).limit(limit).all()

    return DocumentList(
        items=[DocumentResponse.from_orm(d) for d in documents],
        total=total,
        skip=skip,
        limit=limit
    )

@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    doc_data: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.create"))
):
    """Crear nuevo documento."""
    # Generar código automático
    prefix = {"QUOTE": "PRE", "DELIVERY_NOTE": "ALB", "INVOICE": "FAC"}[doc_data.type]
    count = db.query(Document).filter(
        Document.company_id == current_user.company_id,
        Document.type == doc_data.type
    ).count() + 1
    code = f"{prefix}-{count:05d}"

    document = Document(
        company_id=current_user.company_id,
        code=code,
        type=doc_data.type,
        status=DocumentStatus.DRAFT,
        client_id=doc_data.client_id,
        issue_date=doc_data.issue_date or date.today(),
        due_date=doc_data.due_date,
        notes=doc_data.notes,
        created_by=current_user.id
    )

    db.add(document)
    db.flush()

    # Añadir líneas
    for line_data in doc_data.lines:
        line = DocumentLine(
            document_id=document.id,
            **line_data.dict()
        )
        db.add(line)

    db.commit()
    db.refresh(document)

    return DocumentResponse.from_orm(document)

@router.put("/{document_id}/status", response_model=DocumentResponse)
async def change_status(
    document_id: UUID,
    status_data: StatusChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("documents.update"))
):
    """Cambiar estado del documento."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.company_id == current_user.company_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Validar transición de estado
    valid_transitions = {
        "draft": ["not_sent"],
        "not_sent": ["sent", "cancelled"],
        "sent": ["accepted", "rejected", "cancelled"],
        "accepted": ["paid", "partially_paid", "cancelled"],
        "partially_paid": ["paid", "cancelled"],
    }

    current_status = document.status.value
    new_status = status_data.new_status

    if new_status not in valid_transitions.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Transición de {current_status} a {new_status} no permitida"
        )

    document.status = DocumentStatus(new_status)

    # Si se marca como pagado, descontar stock
    if new_status == "paid" and document.type == "INVOICE":
        for line in document.lines:
            if line.product:
                line.product.current_stock -= line.quantity

    db.commit()
    db.refresh(document)

    return DocumentResponse.from_orm(document)

@router.get("/{document_id}/pdf")
async def get_document_pdf(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generar y descargar PDF del documento."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.company_id == current_user.company_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    pdf_bytes = generate_document_pdf(document, current_user.company)

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={document.code}.pdf"}
    )
```

### 4.5 Tabla Completa de Endpoints

| Método | Endpoint | Descripción | Permiso |
|--------|----------|-------------|---------|
| **Auth** ||||
| POST | `/api/v1/auth/login` | Login, retorna tokens | Público |
| POST | `/api/v1/auth/refresh` | Renovar access token | Público |
| POST | `/api/v1/auth/register` | Registrar empresa + admin | Público |
| GET | `/api/v1/auth/me` | Info usuario actual | Autenticado |
| POST | `/api/v1/auth/logout` | Cerrar sesión | Autenticado |
| **Companies** ||||
| GET | `/api/v1/companies/me` | Info empresa actual | Autenticado |
| PUT | `/api/v1/companies/me` | Actualizar empresa | company.update |
| **Users** ||||
| GET | `/api/v1/users` | Listar usuarios empresa | users.read |
| POST | `/api/v1/users` | Crear usuario | users.create |
| GET | `/api/v1/users/{id}` | Obtener usuario | users.read |
| PUT | `/api/v1/users/{id}` | Actualizar usuario | users.update |
| DELETE | `/api/v1/users/{id}` | Eliminar usuario | users.delete |
| **Clients** ||||
| GET | `/api/v1/clients` | Listar clientes | Autenticado |
| POST | `/api/v1/clients` | Crear cliente | clients.create |
| GET | `/api/v1/clients/{id}` | Obtener cliente | Autenticado |
| PUT | `/api/v1/clients/{id}` | Actualizar cliente | clients.update |
| DELETE | `/api/v1/clients/{id}` | Eliminar cliente | clients.delete |
| **Suppliers** ||||
| GET | `/api/v1/suppliers` | Listar proveedores | Autenticado |
| POST | `/api/v1/suppliers` | Crear proveedor | suppliers.create |
| GET | `/api/v1/suppliers/{id}` | Obtener proveedor | Autenticado |
| PUT | `/api/v1/suppliers/{id}` | Actualizar proveedor | suppliers.update |
| DELETE | `/api/v1/suppliers/{id}` | Eliminar proveedor | suppliers.delete |
| **Products** ||||
| GET | `/api/v1/products` | Listar productos | Autenticado |
| POST | `/api/v1/products` | Crear producto | products.create |
| GET | `/api/v1/products/{id}` | Obtener producto | Autenticado |
| PUT | `/api/v1/products/{id}` | Actualizar producto | products.update |
| DELETE | `/api/v1/products/{id}` | Eliminar producto | products.delete |
| **Documents** ||||
| GET | `/api/v1/documents` | Listar documentos | Autenticado |
| POST | `/api/v1/documents` | Crear documento | documents.create |
| GET | `/api/v1/documents/{id}` | Obtener documento | Autenticado |
| PUT | `/api/v1/documents/{id}` | Actualizar documento | documents.update |
| PUT | `/api/v1/documents/{id}/status` | Cambiar estado | documents.update |
| DELETE | `/api/v1/documents/{id}` | Eliminar documento | documents.delete |
| GET | `/api/v1/documents/{id}/pdf` | Descargar PDF | Autenticado |
| POST | `/api/v1/documents/{id}/convert` | Convertir a factura | documents.create |
| **Inventory** ||||
| GET | `/api/v1/inventory/levels` | Niveles de stock | Autenticado |
| GET | `/api/v1/inventory/low-stock` | Productos bajo mínimo | Autenticado |
| POST | `/api/v1/inventory/adjust` | Ajustar stock | inventory.adjust |
| GET | `/api/v1/inventory/movements` | Historial movimientos | Autenticado |
| **Workers** ||||
| GET | `/api/v1/workers` | Listar trabajadores | Autenticado |
| POST | `/api/v1/workers` | Crear trabajador | workers.create |
| GET | `/api/v1/workers/{id}` | Obtener trabajador | Autenticado |
| PUT | `/api/v1/workers/{id}` | Actualizar trabajador | workers.update |
| DELETE | `/api/v1/workers/{id}` | Eliminar trabajador | workers.delete |
| POST | `/api/v1/workers/{id}/courses` | Añadir curso | workers.update |
| **Diary** ||||
| GET | `/api/v1/diary` | Listar entradas | Autenticado |
| POST | `/api/v1/diary` | Crear entrada | diary.create |
| GET | `/api/v1/diary/{id}` | Obtener entrada | Autenticado |
| PUT | `/api/v1/diary/{id}` | Actualizar entrada | diary.update |
| DELETE | `/api/v1/diary/{id}` | Eliminar entrada | diary.delete |
| **Reminders** ||||
| GET | `/api/v1/reminders` | Listar recordatorios | Autenticado |
| POST | `/api/v1/reminders` | Crear recordatorio | Autenticado |
| PUT | `/api/v1/reminders/{id}` | Actualizar recordatorio | Autenticado |
| DELETE | `/api/v1/reminders/{id}` | Eliminar recordatorio | Autenticado |
| **Dashboard** ||||
| GET | `/api/v1/dashboard/metrics` | Métricas resumen | Autenticado |
| GET | `/api/v1/dashboard/pending-documents` | Docs pendientes | Autenticado |
| GET | `/api/v1/dashboard/pending-reminders` | Recordatorios pend. | Autenticado |

---

## 5. Modificaciones al Cliente Desktop

### 5.1 Nuevo Módulo: APIClient

```python
# dragofactu/services/api_client.py
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class TokenPair:
    access_token: str
    refresh_token: str
    expires_at: datetime

class APIError(Exception):
    def __init__(self, status_code: int, message: str, details: Dict = None):
        self.status_code = status_code
        self.message = message
        self.details = details or {}
        super().__init__(f"API Error {status_code}: {message}")

class APIClient:
    """Cliente HTTP para comunicación con el backend"""

    def __init__(self, base_url: str = "https://api.dragofactu.com"):
        self.base_url = base_url.rstrip('/')
        self.tokens: Optional[TokenPair] = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    # ============ AUTH ============

    def login(self, username: str, password: str) -> Dict:
        """Login y obtener tokens"""
        response = self._request('POST', '/auth/login', json={
            'username': username,
            'password': password
        }, auth_required=False)

        self.tokens = TokenPair(
            access_token=response['access_token'],
            refresh_token=response['refresh_token'],
            expires_at=datetime.utcnow()  # TODO: parsear de JWT
        )

        return response['user']

    def refresh_token(self) -> bool:
        """Renovar access token usando refresh token"""
        if not self.tokens:
            return False

        try:
            response = self._request('POST', '/auth/refresh', json={
                'refresh_token': self.tokens.refresh_token
            }, auth_required=False)

            self.tokens.access_token = response['access_token']
            return True
        except APIError:
            self.tokens = None
            return False

    def logout(self):
        """Cerrar sesión"""
        try:
            self._request('POST', '/auth/logout')
        finally:
            self.tokens = None

    def get_current_user(self) -> Dict:
        """Obtener info del usuario actual"""
        return self._request('GET', '/auth/me')

    def register_company(self, data: Dict) -> Dict:
        """Registrar nueva empresa"""
        return self._request('POST', '/auth/register', json=data, auth_required=False)

    # ============ CLIENTS ============

    def get_clients(self, search: str = None, skip: int = 0, limit: int = 50) -> Dict:
        """Listar clientes"""
        params = {'skip': skip, 'limit': limit}
        if search:
            params['search'] = search
        return self._request('GET', '/clients', params=params)

    def get_client(self, client_id: str) -> Dict:
        """Obtener cliente por ID"""
        return self._request('GET', f'/clients/{client_id}')

    def create_client(self, data: Dict) -> Dict:
        """Crear cliente"""
        return self._request('POST', '/clients', json=data)

    def update_client(self, client_id: str, data: Dict) -> Dict:
        """Actualizar cliente"""
        return self._request('PUT', f'/clients/{client_id}', json=data)

    def delete_client(self, client_id: str) -> None:
        """Eliminar cliente"""
        self._request('DELETE', f'/clients/{client_id}')

    # ============ PRODUCTS ============

    def get_products(self, search: str = None, skip: int = 0, limit: int = 50) -> Dict:
        """Listar productos"""
        params = {'skip': skip, 'limit': limit}
        if search:
            params['search'] = search
        return self._request('GET', '/products', params=params)

    def get_product(self, product_id: str) -> Dict:
        """Obtener producto por ID"""
        return self._request('GET', f'/products/{product_id}')

    def create_product(self, data: Dict) -> Dict:
        """Crear producto"""
        return self._request('POST', '/products', json=data)

    def update_product(self, product_id: str, data: Dict) -> Dict:
        """Actualizar producto"""
        return self._request('PUT', f'/products/{product_id}', json=data)

    def delete_product(self, product_id: str) -> None:
        """Eliminar producto"""
        self._request('DELETE', f'/products/{product_id}')

    # ============ DOCUMENTS ============

    def get_documents(
        self,
        doc_type: str = None,
        status: str = None,
        client_id: str = None,
        date_from: str = None,
        date_to: str = None,
        search: str = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict:
        """Listar documentos con filtros"""
        params = {'skip': skip, 'limit': limit}
        if doc_type:
            params['doc_type'] = doc_type
        if status:
            params['status'] = status
        if client_id:
            params['client_id'] = client_id
        if date_from:
            params['date_from'] = date_from
        if date_to:
            params['date_to'] = date_to
        if search:
            params['search'] = search
        return self._request('GET', '/documents', params=params)

    def get_document(self, document_id: str) -> Dict:
        """Obtener documento por ID"""
        return self._request('GET', f'/documents/{document_id}')

    def create_document(self, data: Dict) -> Dict:
        """Crear documento"""
        return self._request('POST', '/documents', json=data)

    def update_document(self, document_id: str, data: Dict) -> Dict:
        """Actualizar documento"""
        return self._request('PUT', f'/documents/{document_id}', json=data)

    def change_document_status(self, document_id: str, new_status: str) -> Dict:
        """Cambiar estado del documento"""
        return self._request('PUT', f'/documents/{document_id}/status', json={
            'new_status': new_status
        })

    def delete_document(self, document_id: str) -> None:
        """Eliminar documento"""
        self._request('DELETE', f'/documents/{document_id}')

    def get_document_pdf(self, document_id: str) -> bytes:
        """Descargar PDF del documento"""
        return self._request('GET', f'/documents/{document_id}/pdf', raw_response=True)

    # ============ INVENTORY ============

    def get_stock_levels(self) -> List[Dict]:
        """Obtener niveles de stock"""
        return self._request('GET', '/inventory/levels')

    def get_low_stock_products(self) -> List[Dict]:
        """Obtener productos con stock bajo"""
        return self._request('GET', '/inventory/low-stock')

    def adjust_stock(self, product_id: str, quantity: int, reason: str) -> Dict:
        """Ajustar stock de producto"""
        return self._request('POST', '/inventory/adjust', json={
            'product_id': product_id,
            'quantity': quantity,
            'reason': reason
        })

    # ============ DASHBOARD ============

    def get_dashboard_metrics(self) -> Dict:
        """Obtener métricas del dashboard"""
        return self._request('GET', '/dashboard/metrics')

    def get_pending_documents(self) -> List[Dict]:
        """Obtener documentos pendientes"""
        return self._request('GET', '/dashboard/pending-documents')

    def get_pending_reminders(self) -> List[Dict]:
        """Obtener recordatorios pendientes"""
        return self._request('GET', '/dashboard/pending-reminders')

    # ============ INTERNAL ============

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        json: Dict = None,
        auth_required: bool = True,
        raw_response: bool = False
    ) -> Any:
        """Realizar petición HTTP"""
        url = f"{self.base_url}/api/v1{endpoint}"
        headers = {}

        if auth_required and self.tokens:
            headers['Authorization'] = f"Bearer {self.tokens.access_token}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers=headers,
                timeout=30
            )

            # Token expirado, intentar refresh
            if response.status_code == 401 and auth_required and self.tokens:
                if self.refresh_token():
                    headers['Authorization'] = f"Bearer {self.tokens.access_token}"
                    response = self.session.request(
                        method=method,
                        url=url,
                        params=params,
                        json=json,
                        headers=headers,
                        timeout=30
                    )

            if raw_response:
                response.raise_for_status()
                return response.content

            if response.status_code == 204:
                return None

            if response.status_code >= 400:
                error_data = response.json() if response.text else {}
                raise APIError(
                    status_code=response.status_code,
                    message=error_data.get('detail', 'Error desconocido'),
                    details=error_data
                )

            return response.json()

        except requests.exceptions.Timeout:
            raise APIError(0, "Timeout de conexión")
        except requests.exceptions.ConnectionError:
            raise APIError(0, "Error de conexión con el servidor")


# Singleton global
_api_client: Optional[APIClient] = None

def get_api_client() -> APIClient:
    """Obtener instancia global del APIClient"""
    global _api_client
    if _api_client is None:
        from dragofactu.config.config import get_settings
        settings = get_settings()
        _api_client = APIClient(base_url=settings.API_BASE_URL)
    return _api_client

def set_api_client(client: APIClient):
    """Establecer instancia global (útil para testing)"""
    global _api_client
    _api_client = client
```

### 5.2 Modificación de Servicios

Los servicios actuales que usan SQLAlchemy directamente deben modificarse para usar el APIClient:

```python
# ANTES (actual): dragofactu/services/business/entity_services.py
class ClientService:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user

    @require_permission('clients.read')
    def get_all(self) -> List[Client]:
        return self.db.query(Client).filter(Client.is_active == True).all()

    @require_permission('clients.create')
    def create(self, data: dict) -> Client:
        client = Client(**data)
        self.db.add(client)
        self.db.commit()
        return client

# DESPUÉS (nuevo): dragofactu/services/client_service.py
from dragofactu.services.api_client import get_api_client, APIError

class ClientService:
    """Servicio de clientes usando API remota"""

    def __init__(self):
        self.api = get_api_client()

    def get_all(self, search: str = None) -> List[dict]:
        """Obtener todos los clientes"""
        response = self.api.get_clients(search=search)
        return response['items']

    def get_by_id(self, client_id: str) -> dict:
        """Obtener cliente por ID"""
        return self.api.get_client(client_id)

    def create(self, data: dict) -> dict:
        """Crear nuevo cliente"""
        return self.api.create_client(data)

    def update(self, client_id: str, data: dict) -> dict:
        """Actualizar cliente"""
        return self.api.update_client(client_id, data)

    def delete(self, client_id: str) -> None:
        """Eliminar cliente"""
        self.api.delete_client(client_id)
```

### 5.3 Modificaciones en UI

#### LoginDialog

```python
# MODIFICACIONES en dragofactu_complete.py / LoginDialog

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = get_api_client()
        self.user_data = None
        self.setup_ui()

    def setup_ui(self):
        # ... UI existente ...

        # NUEVO: Añadir opción de servidor
        self.server_combo = QComboBox()
        self.server_combo.addItems([
            "https://api.dragofactu.com",  # Producción
            "http://localhost:8000",        # Desarrollo
        ])
        self.server_combo.setEditable(True)

        # NUEVO: Link para registro
        self.register_link = QLabel('<a href="#">Crear nueva empresa</a>')
        self.register_link.linkActivated.connect(self.show_register_dialog)

        # Layout...

    def attempt_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        server = self.server_combo.currentText()

        if not username or not password:
            self.show_error("Ingresa usuario y contraseña")
            return

        # Configurar servidor
        self.api.base_url = server

        try:
            self.user_data = self.api.login(username, password)
            self.accept()
        except APIError as e:
            if e.status_code == 401:
                self.show_error("Credenciales incorrectas")
            elif e.status_code == 0:
                self.show_error("No se puede conectar al servidor")
            else:
                self.show_error(f"Error: {e.message}")

    def show_register_dialog(self):
        dialog = RegisterCompanyDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # Auto-login después de registro
            self.username_input.setText(dialog.username)
            self.password_input.setText(dialog.password)
            self.attempt_login()


class RegisterCompanyDialog(QDialog):
    """Diálogo para registrar nueva empresa"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = get_api_client()
        self.username = ""
        self.password = ""
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Registrar Nueva Empresa")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)

        # Datos empresa
        self.company_name_input = QLineEdit()
        self.company_code_input = QLineEdit()
        self.company_cif_input = QLineEdit()

        # Datos usuario admin
        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_confirm_input = QLineEdit()
        self.password_confirm_input.setEchoMode(QLineEdit.Password)

        layout.addRow("Nombre Empresa:", self.company_name_input)
        layout.addRow("Código Empresa:", self.company_code_input)
        layout.addRow("CIF/NIF:", self.company_cif_input)
        layout.addRow(QLabel(""))  # Separator
        layout.addRow("Nombre:", self.first_name_input)
        layout.addRow("Apellidos:", self.last_name_input)
        layout.addRow("Email:", self.email_input)
        layout.addRow("Usuario:", self.username_input)
        layout.addRow("Contraseña:", self.password_input)
        layout.addRow("Confirmar:", self.password_confirm_input)

        # Botones
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.register)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def register(self):
        # Validaciones
        if self.password_input.text() != self.password_confirm_input.text():
            QMessageBox.warning(self, "Error", "Las contraseñas no coinciden")
            return

        try:
            self.api.register_company({
                'company_code': self.company_code_input.text(),
                'company_name': self.company_name_input.text(),
                'company_tax_id': self.company_cif_input.text(),
                'first_name': self.first_name_input.text(),
                'last_name': self.last_name_input.text(),
                'email': self.email_input.text(),
                'username': self.username_input.text(),
                'password': self.password_input.text()
            })

            self.username = self.username_input.text()
            self.password = self.password_input.text()
            self.accept()

        except APIError as e:
            QMessageBox.warning(self, "Error", e.message)
```

#### Tabs de Gestión

```python
# Patrón de modificación para todas las tabs

class ClientManagementTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service = ClientService()  # Ya no recibe db ni user
        self.setup_ui()

    def load_clients(self):
        """Cargar clientes desde API"""
        try:
            search = self.search_input.text() if hasattr(self, 'search_input') else None
            clients = self.service.get_all(search=search)

            self.table.setRowCount(len(clients))
            for row, client in enumerate(clients):
                self.table.setItem(row, 0, QTableWidgetItem(client['code']))
                self.table.setItem(row, 1, QTableWidgetItem(client['name']))
                # ... etc

        except APIError as e:
            QMessageBox.warning(self, "Error", f"Error al cargar clientes: {e.message}")

    def create_client(self):
        """Crear cliente via API"""
        dialog = ClientDialog(self)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.service.create(dialog.get_data())
                self.load_clients()  # Recargar
            except APIError as e:
                QMessageBox.warning(self, "Error", e.message)

    def delete_client(self):
        """Eliminar cliente via API"""
        row = self.table.currentRow()
        if row < 0:
            return

        client_id = self.table.item(row, 0).data(Qt.UserRole)

        if QMessageBox.question(
            self, "Confirmar", "¿Eliminar este cliente?"
        ) == QMessageBox.Yes:
            try:
                self.service.delete(client_id)
                self.load_clients()
            except APIError as e:
                QMessageBox.warning(self, "Error", e.message)
```

### 5.4 Manejo de Errores y Conectividad

```python
# dragofactu/ui/widgets/connection_status.py

class ConnectionStatusWidget(QWidget):
    """Widget que muestra estado de conexión en status bar"""

    connection_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = get_api_client()
        self.is_connected = False
        self.setup_ui()
        self.start_monitoring()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.icon_label = QLabel()
        self.status_label = QLabel("Conectando...")

        layout.addWidget(self.icon_label)
        layout.addWidget(self.status_label)

    def start_monitoring(self):
        """Iniciar monitoreo de conexión"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_connection)
        self.timer.start(30000)  # Cada 30 segundos
        self.check_connection()  # Check inicial

    def check_connection(self):
        """Verificar conexión con servidor"""
        try:
            # Endpoint ligero para health check
            response = requests.get(
                f"{self.api.base_url}/health",
                timeout=5
            )
            connected = response.status_code == 200
        except:
            connected = False

        if connected != self.is_connected:
            self.is_connected = connected
            self.update_display()
            self.connection_changed.emit(connected)

    def update_display(self):
        if self.is_connected:
            self.icon_label.setPixmap(QPixmap("icons/connected.png"))
            self.status_label.setText("Conectado")
            self.status_label.setStyleSheet("color: #34C759;")
        else:
            self.icon_label.setPixmap(QPixmap("icons/disconnected.png"))
            self.status_label.setText("Sin conexión")
            self.status_label.setStyleSheet("color: #FF3B30;")
```

---

## 6. Despliegue y Hosting

### 6.1 Opciones de Hosting

| Plataforma | Pros | Contras | Costo Estimado |
|------------|------|---------|----------------|
| **Railway** (Recomendado) | Deploy automático desde Git, PostgreSQL incluido, SSL automático | Límites en plan free | $5-20/mes |
| **Render** | Similar a Railway, free tier generoso | Cold starts en free tier | $7-25/mes |
| **DigitalOcean App Platform** | Más control, escalable | Más configuración | $12-50/mes |
| **AWS (ECS/Lambda)** | Máxima escalabilidad | Complejo, curva de aprendizaje | Variable |
| **Heroku** | Simple deploy | Caro para producción | $25+/mes |

### 6.2 Configuración Railway (Recomendado)

```yaml
# railway.json
{
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Variables de entorno
ENV PYTHONUNBUFFERED=1

# Puerto (Railway asigna automáticamente)
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```txt
# requirements.txt (backend)
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
alembic>=1.12.0
python-multipart>=0.0.6
reportlab>=4.0.0
```

### 6.3 Docker Compose (Desarrollo Local)

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://dragofactu:secret@db:5432/dragofactu
      - SECRET_KEY=development-secret-key-change-in-production
      - DEBUG=true
    depends_on:
      - db
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=dragofactu
      - POSTGRES_PASSWORD=secret
      - POSTGRES_DB=dragofactu
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  adminer:
    image: adminer
    ports:
      - "8080:8080"

volumes:
  postgres_data:
```

### 6.4 Variables de Entorno Producción

```bash
# .env.production
DATABASE_URL=postgresql://user:password@host:5432/dragofactu
SECRET_KEY=<generar-clave-segura-64-chars>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DEBUG=false
ALLOWED_ORIGINS=https://app.dragofactu.com,https://dragofactu.com
```

---

## 7. Fases de Implementación

### Resumen Visual

```
Fase 1 ──▶ Fase 2 ──▶ Fase 3 ──▶ Fase 4 ──▶ Fase 5 ──▶ Fase 6 ──▶ Fase 7 ──▶ Fase 8
 Setup     Backend    Auth       CRUD       Docs       Client    Testing    Deploy
 (1 sem)   (2 sem)   (1 sem)    (2 sem)    (2 sem)    (2 sem)   (1 sem)    (1 sem)

TOTAL ESTIMADO: 12 semanas
```

### Fase 1: Setup Inicial (Semana 1)

**Objetivo:** Preparar infraestructura y estructura del proyecto

**Tareas:**
- [ ] Crear repositorio separado `dragofactu-api`
- [ ] Configurar estructura de carpetas backend
- [ ] Configurar PostgreSQL local con Docker
- [ ] Configurar Alembic para migraciones
- [ ] Crear modelo `Company` y migraciones base
- [ ] Configurar CI/CD básico (GitHub Actions)

**Entregables:**
- Repositorio backend funcional
- Base de datos PostgreSQL corriendo
- Estructura de carpetas completa

### Fase 2: Backend Core (Semanas 2-3)

**Objetivo:** Implementar FastAPI base con modelos y routers

**Tareas:**
- [ ] Configurar FastAPI application
- [ ] Implementar todos los modelos SQLAlchemy (con company_id)
- [ ] Crear schemas Pydantic para cada entidad
- [ ] Implementar dependency injection (get_db)
- [ ] Configurar CORS y middleware básico
- [ ] Implementar endpoint `/health`

**Entregables:**
- FastAPI app corriendo en localhost:8000
- Modelos completos con relaciones
- Swagger UI funcional en `/docs`

### Fase 3: Sistema de Autenticación (Semana 4)

**Objetivo:** Implementar auth completo con multi-tenancy

**Tareas:**
- [ ] Implementar JWT con refresh tokens
- [ ] Crear endpoints auth (login, refresh, register, logout)
- [ ] Implementar middleware de multi-tenancy
- [ ] Crear sistema de permisos RBAC
- [ ] Implementar `get_current_user` dependency
- [ ] Tests de autenticación

**Entregables:**
- Sistema auth funcional
- Registro de empresas operativo
- Tokens seguros con refresh

### Fase 4: CRUD Endpoints (Semanas 5-6)

**Objetivo:** Implementar todos los endpoints CRUD

**Tareas:**
- [ ] Endpoints Clients (CRUD completo)
- [ ] Endpoints Products (CRUD completo)
- [ ] Endpoints Suppliers (CRUD completo)
- [ ] Endpoints Workers + Courses
- [ ] Endpoints Diary + Reminders
- [ ] Endpoints Users (gestión por empresa)
- [ ] Filtros y paginación en todos

**Entregables:**
- Todos los endpoints CRUD funcionales
- Swagger documentado
- Filtrado y paginación

### Fase 5: Documentos e Inventario (Semanas 7-8)

**Objetivo:** Implementar lógica de negocio compleja

**Tareas:**
- [ ] Endpoints Documents (create, update, status)
- [ ] Lógica de transición de estados
- [ ] Conversión Quote → Invoice
- [ ] Generación de PDF en servidor
- [ ] Endpoints Inventory (adjust, movements)
- [ ] Deducción automática de stock
- [ ] Endpoints Dashboard (metrics, pending)

**Entregables:**
- Flujo completo de documentos
- PDFs generados en servidor
- Dashboard API funcional

### Fase 6: Cliente Desktop (Semanas 9-10)

**Objetivo:** Modificar cliente para usar API

**Tareas:**
- [ ] Implementar APIClient completo
- [ ] Modificar LoginDialog (servidor + registro)
- [ ] Adaptar servicios a usar API
- [ ] Modificar todas las tabs de gestión
- [ ] Implementar manejo de errores de red
- [ ] Añadir indicador de conexión
- [ ] Cache local opcional (SQLite para offline)

**Entregables:**
- Cliente funcionando con API remota
- Login y registro de empresas
- Todas las funcionalidades operativas

### Fase 7: Testing e Integración (Semana 11)

**Objetivo:** Asegurar calidad y estabilidad

**Tareas:**
- [ ] Tests unitarios backend (pytest)
- [ ] Tests de integración API
- [ ] Tests end-to-end cliente
- [ ] Load testing básico
- [ ] Documentación de API
- [ ] Documentación de despliegue

**Entregables:**
- Cobertura de tests > 80%
- Documentación completa
- Sistema estable

### Fase 8: Despliegue Producción (Semana 12)

**Objetivo:** Poner en producción

**Tareas:**
- [ ] Configurar Railway/Render
- [ ] Configurar PostgreSQL producción
- [ ] Configurar dominio personalizado
- [ ] Configurar SSL
- [ ] Migrar datos de prueba
- [ ] Monitoreo y alertas
- [ ] Backup automático BD

**Entregables:**
- API en producción
- Cliente conectado a producción
- Sistema de backups operativo

---

## 8. Capacidades de Claude

### 8.1 Lo que Claude PUEDE hacer

| Tarea | Complejidad | Notas |
|-------|-------------|-------|
| Crear estructura de carpetas backend | Baja | Automatizable 100% |
| Escribir modelos SQLAlchemy | Media | Basado en entities.py existente |
| Escribir schemas Pydantic | Media | Derivados de modelos |
| Implementar routers FastAPI | Media | CRUD patterns repetitivos |
| Configurar autenticación JWT | Media | Código estándar con variaciones |
| Escribir APIClient completo | Media | HTTP client straightforward |
| Modificar servicios existentes | Media | Adaptar de SQLAlchemy a HTTP |
| Escribir tests unitarios | Media | pytest patterns |
| Crear Dockerfile y docker-compose | Baja | Configuración estándar |
| Escribir migraciones Alembic | Media | Basadas en modelos |
| Modificar UI tabs existentes | Media-Alta | Cambios en lógica de carga |
| Documentar API | Baja | Swagger automático + markdown |

### 8.2 Lo que Claude NO puede hacer

| Tarea | Razón | Quién debe hacerlo |
|-------|-------|-------------------|
| Ejecutar deploy en Railway | Requiere cuenta y credenciales | Usuario |
| Crear cuenta en servicios cloud | Requiere datos personales | Usuario |
| Configurar DNS personalizado | Acceso a registrador | Usuario |
| Generar SECRET_KEY producción | Seguridad crítica | Usuario (openssl) |
| Ejecutar migraciones en prod | Acceso a BD producción | Usuario |
| Monitorear en producción | Acceso a logs | Usuario |
| Configurar backups automáticos | Acceso a infra | Usuario |
| Comprar dominio | Pago | Usuario |
| Testing en dispositivos reales | Acceso físico | Usuario |

### 8.3 Modelo de Colaboración Recomendado

```
┌─────────────────────────────────────────────────────────────┐
│                     FLUJO DE TRABAJO                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Usuario define requisito                                │
│          ↓                                                  │
│  2. Claude escribe código/configuración                     │
│          ↓                                                  │
│  3. Usuario revisa y valida                                 │
│          ↓                                                  │
│  4. Usuario ejecuta comandos sensibles                      │
│     (deploy, migrations, credenciales)                      │
│          ↓                                                  │
│  5. Claude ayuda a debuggear si hay errores                 │
│          ↓                                                  │
│  6. Iterar hasta completar                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 8.4 Comandos que el Usuario debe ejecutar

```bash
# Crear cuenta Railway (manual en web)
# https://railway.app

# Generar SECRET_KEY seguro
openssl rand -hex 32

# Deploy inicial Railway (después de login)
railway init
railway up

# Ejecutar migraciones en producción
railway run alembic upgrade head

# Ver logs en producción
railway logs
```

---

## 9. Alternativas Consideradas

### 9.1 Opción A: Solo Desktop (Status Quo)

```
Pros:
- Sin cambios de arquitectura
- Sin costos de hosting
- Funciona offline

Contras:
- Sin multi-usuario
- Sin acceso remoto
- Sin backup centralizado
- Datos en cada PC

Recomendación: Solo si no se necesita colaboración
```

### 9.2 Opción B: Web App Completa (SPA + API)

```
Pros:
- Accesible desde cualquier navegador
- Sin instalación en clientes
- Actualizaciones instantáneas

Contras:
- Reescritura completa de UI
- Pérdida de funcionalidad desktop (PDF local, etc.)
- Mayor esfuerzo de desarrollo

Recomendación: Fase futura si se quiere web
```

### 9.3 Opción C: Híbrido Desktop + API (Elegida)

```
Pros:
- Reutiliza UI existente
- Multi-usuario y multi-empresa
- Acceso remoto a datos
- Cliente rico en funcionalidades

Contras:
- Requiere conexión a internet
- Dos codebases que mantener
- Complejidad de sincronización

Recomendación: ELEGIDA - Balance óptimo
```

### 9.4 Opción D: Sincronización P2P

```
Pros:
- Sin servidor central
- Sin costos de hosting

Contras:
- Muy complejo de implementar
- Conflictos de sincronización
- Sin multi-tenancy real

Recomendación: Demasiado complejo
```

---

## 10. Archivos Críticos del Proyecto

### 10.1 Archivos a Modificar

| Archivo | Ubicación | Cambios |
|---------|-----------|---------|
| `entities.py` | `dragofactu/models/` | Agregar Company, company_id a entidades |
| `database.py` | `dragofactu/models/` | Configuración para PostgreSQL |
| `entity_services.py` | `dragofactu/services/business/` | Base para adaptar a API |
| `auth_service.py` | `dragofactu/services/auth/` | Base para JWT backend |
| `dragofactu_complete.py` | `/` | UI tabs, LoginDialog |
| `config.py` | `dragofactu/config/` | Agregar API_BASE_URL |

### 10.2 Archivos a Crear

| Archivo | Ubicación | Propósito |
|---------|-----------|-----------|
| `api_client.py` | `dragofactu/services/` | Cliente HTTP para API |
| `main.py` | `backend/app/` | Entry point FastAPI |
| `config.py` | `backend/app/` | Settings Pydantic |
| `database.py` | `backend/app/` | Engine PostgreSQL |
| Routers | `backend/app/api/v1/` | Endpoints por módulo |
| Schemas | `backend/app/schemas/` | Pydantic models |
| Models | `backend/app/models/` | SQLAlchemy models |
| `Dockerfile` | `backend/` | Imagen Docker |
| `docker-compose.yml` | `/` | Dev environment |
| `requirements.txt` | `backend/` | Dependencias Python |

### 10.3 Rutas Absolutas del Proyecto

```
/Users/jaimeruiz/Dragofactu/
├── dragofactu/                    # Paquete modular
│   ├── models/
│   │   ├── entities.py            # ← MODIFICAR
│   │   └── database.py            # ← MODIFICAR
│   ├── services/
│   │   ├── api_client.py          # ← CREAR
│   │   └── business/
│   │       └── entity_services.py # ← REFERENCIA
│   └── config/
│       └── config.py              # ← MODIFICAR
├── dragofactu_complete.py         # ← MODIFICAR UI
├── backend/                       # ← CREAR DIRECTORIO
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/
│   │   ├── services/
│   │   └── core/
│   ├── alembic/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
└── docker-compose.yml
```

---

## 11. Glosario

| Término | Definición |
|---------|------------|
| **Multi-tenancy** | Arquitectura donde múltiples clientes (empresas) comparten la misma infraestructura pero con datos aislados |
| **Tenant** | Un cliente/empresa en un sistema multi-tenant |
| **JWT (JSON Web Token)** | Estándar para tokens de autenticación seguros y stateless |
| **Access Token** | Token de corta duración para autenticar requests API |
| **Refresh Token** | Token de larga duración para obtener nuevos access tokens |
| **RBAC** | Role-Based Access Control - control de acceso basado en roles |
| **ORM** | Object-Relational Mapping - mapeo de objetos a base de datos |
| **Soft Delete** | Marcar como eliminado (is_active=False) sin borrar físicamente |
| **Cold Start** | Tiempo de inicio cuando una instancia serverless estaba inactiva |
| **Row-Level Security** | Seguridad a nivel de fila en base de datos |
| **Pydantic** | Librería Python para validación de datos con type hints |
| **SQLAlchemy** | ORM más popular de Python |
| **FastAPI** | Framework web moderno para APIs en Python |
| **Alembic** | Herramienta de migraciones para SQLAlchemy |

---

## 12. Lecciones Aprendidas y Recomendaciones (Revisión 2026-02-06)

Esta sección documenta los problemas encontrados durante la implementación y las recomendaciones para futuros agentes IA que trabajen en este proyecto.

### 12.1 Evaluación General: 7/10

La implementación del backend y la estructura base es sólida, pero la integración con el frontend tiene inconsistencias graves que causan errores en producción.

### 12.2 Problemas Críticos Encontrados

#### ❌ GRAVE: Inconsistencia Schema/Frontend

**Problema:** El schema `ClientCreate` no incluía el campo `is_active`, pero el frontend lo enviaba, causando Error 400.

**Archivo:** `backend/app/schemas/client.py`

**Solución aplicada:**
```python
class ClientCreate(ClientBase):
    """Client creation schema."""
    is_active: bool = True  # ← Añadido

class ClientUpdate(BaseModel):
    # ... otros campos ...
    is_active: Optional[bool] = None  # ← Añadido
```

**Lección:** SIEMPRE verificar que los campos enviados por el frontend coincidan con los aceptados por el schema Pydantic.

#### ❌ GRAVE: Métodos que ignoran el modo remoto

**Problema:** Varios métodos en `dragofactu_complete.py` nunca verifican `app_mode.is_remote` y siempre usan SQLite local.

**Métodos afectados:**
1. `_get_user_reminders()` (línea ~1417) - Dashboard siempre muestra recordatorios locales
2. `edit_document()` (línea ~4712) - Edición siempre usa BD local
3. `open_document_editor()` (línea ~4601) - Diálogo siempre carga datos locales
4. `view_document()` (línea ~4626) - Vista siempre recarga de BD local

**Patrón que DEBIÓ usarse:**
```python
def some_method(self):
    app_mode = get_app_mode()
    if app_mode.is_remote:
        return self._some_method_remote(app_mode.api)
    else:
        return self._some_method_local()
```

#### ❌ GRAVE: Conversión UUID inconsistente

**Problema:** El API devuelve IDs como strings, pero el código local espera objetos UUID, causando `'str' object has no attribute 'hex'`.

**Solución correcta:**
```python
# Siempre normalizar IDs antes de usarlos
def normalize_id(id_value):
    if isinstance(id_value, str):
        return uuid.UUID(id_value)
    return id_value
```

### 12.3 Cosas MAL Hechas que NO deben repetirse

1. **NO marcar métodos como "completados" sin probarlos** - Varios métodos fueron documentados como "híbridos" pero nunca se implementó el soporte remoto.

2. **NO asumir que `SessionLocal()` funciona en modo remoto** - Cada uso de `SessionLocal()` debe estar condicionado a `not app_mode.is_remote`.

3. **NO ignorar la validación de schemas** - El frontend debe enviar EXACTAMENTE lo que el schema espera.

4. **NO mezclar tipos de ID** - Decidir si se usan strings o UUIDs y ser CONSISTENTE en todo el código.

5. **NO modificar múltiples archivos sin verificar integración** - Cada cambio debe probarse end-to-end.

### 12.4 Recomendaciones para Futuros Agentes IA

#### Antes de modificar código:
1. **Leer CLAUDE.md completo** - Contiene el estado actual y patrones establecidos
2. **Buscar usos existentes** del patrón que vas a implementar
3. **Verificar schemas Pydantic** antes de enviar datos al API

#### Durante la implementación:
1. **Un commit por feature funcional** - No commits parciales
2. **Probar en ambos modos** (local y remoto) antes de marcar como completado
3. **Usar el patrón establecido:**
   ```python
   app_mode = get_app_mode()
   if app_mode.is_remote:
       # Usar app_mode.api.method()
   else:
       # Usar SessionLocal()
   ```

#### Después de implementar:
1. **Actualizar CLAUDE.md** con los cambios realizados
2. **Documentar problemas encontrados** para el siguiente agente
3. **NO mentir sobre el estado** - Si algo no funciona, documentarlo

### 12.5 Checklist de Verificación para Modo Híbrido

Antes de marcar una tab como "completada", verificar:

- [ ] `refresh_data()` usa API en modo remoto
- [ ] `create_*()` usa API en modo remoto
- [ ] `update_*()` usa API en modo remoto
- [ ] `delete_*()` usa API en modo remoto
- [ ] Diálogos de edición cargan datos del API en modo remoto
- [ ] Los IDs se manejan correctamente (string vs UUID)
- [ ] No hay llamadas a `SessionLocal()` sin verificar modo
- [ ] Los datos se muestran correctamente en la tabla después de crear/editar

### 12.6 Archivos Críticos a Revisar

| Archivo | Qué verificar |
|---------|---------------|
| `dragofactu_complete.py` | Todos los métodos de cada Tab |
| `backend/app/schemas/*.py` | Campos coinciden con frontend |
| `dragofactu/services/api_client.py` | Métodos cubren todos los endpoints |
| `backend/app/api/v1/*.py` | Responses incluyen todos los campos necesarios |

---

## Checklist Final

Antes de empezar la implementación, verificar:

- [ ] Este documento ha sido leído completamente
- [ ] Se entiende la arquitectura objetivo
- [ ] Se tiene acceso a los archivos del proyecto
- [ ] Se tiene Python 3.10+ instalado
- [ ] Se tiene Docker instalado (para PostgreSQL local)
- [ ] Se tiene cuenta en Railway/Render (o se creará)
- [ ] Se entiende el modelo de colaboración Claude/Usuario

---

**Documento creado por:** Claude Opus 4.5
**Fecha:** 2026-02-01
**Versión:** 1.0
**Próxima revisión:** Al iniciar Fase 1
