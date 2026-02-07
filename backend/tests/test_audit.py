"""
Tests for Audit Log endpoints (Fase 16.2).
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models import Company, User, UserRole
from app.core.security import hash_password, create_access_token


class TestAuditLogEndpoints:
    """Test audit log listing and filtering."""

    def _create_audit_entries(self, db, company_id, user_id, count=5):
        """Helper to create test audit entries."""
        actions = ["create", "update", "delete"]
        entities = ["client", "product", "document"]
        for i in range(count):
            entry = AuditLog(
                company_id=company_id,
                user_id=user_id,
                action=actions[i % len(actions)],
                entity_type=entities[i % len(entities)],
                entity_id=uuid.uuid4().hex,
                details=f'{{"test": "entry {i}"}}'
            )
            db.add(entry)
        db.commit()

    def test_list_audit_empty(self, client: TestClient, auth_headers):
        """List audit when empty returns empty list."""
        response = client.get("/api/v1/audit", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_audit_with_data(self, client: TestClient, auth_headers, db, test_company, test_user):
        """List audit returns entries."""
        self._create_audit_entries(db, test_company.id, test_user.id, 5)

        response = client.get("/api/v1/audit", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5

    def test_list_audit_pagination(self, client: TestClient, auth_headers, db, test_company, test_user):
        """List audit supports pagination."""
        self._create_audit_entries(db, test_company.id, test_user.id, 10)

        response = client.get("/api/v1/audit?skip=0&limit=3", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert len(data["items"]) == 3

    def test_list_audit_filter_action(self, client: TestClient, auth_headers, db, test_company, test_user):
        """Filter audit by action type."""
        self._create_audit_entries(db, test_company.id, test_user.id, 6)

        response = client.get("/api/v1/audit?action=create", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # 6 entries, actions cycle: create, update, delete, create, update, delete -> 2 creates
        assert data["total"] == 2
        for item in data["items"]:
            assert item["action"] == "create"

    def test_list_audit_filter_entity_type(self, client: TestClient, auth_headers, db, test_company, test_user):
        """Filter audit by entity type."""
        self._create_audit_entries(db, test_company.id, test_user.id, 6)

        response = client.get("/api/v1/audit?entity_type=client", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # 6 entries, entities cycle: client, product, document, client, product, document -> 2 clients
        assert data["total"] == 2
        for item in data["items"]:
            assert item["entity_type"] == "client"

    def test_list_audit_unauthorized(self, client: TestClient):
        """Audit without auth returns 401."""
        response = client.get("/api/v1/audit")
        assert response.status_code == 401


class TestAuditMultiTenancy:
    """Test audit log multi-tenancy isolation."""

    def test_cannot_see_other_company_audit(self, client: TestClient, auth_headers, db, test_company, test_user):
        """Cannot see audit entries from another company."""
        # Create entry in test company
        entry1 = AuditLog(
            company_id=test_company.id,
            user_id=test_user.id,
            action="create",
            entity_type="client",
        )
        db.add(entry1)

        # Create another company + user + entry
        other_company = Company(code="OTHER01", name="Other Co", is_active=True)
        db.add(other_company)
        db.commit()
        db.refresh(other_company)

        other_user = User(
            company_id=other_company.id,
            username="otheruser",
            email="other@other.com",
            password_hash="$2b$12$dummy",
            full_name="Other User",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        entry2 = AuditLog(
            company_id=other_company.id,
            user_id=other_user.id,
            action="delete",
            entity_type="product",
        )
        db.add(entry2)
        db.commit()

        response = client.get("/api/v1/audit", headers=auth_headers)
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["action"] == "create"
