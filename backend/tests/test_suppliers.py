"""
Tests for suppliers CRUD endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from app.models import Company
from app.models.supplier import Supplier
from tests.conftest import create_test_supplier_data


class TestSuppliersEndpoints:
    """Test supplier CRUD operations."""

    def test_create_supplier(self, client: TestClient, auth_headers: dict):
        """Test creating a new supplier."""
        supplier_data = create_test_supplier_data()

        response = client.post(
            "/api/v1/suppliers",
            json=supplier_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == supplier_data["code"]
        assert data["name"] == supplier_data["name"]
        assert data["tax_id"] == supplier_data["tax_id"]
        assert "id" in data

    def test_create_supplier_duplicate_code(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test creating supplier with duplicate code fails."""
        existing = Supplier(
            company_id=test_company.id,
            code="DUPSUP",
            name="Existing Supplier"
        )
        db.add(existing)
        db.commit()

        response = client.post(
            "/api/v1/suppliers",
            json={"code": "DUPSUP", "name": "Another Supplier"},
            headers=auth_headers
        )

        assert response.status_code == 400

    def test_create_supplier_unauthorized(self, client: TestClient):
        """Test creating supplier without auth fails."""
        response = client.post(
            "/api/v1/suppliers",
            json=create_test_supplier_data()
        )

        assert response.status_code == 401

    def test_list_suppliers(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test listing suppliers."""
        for i in range(3):
            db.add(Supplier(
                company_id=test_company.id,
                code=f"LISTSUP{i:03d}",
                name=f"List Supplier {i}"
            ))
        db.commit()

        response = client.get("/api/v1/suppliers", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 3

    def test_list_suppliers_pagination(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test supplier list pagination."""
        for i in range(10):
            db.add(Supplier(
                company_id=test_company.id,
                code=f"PAGESUP{i:03d}",
                name=f"Page Supplier {i}"
            ))
        db.commit()

        response = client.get(
            "/api/v1/suppliers?skip=0&limit=5",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["total"] == 10

    def test_list_suppliers_search(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test supplier search."""
        db.add(Supplier(company_id=test_company.id, code="FIND001", name="Proveedor Buscable"))
        db.add(Supplier(company_id=test_company.id, code="OTHER001", name="Otro Proveedor"))
        db.commit()

        response = client.get(
            "/api/v1/suppliers?search=Buscable",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Proveedor Buscable"

    def test_get_supplier(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test getting a single supplier."""
        supplier = Supplier(
            company_id=test_company.id,
            code="GETSUP001",
            name="Get Supplier"
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)

        response = client.get(
            f"/api/v1/suppliers/{supplier.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "GETSUP001"
        assert data["name"] == "Get Supplier"

    def test_get_supplier_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting nonexistent supplier."""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/v1/suppliers/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_supplier(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test updating a supplier."""
        supplier = Supplier(
            company_id=test_company.id,
            code="UPDSUP001",
            name="Update Supplier"
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)

        response = client.put(
            f"/api/v1/suppliers/{supplier.id}",
            json={"name": "Updated Supplier", "city": "Sevilla"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Supplier"
        assert data["city"] == "Sevilla"
        assert data["code"] == "UPDSUP001"

    def test_delete_supplier(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test soft deleting a supplier."""
        supplier = Supplier(
            company_id=test_company.id,
            code="DELSUP001",
            name="Delete Supplier"
        )
        db.add(supplier)
        db.commit()
        db.refresh(supplier)

        response = client.delete(
            f"/api/v1/suppliers/{supplier.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        db.refresh(supplier)
        assert supplier.is_active == False


class TestSupplierMultiTenancy:
    """Test multi-tenancy isolation for suppliers."""

    def test_cannot_see_other_company_suppliers(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that suppliers from other companies are not visible."""
        other_company = Company(code="OTHERSUP", name="Other Company Sup")
        db.add(other_company)
        db.commit()
        db.refresh(other_company)

        other_supplier = Supplier(
            company_id=other_company.id,
            code="HIDDEN001",
            name="Hidden Supplier"
        )
        db.add(other_supplier)
        db.commit()
        db.refresh(other_supplier)

        response = client.get(
            f"/api/v1/suppliers/{other_supplier.id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_list_only_shows_own_company(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test listing only shows own company's suppliers."""
        own = Supplier(company_id=test_company.id, code="OWN001", name="Own Supplier")
        db.add(own)

        other_company = Company(code="OTHERSUP2", name="Other Sup Company 2")
        db.add(other_company)
        db.commit()
        db.refresh(other_company)

        foreign = Supplier(company_id=other_company.id, code="FOREIGN001", name="Foreign Supplier")
        db.add(foreign)
        db.commit()

        response = client.get("/api/v1/suppliers", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["code"] == "OWN001"
