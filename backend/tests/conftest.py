"""
Pytest configuration and fixtures for Dragofactu API tests.
"""
import os
import pytest
from typing import Generator, Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

# Set test database URL BEFORE importing app modules
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

# Clear any cached settings
from app import config
config._settings = None

# Now import app modules
from app.main import app
from app.database import engine, SessionLocal, get_db
from app.models.base import Base
from app.models import Company, User, UserRole
from app.core.security import hash_password, create_access_token


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database session."""
    # The db fixture already creates tables using the app's engine
    # which uses StaticPool for in-memory SQLite
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def test_company(db: Session) -> Company:
    """Create a test company."""
    company = Company(
        id=uuid.uuid4(),
        code="TEST001",
        name="Test Company S.L.",
        tax_id="B12345678",
        address="Calle Test 123",
        city="Madrid",
        postal_code="28001",
        country="ES",
        phone="+34 912 345 678",
        email="test@testcompany.com",
        is_active=True
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@pytest.fixture(scope="function")
def test_user(db: Session, test_company: Company) -> User:
    """Create a test admin user."""
    user = User(
        id=uuid.uuid4(),
        company_id=test_company.id,
        username="testadmin",
        email="admin@testcompany.com",
        password_hash=hash_password("testpass123"),
        full_name="Test Admin User",
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_user_warehouse(db: Session, test_company: Company) -> User:
    """Create a test warehouse user (limited permissions)."""
    user = User(
        id=uuid.uuid4(),
        company_id=test_company.id,
        username="warehouse",
        email="warehouse@testcompany.com",
        password_hash=hash_password("warehouse123"),
        full_name="Warehouse User",
        role=UserRole.WAREHOUSE,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user: User) -> Dict[str, str]:
    """Get authentication headers for test user."""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def auth_headers_warehouse(test_user_warehouse: User) -> Dict[str, str]:
    """Get authentication headers for warehouse user."""
    token = create_access_token(data={"sub": str(test_user_warehouse.id)})
    return {"Authorization": f"Bearer {token}"}


# Helper function to create common test data
def create_test_client_data() -> Dict[str, Any]:
    """Generate test client data."""
    return {
        "code": f"CLI{uuid.uuid4().hex[:6].upper()}",
        "name": "Cliente de Prueba",
        "tax_id": "A12345678",
        "address": "Calle Prueba 1",
        "city": "Barcelona",
        "postal_code": "08001",
        "country": "ES",
        "phone": "+34 931 234 567",
        "email": "cliente@prueba.com"
    }


def create_test_product_data() -> Dict[str, Any]:
    """Generate test product data."""
    return {
        "code": f"PROD{uuid.uuid4().hex[:6].upper()}",
        "name": "Producto de Prueba",
        "description": "Descripción del producto de prueba",
        "category": "General",
        "purchase_price": 10.00,
        "sale_price": 25.00,
        "tax_rate": 21.0,
        "current_stock": 100,
        "minimum_stock": 10
    }


def create_test_supplier_data() -> Dict[str, Any]:
    """Generate test supplier data."""
    return {
        "code": f"SUP{uuid.uuid4().hex[:6].upper()}",
        "name": "Proveedor de Prueba",
        "tax_id": "B87654321",
        "contact_name": "Juan Proveedor",
        "phone": "+34 912 345 678",
        "email": "proveedor@prueba.com"
    }
