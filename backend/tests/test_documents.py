"""
Tests for documents endpoints with business logic.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from app.models import (
    Document, DocumentLine, DocumentType, DocumentStatus,
    Client, Product, Company
)


class TestDocumentCreation:
    """Test document creation."""

    @pytest.fixture
    def test_client_entity(self, db: Session, test_company: Company) -> Client:
        """Create a test client for documents."""
        client_entity = Client(
            company_id=test_company.id,
            code="DOCCLI001",
            name="Document Test Client"
        )
        db.add(client_entity)
        db.commit()
        db.refresh(client_entity)
        return client_entity

    @pytest.fixture
    def test_product(self, db: Session, test_company: Company) -> Product:
        """Create a test product for document lines."""
        product = Product(
            company_id=test_company.id,
            code="DOCPROD001",
            name="Document Test Product",
            sale_price=100.00,
            current_stock=50
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    def test_create_quote(
        self, client: TestClient, auth_headers: dict,
        test_client_entity: Client, test_product: Product
    ):
        """Test creating a quote document."""
        response = client.post(
            "/api/v1/documents",
            json={
                "type": "quote",
                "client_id": str(test_client_entity.id),
                "issue_date": datetime.now(timezone.utc).isoformat(),
                "lines": [
                    {
                        "line_type": "product",
                        "product_id": str(test_product.id),
                        "description": "Test Product",
                        "quantity": 2,
                        "unit_price": 100.00,
                        "discount_percent": 0
                    }
                ]
            },
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "quote"
        assert data["status"] == "draft"
        assert data["code"].startswith("PRE-")
        assert float(data["subtotal"]) == 200.00
        assert len(data["lines"]) == 1

    def test_create_invoice(
        self, client: TestClient, auth_headers: dict,
        test_client_entity: Client
    ):
        """Test creating an invoice document."""
        response = client.post(
            "/api/v1/documents",
            json={
                "type": "invoice",
                "client_id": str(test_client_entity.id),
                "issue_date": datetime.now(timezone.utc).isoformat(),
                "lines": [
                    {
                        "line_type": "text",  # Use text for service-type entries
                        "description": "Consulting Service",
                        "quantity": 5,
                        "unit_price": 50.00,
                        "discount_percent": 10
                    }
                ]
            },
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "invoice"
        assert data["code"].startswith("FAC-")
        # 5 * 50 = 250, 10% discount = 225 subtotal
        assert float(data["subtotal"]) == 225.00

    def test_create_delivery_note(
        self, client: TestClient, auth_headers: dict,
        test_client_entity: Client
    ):
        """Test creating a delivery note."""
        response = client.post(
            "/api/v1/documents",
            json={
                "type": "delivery_note",
                "client_id": str(test_client_entity.id),
                "issue_date": datetime.now(timezone.utc).isoformat(),
                "lines": [
                    {
                        "line_type": "product",
                        "description": "Delivered Item",
                        "quantity": 3,
                        "unit_price": 75.00,
                        "discount_percent": 0
                    }
                ]
            },
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"].startswith("ALB-")

    def test_create_document_invalid_client(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating document with invalid client fails."""
        fake_client_id = uuid.uuid4()

        response = client.post(
            "/api/v1/documents",
            json={
                "type": "invoice",
                "client_id": str(fake_client_id),
                "issue_date": datetime.now(timezone.utc).isoformat(),
                "lines": [
                    {
                        "line_type": "text",
                        "description": "Service",
                        "quantity": 1,
                        "unit_price": 100.00,
                        "discount_percent": 0
                    }
                ]
            },
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "cliente" in response.json()["detail"].lower()


class TestDocumentStatusTransitions:
    """Test document status workflow."""

    @pytest.fixture
    def draft_invoice(
        self, db: Session, test_company: Company, test_user
    ) -> tuple[Document, Client]:
        """Create a draft invoice for testing."""
        client_entity = Client(
            company_id=test_company.id,
            code="STATCLI",
            name="Status Test Client"
        )
        db.add(client_entity)
        db.commit()
        db.refresh(client_entity)

        document = Document(
            company_id=test_company.id,
            code="FAC-TEST-001",
            type=DocumentType.INVOICE,
            status=DocumentStatus.DRAFT,
            client_id=client_entity.id,
            issue_date=datetime.now(timezone.utc),
            subtotal=100.00,
            tax_amount=21.00,
            total=121.00,
            created_by=test_user.id
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document, client_entity

    def test_change_status_draft_to_not_sent(
        self, client: TestClient, auth_headers: dict,
        draft_invoice: tuple[Document, Client], test_user
    ):
        """Test transitioning from draft to not_sent."""
        document, _ = draft_invoice

        response = client.post(
            f"/api/v1/documents/{document.id}/change-status",
            json={"new_status": "not_sent"},
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["status"] == "not_sent"

    def test_change_status_to_sent(
        self, client: TestClient, auth_headers: dict,
        draft_invoice: tuple[Document, Client], db: Session, test_user
    ):
        """Test transitioning to sent status."""
        document, _ = draft_invoice
        document.status = DocumentStatus.NOT_SENT
        db.commit()

        response = client.post(
            f"/api/v1/documents/{document.id}/change-status",
            json={"new_status": "sent"},
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["status"] == "sent"

    def test_invalid_status_transition(
        self, client: TestClient, auth_headers: dict,
        draft_invoice: tuple[Document, Client], test_user
    ):
        """Test invalid status transition fails."""
        document, _ = draft_invoice

        # Can't go from draft directly to paid
        response = client.post(
            f"/api/v1/documents/{document.id}/change-status",
            json={"new_status": "paid"},
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "transicion" in response.json()["detail"].lower()


class TestDocumentStockDeduction:
    """Test stock deduction on invoice creation."""

    def test_stock_deducted_on_invoice_creation(
        self, client: TestClient, auth_headers: dict,
        db: Session, test_company: Company
    ):
        """Test that stock is deducted when invoice is created."""
        # Create client
        client_entity = Client(
            company_id=test_company.id,
            code="STOCKCLI",
            name="Stock Test Client"
        )
        db.add(client_entity)

        # Create product with stock
        product = Product(
            company_id=test_company.id,
            code="STOCKPROD",
            name="Stock Product",
            sale_price=50.00,
            current_stock=100
        )
        db.add(product)
        db.commit()
        db.refresh(client_entity)
        db.refresh(product)

        # Create invoice with product line - stock should be deducted immediately
        response = client.post(
            "/api/v1/documents",
            json={
                "type": "invoice",
                "client_id": str(client_entity.id),
                "issue_date": datetime.now(timezone.utc).isoformat(),
                "lines": [
                    {
                        "line_type": "product",
                        "product_id": str(product.id),
                        "description": "Stock Product",
                        "quantity": 10,
                        "unit_price": 50.00,
                        "discount_percent": 0
                    }
                ]
            },
            headers=auth_headers
        )
        assert response.status_code == 201

        # Verify stock was deducted at creation time
        db.refresh(product)
        assert product.current_stock == 90  # 100 - 10

    def test_stock_allows_negative(
        self, client: TestClient, auth_headers: dict,
        db: Session, test_company: Company
    ):
        """Test that stock can go negative when creating invoice with more than available."""
        # Create client and product with low stock
        client_entity = Client(
            company_id=test_company.id,
            code="LOWSTOCKCLI",
            name="Low Stock Client"
        )
        db.add(client_entity)

        product = Product(
            company_id=test_company.id,
            code="LOWSTOCKPROD",
            name="Low Stock Product",
            sale_price=50.00,
            current_stock=5  # Only 5 in stock
        )
        db.add(product)
        db.commit()
        db.refresh(client_entity)
        db.refresh(product)

        # Create invoice requesting more than available - should succeed with negative stock
        response = client.post(
            "/api/v1/documents",
            json={
                "type": "invoice",
                "client_id": str(client_entity.id),
                "issue_date": datetime.now(timezone.utc).isoformat(),
                "lines": [
                    {
                        "line_type": "product",
                        "product_id": str(product.id),
                        "description": "Low Stock Product",
                        "quantity": 10,  # More than available
                        "unit_price": 50.00,
                        "discount_percent": 0
                    }
                ]
            },
            headers=auth_headers
        )
        assert response.status_code == 201

        # Verify stock went negative
        db.refresh(product)
        assert product.current_stock == -5  # 5 - 10 = -5

    def test_quote_does_not_deduct_stock(
        self, client: TestClient, auth_headers: dict,
        db: Session, test_company: Company
    ):
        """Test that creating a quote does NOT deduct stock."""
        client_entity = Client(
            company_id=test_company.id,
            code="QUOTECLI",
            name="Quote Client"
        )
        db.add(client_entity)

        product = Product(
            company_id=test_company.id,
            code="QUOTEPROD",
            name="Quote Product",
            sale_price=50.00,
            current_stock=100
        )
        db.add(product)
        db.commit()
        db.refresh(client_entity)
        db.refresh(product)

        # Create quote - stock should NOT be deducted
        response = client.post(
            "/api/v1/documents",
            json={
                "type": "quote",
                "client_id": str(client_entity.id),
                "issue_date": datetime.now(timezone.utc).isoformat(),
                "lines": [
                    {
                        "line_type": "product",
                        "product_id": str(product.id),
                        "description": "Quote Product",
                        "quantity": 10,
                        "unit_price": 50.00,
                        "discount_percent": 0
                    }
                ]
            },
            headers=auth_headers
        )
        assert response.status_code == 201

        # Verify stock was NOT deducted
        db.refresh(product)
        assert product.current_stock == 100  # Unchanged


class TestDocumentConversion:
    """Test document conversion (quote to invoice/delivery note)."""

    def test_convert_quote_to_invoice(
        self, client: TestClient, auth_headers: dict,
        db: Session, test_company: Company
    ):
        """Test converting accepted quote to invoice."""
        # Create client
        client_entity = Client(
            company_id=test_company.id,
            code="CONVCLI",
            name="Conversion Client"
        )
        db.add(client_entity)
        db.commit()
        db.refresh(client_entity)

        # Create quote
        response = client.post(
            "/api/v1/documents",
            json={
                "type": "quote",
                "client_id": str(client_entity.id),
                "issue_date": datetime.now(timezone.utc).isoformat(),
                "lines": [
                    {
                        "line_type": "text",
                        "description": "Service",
                        "quantity": 1,
                        "unit_price": 500.00,
                        "discount_percent": 0
                    }
                ]
            },
            headers=auth_headers
        )
        quote_id = response.json()["id"]

        # Move to accepted status: DRAFT -> NOT_SENT -> SENT -> ACCEPTED
        client.post(
            f"/api/v1/documents/{quote_id}/change-status",
            json={"new_status": "not_sent"},
            headers=auth_headers
        )
        client.post(
            f"/api/v1/documents/{quote_id}/change-status",
            json={"new_status": "sent"},
            headers=auth_headers
        )
        client.post(
            f"/api/v1/documents/{quote_id}/change-status",
            json={"new_status": "accepted"},
            headers=auth_headers
        )

        # Convert to invoice
        response = client.post(
            f"/api/v1/documents/{quote_id}/convert?target_type=invoice",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "invoice"
        assert data["code"].startswith("FAC-")
        assert float(data["subtotal"]) == 500.00
        assert data["parent_document_id"] == quote_id

    def test_cannot_convert_invoice(
        self, client: TestClient, auth_headers: dict,
        db: Session, test_company: Company
    ):
        """Test that invoices cannot be converted."""
        client_entity = Client(
            company_id=test_company.id,
            code="NOCONVCLI",
            name="No Conversion Client"
        )
        db.add(client_entity)
        db.commit()
        db.refresh(client_entity)

        # Create invoice (not quote)
        response = client.post(
            "/api/v1/documents",
            json={
                "type": "invoice",
                "client_id": str(client_entity.id),
                "issue_date": datetime.now(timezone.utc).isoformat(),
                "lines": [
                    {
                        "line_type": "text",
                        "description": "Service",
                        "quantity": 1,
                        "unit_price": 100.00,
                        "discount_percent": 0
                    }
                ]
            },
            headers=auth_headers
        )
        invoice_id = response.json()["id"]

        # Try to convert - should fail
        response = client.post(
            f"/api/v1/documents/{invoice_id}/convert?target_type=delivery_note",
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "presupuestos" in response.json()["detail"].lower()


class TestDocumentSummary:
    """Test document summary/stats endpoint."""

    def test_get_summary(
        self, client: TestClient, auth_headers: dict,
        db: Session, test_company: Company, test_user
    ):
        """Test getting document summary."""
        # Create some documents
        client_entity = Client(
            company_id=test_company.id,
            code="SUMCLI",
            name="Summary Client"
        )
        db.add(client_entity)
        db.commit()
        db.refresh(client_entity)

        # Create a draft invoice
        doc = Document(
            company_id=test_company.id,
            code="FAC-SUM-001",
            type=DocumentType.INVOICE,
            status=DocumentStatus.DRAFT,
            client_id=client_entity.id,
            issue_date=datetime.now(timezone.utc),
            subtotal=100.00,
            tax_amount=21.00,
            total=121.00,
            created_by=test_user.id
        )
        db.add(doc)
        db.commit()

        response = client.get(
            "/api/v1/documents/stats/summary",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "pending_documents" in data
        assert "pending_total" in data
        assert "month_invoices" in data
        assert "month_total" in data
