"""
Tests for per-company email settings and status endpoints.
"""
import smtplib
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Company
from app.core.security import encrypt_secret_value


class TestCompanyEmailSettings:
    """Test company SMTP settings CRUD and connection checks."""

    def test_get_email_settings_default_unconfigured(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        response = client.get("/api/v1/company/email/settings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is False
        assert data["smtp_host"] is None

    def test_update_email_settings_encrypts_password(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        test_user,
    ):
        payload = {
            "smtp_host": "smtp.test.com",
            "smtp_port": 587,
            "smtp_user": "billing@test.com",
            "smtp_password": "super-secret",
            "smtp_use_tls": True,
            "smtp_from_email": "billing@test.com",
            "smtp_from_name": "Test Billing",
        }

        response = client.put("/api/v1/company/email/settings", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is True
        assert data["smtp_host"] == "smtp.test.com"
        assert data["smtp_user"] == "billing@test.com"
        assert data["smtp_from_name"] == "Test Billing"

        company = db.query(Company).filter(Company.id == test_user.company_id).first()
        assert company is not None
        assert company.smtp_password_encrypted is not None
        assert company.smtp_password_encrypted != "super-secret"

    def test_update_email_settings_forbidden_for_warehouse(
        self,
        client: TestClient,
        auth_headers_warehouse: dict,
    ):
        payload = {"smtp_host": "smtp.test.com", "smtp_user": "w@test.com"}
        response = client.put(
            "/api/v1/company/email/settings",
            json=payload,
            headers=auth_headers_warehouse,
        )
        assert response.status_code == 403

    def test_test_email_settings_success(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        test_user,
        monkeypatch,
    ):
        company = db.query(Company).filter(Company.id == test_user.company_id).first()
        company.smtp_host = "smtp.test.com"
        company.smtp_port = 587
        company.smtp_user = "billing@test.com"
        company.smtp_password_encrypted = encrypt_secret_value("app-password")
        company.smtp_use_tls = True
        db.commit()

        class DummySMTP:
            def __init__(self, host, port, timeout=None):
                self.host = host
                self.port = port
                self.timeout = timeout

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def starttls(self):
                return None

            def login(self, user, password):
                assert user == "billing@test.com"
                assert password == "app-password"
                return None

        monkeypatch.setattr(smtplib, "SMTP", DummySMTP)

        response = client.post("/api/v1/company/email/test", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_test_email_settings_not_configured(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        response = client.post("/api/v1/company/email/test", headers=auth_headers)
        assert response.status_code == 400
        assert "no configurado" in response.json()["detail"].lower()


class TestDocumentEmailStatusByCompany:
    """Ensure document email status uses tenant SMTP config."""

    def test_document_email_status_false_without_company_config(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        response = client.get("/api/v1/documents/email/status", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["configured"] is False

    def test_document_email_status_true_with_company_config(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        test_user,
    ):
        company = db.query(Company).filter(Company.id == test_user.company_id).first()
        company.smtp_host = "smtp.test.com"
        company.smtp_port = 587
        company.smtp_user = "billing@test.com"
        company.smtp_password_encrypted = encrypt_secret_value("app-password")
        company.smtp_use_tls = True
        db.commit()

        response = client.get("/api/v1/documents/email/status", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["configured"] is True
