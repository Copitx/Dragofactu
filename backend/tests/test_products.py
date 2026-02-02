"""
Tests for products CRUD endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from app.models import Product, Company, User
from tests.conftest import create_test_product_data


class TestProductsEndpoints:
    """Test product CRUD operations."""

    def test_create_product(self, client: TestClient, auth_headers: dict):
        """Test creating a new product."""
        product_data = create_test_product_data()

        response = client.post(
            "/api/v1/products",
            json=product_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == product_data["code"]
        assert data["name"] == product_data["name"]
        assert float(data["sale_price"]) == product_data["sale_price"]
        assert data["current_stock"] == product_data["current_stock"]

    def test_create_product_duplicate_code(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test creating product with duplicate code fails."""
        existing = Product(
            company_id=test_company.id,
            code="DUPPROD",
            name="Existing Product",
            sale_price=10.00
        )
        db.add(existing)
        db.commit()

        response = client.post(
            "/api/v1/products",
            json={"code": "DUPPROD", "name": "Another Product", "sale_price": 20.00},
            headers=auth_headers
        )

        assert response.status_code == 400

    def test_list_products(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test listing products."""
        for i in range(5):
            db.add(Product(
                company_id=test_company.id,
                code=f"LISTPROD{i:03d}",
                name=f"List Product {i}",
                sale_price=10.00 + i
            ))
        db.commit()

        response = client.get("/api/v1/products", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["total"] == 5

    def test_list_products_by_category(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test filtering products by category."""
        db.add(Product(
            company_id=test_company.id,
            code="CAT001",
            name="Product Cat A",
            category="Categoria A",
            sale_price=10.00
        ))
        db.add(Product(
            company_id=test_company.id,
            code="CAT002",
            name="Product Cat B",
            category="Categoria B",
            sale_price=20.00
        ))
        db.commit()

        response = client.get(
            "/api/v1/products?category=Categoria A",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["category"] == "Categoria A"

    def test_list_low_stock_products(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test filtering low stock products."""
        db.add(Product(
            company_id=test_company.id,
            code="LOWSTOCK",
            name="Low Stock Product",
            sale_price=10.00,
            current_stock=5,
            minimum_stock=10
        ))
        db.add(Product(
            company_id=test_company.id,
            code="OKSTOCK",
            name="OK Stock Product",
            sale_price=20.00,
            current_stock=100,
            minimum_stock=10
        ))
        db.commit()

        response = client.get(
            "/api/v1/products?low_stock=true",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["code"] == "LOWSTOCK"

    def test_get_product(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test getting a single product."""
        product = Product(
            company_id=test_company.id,
            code="GETPROD",
            name="Get Product",
            sale_price=50.00
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        response = client.get(
            f"/api/v1/products/{product.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "GETPROD"

    def test_update_product(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test updating a product."""
        product = Product(
            company_id=test_company.id,
            code="UPDPROD",
            name="Update Product",
            sale_price=30.00
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        response = client.put(
            f"/api/v1/products/{product.id}",
            json={"name": "Updated Product", "sale_price": 45.00},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Product"
        assert float(data["sale_price"]) == 45.00

    def test_delete_product(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test soft deleting a product."""
        product = Product(
            company_id=test_company.id,
            code="DELPROD",
            name="Delete Product",
            sale_price=10.00
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        response = client.delete(
            f"/api/v1/products/{product.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        db.refresh(product)
        assert product.is_active == False


class TestStockAdjustment:
    """Test stock adjustment functionality."""

    def test_adjust_stock_positive(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test adding stock."""
        product = Product(
            company_id=test_company.id,
            code="STOCKADD",
            name="Stock Add Product",
            sale_price=10.00,
            current_stock=50
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        response = client.post(
            f"/api/v1/products/{product.id}/adjust-stock",
            json={"product_id": str(product.id), "quantity": 25, "reason": "Reposicion"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["current_stock"] == 75

    def test_adjust_stock_negative(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test removing stock."""
        product = Product(
            company_id=test_company.id,
            code="STOCKSUB",
            name="Stock Sub Product",
            sale_price=10.00,
            current_stock=50
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        response = client.post(
            f"/api/v1/products/{product.id}/adjust-stock",
            json={"product_id": str(product.id), "quantity": -20, "reason": "Ajuste inventario"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["current_stock"] == 30

    def test_adjust_stock_negative_below_zero(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test cannot reduce stock below zero."""
        product = Product(
            company_id=test_company.id,
            code="STOCKNEG",
            name="Stock Negative Product",
            sale_price=10.00,
            current_stock=10
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        response = client.post(
            f"/api/v1/products/{product.id}/adjust-stock",
            json={"product_id": str(product.id), "quantity": -50, "reason": "Too much"},
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "insuficiente" in response.json()["detail"].lower()
