"""
Tests for Export/Import CSV endpoints (Fase 16.1).
"""
import io
import csv
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Client, Product, Supplier, Company, User, UserRole
from app.core.security import hash_password, create_access_token


class TestExportEndpoints:
    """Test CSV export functionality."""

    def test_export_clients_empty(self, client: TestClient, auth_headers):
        """Export when no clients exist returns just headers."""
        response = client.get("/api/v1/export/clients", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

        reader = csv.reader(io.StringIO(response.text))
        rows = list(reader)
        assert len(rows) == 1  # Just headers
        assert rows[0][0] == "code"

    def test_export_clients_with_data(self, client: TestClient, auth_headers, db, test_company):
        """Export clients with data returns correct CSV."""
        # Create test clients
        for i in range(3):
            c = Client(
                company_id=test_company.id,
                code=f"CLI00{i+1}",
                name=f"Client {i+1}",
                email=f"client{i+1}@test.com"
            )
            db.add(c)
        db.commit()

        response = client.get("/api/v1/export/clients", headers=auth_headers)
        assert response.status_code == 200

        reader = csv.reader(io.StringIO(response.text))
        rows = list(reader)
        assert len(rows) == 4  # Header + 3 clients
        assert rows[1][0] == "CLI001"  # First client code
        assert rows[1][1] == "Client 1"

    def test_export_clients_unauthorized(self, client: TestClient):
        """Export without auth returns 401."""
        response = client.get("/api/v1/export/clients")
        assert response.status_code == 401

    def test_export_products_with_data(self, client: TestClient, auth_headers, db, test_company):
        """Export products returns correct CSV."""
        p = Product(
            company_id=test_company.id,
            code="PROD001",
            name="Widget",
            sale_price=19.99,
            current_stock=50,
        )
        db.add(p)
        db.commit()

        response = client.get("/api/v1/export/products", headers=auth_headers)
        assert response.status_code == 200

        reader = csv.reader(io.StringIO(response.text))
        rows = list(reader)
        assert len(rows) == 2
        assert rows[1][0] == "PROD001"
        assert rows[1][1] == "Widget"

    def test_export_suppliers_with_data(self, client: TestClient, auth_headers, db, test_company):
        """Export suppliers returns correct CSV."""
        s = Supplier(
            company_id=test_company.id,
            code="SUP001",
            name="Supplier One",
            phone="+34 999 111 222"
        )
        db.add(s)
        db.commit()

        response = client.get("/api/v1/export/suppliers", headers=auth_headers)
        assert response.status_code == 200

        reader = csv.reader(io.StringIO(response.text))
        rows = list(reader)
        assert len(rows) == 2
        assert rows[1][0] == "SUP001"

    def test_export_only_own_company(self, client: TestClient, auth_headers, db, test_company):
        """Export only returns data from the authenticated user's company."""
        # Create client in test company
        c1 = Client(company_id=test_company.id, code="OWN001", name="Own Client")
        db.add(c1)

        # Create another company and its client
        other_company = Company(code="OTHER01", name="Other Co", is_active=True)
        db.add(other_company)
        db.commit()
        db.refresh(other_company)

        c2 = Client(company_id=other_company.id, code="ALIEN01", name="Alien Client")
        db.add(c2)
        db.commit()

        response = client.get("/api/v1/export/clients", headers=auth_headers)
        reader = csv.reader(io.StringIO(response.text))
        rows = list(reader)
        # Should only have 1 client (OWN001), not ALIEN01
        assert len(rows) == 2
        assert rows[1][0] == "OWN001"


class TestImportEndpoints:
    """Test CSV import functionality."""

    def test_import_clients_success(self, client: TestClient, auth_headers):
        """Import valid CSV creates clients."""
        csv_content = "code,name,tax_id,email\nIMP001,Imported Client,A11111111,imp@test.com\nIMP002,Second Client,,second@test.com"
        file = io.BytesIO(csv_content.encode("utf-8"))

        response = client.post(
            "/api/v1/export/import/clients",
            headers=auth_headers,
            files={"file": ("clients.csv", file, "text/csv")}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Importados: 2" in data["message"]

    def test_import_clients_skips_duplicates(self, client: TestClient, auth_headers, db, test_company):
        """Import skips clients with existing codes."""
        # Pre-create a client
        c = Client(company_id=test_company.id, code="DUP001", name="Existing")
        db.add(c)
        db.commit()

        csv_content = "code,name\nDUP001,Duplicate\nNEW001,New Client"
        file = io.BytesIO(csv_content.encode("utf-8"))

        response = client.post(
            "/api/v1/export/import/clients",
            headers=auth_headers,
            files={"file": ("clients.csv", file, "text/csv")}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Importados: 1" in data["message"]
        assert "Omitidos (duplicados): 1" in data["message"]

    def test_import_clients_invalid_file(self, client: TestClient, auth_headers):
        """Import rejects non-CSV files."""
        file = io.BytesIO(b"not a csv")

        response = client.post(
            "/api/v1/export/import/clients",
            headers=auth_headers,
            files={"file": ("data.txt", file, "text/plain")}
        )
        assert response.status_code == 400

    def test_import_products_success(self, client: TestClient, auth_headers):
        """Import valid products CSV."""
        csv_content = "code,name,sale_price,current_stock\nIMPROD1,Imported Product,29.99,100\nIMPROD2,Second Product,15.00,50"
        file = io.BytesIO(csv_content.encode("utf-8"))

        response = client.post(
            "/api/v1/export/import/products",
            headers=auth_headers,
            files={"file": ("products.csv", file, "text/csv")}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Importados: 2" in data["message"]

    def test_import_products_invalid_file(self, client: TestClient, auth_headers):
        """Import rejects non-CSV files for products."""
        file = io.BytesIO(b"not a csv")

        response = client.post(
            "/api/v1/export/import/products",
            headers=auth_headers,
            files={"file": ("data.json", file, "application/json")}
        )
        assert response.status_code == 400

    def test_import_clients_missing_required_fields(self, client: TestClient, auth_headers):
        """Import handles rows with missing required fields."""
        csv_content = "code,name\n,Missing Code\nGOOD01,Good Client"
        file = io.BytesIO(csv_content.encode("utf-8"))

        response = client.post(
            "/api/v1/export/import/clients",
            headers=auth_headers,
            files={"file": ("clients.csv", file, "text/csv")}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Importados: 1" in data["message"]
        assert "Errores: 1" in data["message"]
