"""
Tests for dashboard stats endpoint.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models import (
    Company, Client, Product, Document,
    DocumentType, DocumentStatus
)


class TestDashboardEndpoints:
    """Test dashboard stats endpoint."""

    def test_get_stats_empty(self, client: TestClient, auth_headers: dict):
        """Test getting stats when no data exists."""
        response = client.get(
            "/api/v1/dashboard/stats",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["clients"] == 0
        assert data["products"] == 0
        assert data["total_documents"] == 0

    def test_get_stats_with_data(
        self, client: TestClient, auth_headers: dict, db: Session,
        test_company: Company, test_user
    ):
        """Test getting stats reflects actual data."""
        # Create clients
        for i in range(3):
            db.add(Client(
                company_id=test_company.id,
                code=f"DASHCLI{i:03d}",
                name=f"Dashboard Client {i}"
            ))

        # Create products (one with low stock)
        db.add(Product(
            company_id=test_company.id, code="DASHPROD1",
            name="Normal Product", sale_price=10.0,
            current_stock=100, minimum_stock=10
        ))
        db.add(Product(
            company_id=test_company.id, code="DASHPROD2",
            name="Low Stock Product", sale_price=20.0,
            current_stock=3, minimum_stock=10
        ))

        # Create a client for document
        doc_client = Client(
            company_id=test_company.id,
            code="DOCCLI001",
            name="Doc Client"
        )
        db.add(doc_client)
        db.commit()
        db.refresh(doc_client)

        # Create a document
        db.add(Document(
            company_id=test_company.id,
            code="FAC-DASH-001",
            type=DocumentType.INVOICE,
            status=DocumentStatus.DRAFT,
            client_id=doc_client.id,
            issue_date=datetime.now(timezone.utc),
            subtotal=100.00, tax_amount=21.00, total=121.00,
            created_by=test_user.id
        ))
        db.commit()

        response = client.get(
            "/api/v1/dashboard/stats",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["clients"] == 4  # 3 + 1 for document
        assert data["products"] == 2
        assert data["low_stock"] == 1
        assert data["total_documents"] >= 1

    def test_get_stats_unauthorized(self, client: TestClient):
        """Test getting stats without auth fails."""
        response = client.get("/api/v1/dashboard/stats")

        assert response.status_code == 401

    def test_stats_multi_tenancy(
        self, client: TestClient, auth_headers: dict, db: Session,
        test_company: Company
    ):
        """Test that stats only count own company's data."""
        # Create own data
        db.add(Client(
            company_id=test_company.id, code="OWNCLI", name="Own Client"
        ))

        # Create other company data
        other_company = Company(code="OTHERDASH", name="Other Dashboard Co")
        db.add(other_company)
        db.commit()
        db.refresh(other_company)

        db.add(Client(
            company_id=other_company.id, code="FOREIGN", name="Foreign Client"
        ))
        db.commit()

        response = client.get(
            "/api/v1/dashboard/stats",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["clients"] == 1  # Only own client
