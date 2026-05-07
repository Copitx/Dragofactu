"""
Tests for Supplier Catalog endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from app.models import Company, Supplier, Product


@pytest.fixture
def test_supplier(db: Session, test_company: Company) -> Supplier:
    supplier = Supplier(
        company_id=test_company.id,
        code="SUP-CAT-001",
        name="Proveedor Catálogo Test",
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@pytest.fixture
def test_product(db: Session, test_company: Company) -> Product:
    product = Product(
        company_id=test_company.id,
        code="PROD-CAT-001",
        name="Producto Catálogo Test",
        sale_price=25.0,
        purchase_price=10.0,
        current_stock=50,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


class TestSupplierCatalog:
    def test_list_catalog_empty(
        self, client: TestClient, auth_headers: dict, test_supplier: Supplier
    ):
        response = client.get(
            f"/api/v1/suppliers/{test_supplier.id}/catalog",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_add_product_to_catalog(
        self, client: TestClient, auth_headers: dict,
        test_supplier: Supplier, test_product: Product
    ):
        response = client.post(
            f"/api/v1/suppliers/{test_supplier.id}/catalog",
            json={
                "product_id": str(test_product.id),
                "supplier_ref": "REF-123",
                "purchase_price": 12.50,
                "lead_time_days": 3,
                "min_order_qty": 5.0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["supplier_ref"] == "REF-123"
        assert data["purchase_price"] == 12.50
        assert data["lead_time_days"] == 3

    def test_add_duplicate_raises_conflict(
        self, client: TestClient, auth_headers: dict,
        test_supplier: Supplier, test_product: Product
    ):
        payload = {
            "product_id": str(test_product.id),
            "supplier_ref": "REF-DUP",
            "purchase_price": 10.0,
        }
        r1 = client.post(
            f"/api/v1/suppliers/{test_supplier.id}/catalog",
            json=payload, headers=auth_headers,
        )
        assert r1.status_code == 201

        r2 = client.post(
            f"/api/v1/suppliers/{test_supplier.id}/catalog",
            json=payload, headers=auth_headers,
        )
        assert r2.status_code == 409

    def test_update_catalog_entry(
        self, client: TestClient, auth_headers: dict,
        test_supplier: Supplier, test_product: Product
    ):
        # Add entry
        r = client.post(
            f"/api/v1/suppliers/{test_supplier.id}/catalog",
            json={
                "product_id": str(test_product.id),
                "purchase_price": 10.0,
            },
            headers=auth_headers,
        )
        entry_id = r.json()["id"]

        # Update price
        response = client.put(
            f"/api/v1/suppliers/{test_supplier.id}/catalog/{entry_id}",
            json={"purchase_price": 15.0, "supplier_ref": "REF-UPD"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["purchase_price"] == 15.0
        assert data["supplier_ref"] == "REF-UPD"

    def test_remove_from_catalog(
        self, client: TestClient, auth_headers: dict,
        test_supplier: Supplier, test_product: Product
    ):
        # Add entry
        r = client.post(
            f"/api/v1/suppliers/{test_supplier.id}/catalog",
            json={"product_id": str(test_product.id), "purchase_price": 10.0},
            headers=auth_headers,
        )
        entry_id = r.json()["id"]

        response = client.delete(
            f"/api/v1/suppliers/{test_supplier.id}/catalog/{entry_id}",
            headers=auth_headers,
        )
        assert response.status_code in (200, 204)

        # Verify removed
        r2 = client.get(
            f"/api/v1/suppliers/{test_supplier.id}/catalog",
            headers=auth_headers,
        )
        assert r2.json() == []

    def test_catalog_search(
        self, client: TestClient, auth_headers: dict,
        test_supplier: Supplier, test_product: Product
    ):
        # Add to catalog first
        client.post(
            f"/api/v1/suppliers/{test_supplier.id}/catalog",
            json={"product_id": str(test_product.id), "purchase_price": 10.0},
            headers=auth_headers,
        )

        response = client.get("/api/v1/catalog/search", headers=auth_headers)
        assert response.status_code == 200
        items = response.json()
        assert len(items) >= 1
        assert "margin_pct" in items[0]

    def test_catalog_search_unknown_supplier(self, client: TestClient, auth_headers: dict):
        response = client.get(
            f"/api/v1/suppliers/{uuid.uuid4()}/catalog",
            headers=auth_headers,
        )
        assert response.status_code == 404
