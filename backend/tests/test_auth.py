"""
Tests for authentication endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User, Company
from tests.conftest import create_test_client_data


class TestAuthEndpoints:
    """Test auth endpoints."""

    def test_register_company(self, client: TestClient):
        """Test company registration creates company and admin user."""
        response = client.post("/api/v1/auth/register", json={
            "company_code": "NEW001",
            "company_name": "New Company S.L.",
            "username": "newadmin",
            "email": "admin@newcompany.com",
            "password": "securepass123"
        })

        assert response.status_code == 201
        data = response.json()
        # Register returns UserResponse (user info only)
        assert data["username"] == "newadmin"
        assert data["role"] == "admin"
        assert data["email"] == "admin@newcompany.com"
        assert "company_id" in data

    def test_register_duplicate_company_code(self, client: TestClient, test_company: Company):
        """Test registration fails with duplicate company code."""
        response = client.post("/api/v1/auth/register", json={
            "company_code": test_company.code,  # Duplicate
            "company_name": "Another Company",
            "username": "admin2",
            "email": "admin2@company.com",
            "password": "password123"
        })

        assert response.status_code == 400
        assert "existe" in response.json()["detail"].lower()

    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login."""
        response = client.post("/api/v1/auth/login", json={
            "username": "testadmin",
            "password": "testpass123"
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["username"] == "testadmin"

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login fails with wrong password."""
        response = client.post("/api/v1/auth/login", json={
            "username": "testadmin",
            "password": "wrongpassword"
        })

        assert response.status_code == 401
        assert "incorrectas" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login fails with nonexistent user."""
        response = client.post("/api/v1/auth/login", json={
            "username": "noexiste",
            "password": "password123"
        })

        assert response.status_code == 401

    def test_get_me(self, client: TestClient, auth_headers: dict, test_user: User):
        """Test get current user info."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testadmin"
        assert data["email"] == "admin@testcompany.com"
        assert data["role"] == "admin"

    def test_get_me_unauthorized(self, client: TestClient):
        """Test get me fails without auth."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_refresh_token(self, client: TestClient, test_user: User):
        """Test refresh token generates new access token."""
        # First login to get tokens
        login_response = client.post("/api/v1/auth/login", json={
            "username": "testadmin",
            "password": "testpass123"
        })
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token
        })

        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh fails with invalid token."""
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.here"
        })

        assert response.status_code == 401

    def test_logout(self, client: TestClient, auth_headers: dict):
        """Test logout endpoint."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)

        assert response.status_code == 200
        assert "sesion" in response.json()["message"].lower() or "cerrada" in response.json()["message"].lower()


class TestPasswordSecurity:
    """Test password security features."""

    def test_password_is_hashed(self, db: Session, test_user: User):
        """Verify password is not stored in plain text."""
        assert test_user.password_hash != "testpass123"
        assert len(test_user.password_hash) > 50  # bcrypt hashes are long

    def test_password_verification_works(self, client: TestClient, test_user: User):
        """Test that correct password works."""
        response = client.post("/api/v1/auth/login", json={
            "username": "testadmin",
            "password": "testpass123"
        })
        assert response.status_code == 200

    def test_password_case_sensitive(self, client: TestClient, test_user: User):
        """Test passwords are case sensitive."""
        response = client.post("/api/v1/auth/login", json={
            "username": "testadmin",
            "password": "TESTPASS123"  # Wrong case
        })
        assert response.status_code == 401
