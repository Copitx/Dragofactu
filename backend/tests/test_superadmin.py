"""
Tests for superadmin platform-level endpoints and isolation.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from app.models import User, UserRole, Company
from app.core.security import hash_password, create_access_token


@pytest.fixture
def superadmin_user(db: Session, test_company: Company) -> User:
    """Create a superadmin user for testing."""
    user = User(
        id=uuid.uuid4(),
        company_id=test_company.id,
        username="superadmin",
        email="super@dragofactu.com",
        password_hash=hash_password("super123!"),
        full_name="Platform Superadmin",
        role=UserRole.ADMIN,
        is_active=True,
        is_superadmin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def superadmin_headers(superadmin_user: User) -> dict:
    token = create_access_token(data={"sub": str(superadmin_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_company(db: Session) -> Company:
    """Create a second company to test isolation."""
    company = Company(
        id=uuid.uuid4(),
        code="COMPANY2",
        name="Second Company S.L.",
        tax_id="B99999999",
        country="ES",
        is_active=True,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


class TestSuperadminAccess:
    def test_superadmin_can_list_companies(
        self, client: TestClient, superadmin_headers: dict
    ):
        response = client.get("/api/v1/superadmin/companies", headers=superadmin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 1

    def test_regular_admin_cannot_access_superadmin(
        self, client: TestClient, auth_headers: dict
    ):
        response = client.get("/api/v1/superadmin/companies", headers=auth_headers)
        assert response.status_code == 403

    def test_unauthenticated_cannot_access_superadmin(self, client: TestClient):
        response = client.get("/api/v1/superadmin/companies")
        assert response.status_code == 401

    def test_superadmin_can_view_company_stats(
        self, client: TestClient, superadmin_headers: dict, test_company: Company
    ):
        response = client.get(
            f"/api/v1/superadmin/companies/{test_company.id}/stats",
            headers=superadmin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # Response has "stats" nested key or top-level counts
        stats = data.get("stats", data)
        assert "users" in stats or "users_count" in stats

    def test_superadmin_can_list_company_users(
        self, client: TestClient, superadmin_headers: dict, test_company: Company
    ):
        response = client.get(
            f"/api/v1/superadmin/companies/{test_company.id}/users",
            headers=superadmin_headers,
        )
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        assert len(users) >= 1

    def test_superadmin_global_audit(
        self, client: TestClient, superadmin_headers: dict
    ):
        response = client.get("/api/v1/superadmin/audit", headers=superadmin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_superadmin_global_audit_returns_list(
        self, client: TestClient, superadmin_headers: dict
    ):
        """Global audit log returns paginated result."""
        response = client.get("/api/v1/superadmin/audit", headers=superadmin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)


class TestMultiTenantIsolation:
    def test_superadmin_sees_all_companies(
        self, client: TestClient, superadmin_headers: dict,
        test_company: Company, second_company: Company
    ):
        response = client.get("/api/v1/superadmin/companies", headers=superadmin_headers)
        assert response.status_code == 200
        data = response.json()
        company_ids = [c["id"] for c in data["items"]]
        assert str(test_company.id) in company_ids
        assert str(second_company.id) in company_ids

    def test_regular_user_cannot_see_other_company_data(
        self, client: TestClient, auth_headers: dict, second_company: Company
    ):
        # Regular user should not see companies endpoint (superadmin only)
        response = client.get("/api/v1/superadmin/companies", headers=auth_headers)
        assert response.status_code == 403


class TestCompanyUserCreation:
    def test_admin_can_create_company_user(
        self, client: TestClient, auth_headers: dict
    ):
        response = client.post(
            "/api/v1/auth/users",
            json={
                "username": "newteammember",
                "email": "new@company.com",
                "full_name": "New Team Member",
                "role": "management",
                "password": "Pass1234!",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newteammember"
        assert data["role"] == "management"
        assert data.get("is_superadmin", False) is False

    def test_created_user_cannot_be_superadmin(
        self, client: TestClient, auth_headers: dict
    ):
        """Admin cannot create superadmin users via API."""
        response = client.post(
            "/api/v1/auth/users",
            json={
                "username": "trysuper",
                "email": "trysuper@company.com",
                "full_name": "Try Super",
                "role": "admin",
                "password": "Pass1234!",
                "is_superadmin": True,  # Should be ignored
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data.get("is_superadmin", False) is False

    def test_management_user_cannot_create_users(
        self, client: TestClient, auth_headers_warehouse: dict
    ):
        response = client.post(
            "/api/v1/auth/users",
            json={
                "username": "unauthorized",
                "email": "unauth@company.com",
                "full_name": "Unauthorized",
                "role": "read_only",
                "password": "Pass1234!",
            },
            headers=auth_headers_warehouse,
        )
        assert response.status_code == 403
