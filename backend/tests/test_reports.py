"""
Tests for Financial Reports endpoints (Fase 16.3).
"""
import uuid
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Document, DocumentType, DocumentStatus, Client, Company, User, UserRole
from app.core.security import hash_password, create_access_token


class TestReportEndpoints:
    """Test financial report endpoints."""

    def _create_test_documents(self, db, company_id, user_id, client_id):
        """Create sample documents for reports."""
        # Invoice - paid
        inv1 = Document(
            company_id=company_id,
            code="FAC-2026-00001",
            type=DocumentType.INVOICE,
            status=DocumentStatus.PAID,
            issue_date=datetime(2026, 1, 15, tzinfo=timezone.utc),
            client_id=client_id,
            created_by=user_id,
            subtotal=1000.0,
            tax_amount=210.0,
            total=1210.0,
        )
        # Invoice - sent (unpaid)
        inv2 = Document(
            company_id=company_id,
            code="FAC-2026-00002",
            type=DocumentType.INVOICE,
            status=DocumentStatus.SENT,
            issue_date=datetime(2026, 1, 20, tzinfo=timezone.utc),
            client_id=client_id,
            created_by=user_id,
            subtotal=500.0,
            tax_amount=105.0,
            total=605.0,
        )
        # Quote
        quote = Document(
            company_id=company_id,
            code="PRE-2026-00001",
            type=DocumentType.QUOTE,
            status=DocumentStatus.SENT,
            issue_date=datetime(2026, 1, 10, tzinfo=timezone.utc),
            client_id=client_id,
            created_by=user_id,
            subtotal=2000.0,
            tax_amount=420.0,
            total=2420.0,
        )
        # Delivery note
        dn = Document(
            company_id=company_id,
            code="ALB-2026-00001",
            type=DocumentType.DELIVERY_NOTE,
            status=DocumentStatus.SENT,
            issue_date=datetime(2026, 2, 5, tzinfo=timezone.utc),
            client_id=client_id,
            created_by=user_id,
            subtotal=300.0,
            tax_amount=63.0,
            total=363.0,
        )
        db.add_all([inv1, inv2, quote, dn])
        db.commit()

    def _create_client(self, db, company_id):
        """Create a test client for documents."""
        c = Client(company_id=company_id, code="RPTCLI01", name="Report Client")
        db.add(c)
        db.commit()
        db.refresh(c)
        return c

    def test_monthly_report_empty(self, client: TestClient, auth_headers):
        """Monthly report with no data returns zeros."""
        response = client.get("/api/v1/reports/monthly?year=2026&month=6", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_invoiced"] == 0
        assert data["total_paid"] == 0
        assert data["total_pending"] == 0
        assert data["document_count"] == 0

    def test_monthly_report_with_data(self, client: TestClient, auth_headers, db, test_company, test_user):
        """Monthly report returns correct totals."""
        test_client = self._create_client(db, test_company.id)
        self._create_test_documents(db, test_company.id, test_user.id, test_client.id)

        response = client.get("/api/v1/reports/monthly?year=2026&month=1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        # January has: 2 invoices (1210 + 605 = 1815), 1 quote (2420), 0 delivery notes
        assert data["total_invoiced"] == 1815.0
        assert data["total_paid"] == 1210.0
        assert data["total_pending"] == 605.0
        assert data["total_quotes"] == 2420.0
        assert data["document_count"] == 3  # 2 invoices + 1 quote

        # Check by_type breakdown
        by_type = {t["type"]: t for t in data["by_type"]}
        assert by_type["invoice"]["count"] == 2
        assert by_type["invoice"]["total"] == 1815.0
        assert by_type["quote"]["count"] == 1
        assert by_type["quote"]["total"] == 2420.0

    def test_quarterly_report(self, client: TestClient, auth_headers, db, test_company, test_user):
        """Quarterly report aggregates correctly."""
        test_client = self._create_client(db, test_company.id)
        self._create_test_documents(db, test_company.id, test_user.id, test_client.id)

        response = client.get("/api/v1/reports/quarterly?year=2026&quarter=1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        # Q1: all 4 documents (Jan: 2 inv + 1 quote, Feb: 1 delivery note)
        assert data["document_count"] == 4
        assert data["total_invoiced"] == 1815.0
        assert data["total_paid"] == 1210.0

    def test_annual_report(self, client: TestClient, auth_headers, db, test_company, test_user):
        """Annual report has 12 monthly breakdowns."""
        test_client = self._create_client(db, test_company.id)
        self._create_test_documents(db, test_company.id, test_user.id, test_client.id)

        response = client.get("/api/v1/reports/annual?year=2026", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        assert data["year"] == 2026
        assert len(data["months"]) == 12
        assert data["total_invoiced"] == 1815.0
        assert data["total_paid"] == 1210.0
        assert data["total_pending"] == 605.0

        # January should have 3 docs
        jan = data["months"][0]
        assert jan["document_count"] == 3

        # February should have 1 doc
        feb = data["months"][1]
        assert feb["document_count"] == 1

    def test_monthly_report_unauthorized(self, client: TestClient):
        """Reports without auth returns 401."""
        response = client.get("/api/v1/reports/monthly?year=2026&month=1")
        assert response.status_code == 401

    def test_monthly_report_invalid_params(self, client: TestClient, auth_headers):
        """Reports with invalid params returns 422."""
        response = client.get("/api/v1/reports/monthly?year=2026&month=13", headers=auth_headers)
        assert response.status_code == 422

    def test_quarterly_report_invalid_quarter(self, client: TestClient, auth_headers):
        """Quarterly with invalid quarter returns 422."""
        response = client.get("/api/v1/reports/quarterly?year=2026&quarter=5", headers=auth_headers)
        assert response.status_code == 422


class TestReportMultiTenancy:
    """Test report multi-tenancy isolation."""

    def test_report_only_shows_own_data(self, client: TestClient, auth_headers, db, test_company, test_user):
        """Reports only include documents from the authenticated user's company."""
        test_client_entity = Client(company_id=test_company.id, code="OWNCLI01", name="Own Client")
        db.add(test_client_entity)
        db.commit()
        db.refresh(test_client_entity)

        # Create document in own company
        doc = Document(
            company_id=test_company.id,
            code="FAC-2026-99001",
            type=DocumentType.INVOICE,
            status=DocumentStatus.PAID,
            issue_date=datetime(2026, 3, 15, tzinfo=timezone.utc),
            client_id=test_client_entity.id,
            created_by=test_user.id,
            total=500.0,
            subtotal=413.22,
            tax_amount=86.78,
        )
        db.add(doc)

        # Create another company + document
        other_company = Company(code="RPTOTR01", name="Other Report Co", is_active=True)
        db.add(other_company)
        db.commit()
        db.refresh(other_company)

        other_user = User(
            company_id=other_company.id,
            username="rptother",
            email="rptother@test.com",
            password_hash="$2b$12$dummy",
            full_name="Other User",
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        other_client = Client(company_id=other_company.id, code="OTRCLI01", name="Other Client")
        db.add(other_client)
        db.commit()
        db.refresh(other_client)

        other_doc = Document(
            company_id=other_company.id,
            code="FAC-2026-99002",
            type=DocumentType.INVOICE,
            status=DocumentStatus.PAID,
            issue_date=datetime(2026, 3, 20, tzinfo=timezone.utc),
            client_id=other_client.id,
            created_by=other_user.id,
            total=9999.0,
            subtotal=8263.64,
            tax_amount=1735.36,
        )
        db.add(other_doc)
        db.commit()

        response = client.get("/api/v1/reports/monthly?year=2026&month=3", headers=auth_headers)
        data = response.json()
        assert data["total_invoiced"] == 500.0  # Only own company
