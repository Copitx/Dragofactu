"""
Tests for clients CRUD endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from app.models import Client, Company, User
from tests.conftest import create_test_client_data


class TestClientsEndpoints:
    """Test client CRUD operations."""

    def test_create_client(self, client: TestClient, auth_headers: dict):
        """Test creating a new client."""
        client_data = create_test_client_data()

        response = client.post(
            "/api/v1/clients",
            json=client_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == client_data["code"]
        assert data["name"] == client_data["name"]
        assert data["tax_id"] == client_data["tax_id"]
        assert "id" in data

    def test_create_client_duplicate_code(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test creating client with duplicate code fails."""
        # Create first client
        existing_client = Client(
            company_id=test_company.id,
            code="DUP001",
            name="Existing Client"
        )
        db.add(existing_client)
        db.commit()

        # Try to create duplicate
        response = client.post(
            "/api/v1/clients",
            json={"code": "DUP001", "name": "Another Client"},
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "existe" in response.json()["detail"].lower()

    def test_create_client_unauthorized(self, client: TestClient):
        """Test creating client without auth fails."""
        response = client.post(
            "/api/v1/clients",
            json=create_test_client_data()
        )

        assert response.status_code == 401

    def test_list_clients(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test listing clients."""
        # Create some clients
        for i in range(3):
            db.add(Client(
                company_id=test_company.id,
                code=f"LIST{i:03d}",
                name=f"List Client {i}"
            ))
        db.commit()

        response = client.get("/api/v1/clients", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 3

    def test_list_clients_pagination(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test client list pagination."""
        # Create 10 clients
        for i in range(10):
            db.add(Client(
                company_id=test_company.id,
                code=f"PAGE{i:03d}",
                name=f"Page Client {i}"
            ))
        db.commit()

        # Get first page
        response = client.get(
            "/api/v1/clients?skip=0&limit=5",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["total"] == 10

    def test_list_clients_search(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test client search."""
        db.add(Client(company_id=test_company.id, code="FIND001", name="Empresa Buscable"))
        db.add(Client(company_id=test_company.id, code="OTHER001", name="Otra Empresa"))
        db.commit()

        response = client.get(
            "/api/v1/clients?search=Buscable",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Empresa Buscable"

    def test_get_client(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test getting a single client."""
        test_client = Client(
            company_id=test_company.id,
            code="GET001",
            name="Get Client"
        )
        db.add(test_client)
        db.commit()
        db.refresh(test_client)

        response = client.get(
            f"/api/v1/clients/{test_client.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "GET001"
        assert data["name"] == "Get Client"

    def test_get_client_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting nonexistent client."""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/v1/clients/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_client(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test updating a client."""
        test_client = Client(
            company_id=test_company.id,
            code="UPD001",
            name="Update Client"
        )
        db.add(test_client)
        db.commit()
        db.refresh(test_client)

        response = client.put(
            f"/api/v1/clients/{test_client.id}",
            json={"name": "Updated Name", "city": "Valencia"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["city"] == "Valencia"
        assert data["code"] == "UPD001"  # Code unchanged

    def test_delete_client(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test soft deleting a client."""
        test_client = Client(
            company_id=test_company.id,
            code="DEL001",
            name="Delete Client"
        )
        db.add(test_client)
        db.commit()
        db.refresh(test_client)

        response = client.delete(
            f"/api/v1/clients/{test_client.id}",
            headers=auth_headers
        )

        assert response.status_code == 200

        # Verify soft delete
        db.refresh(test_client)
        assert test_client.is_active == False


class TestClientMultiTenancy:
    """Test multi-tenancy isolation for clients."""

    def test_cannot_see_other_company_clients(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that clients from other companies are not visible."""
        # Create another company and client
        other_company = Company(
            code="OTHER",
            name="Other Company"
        )
        db.add(other_company)
        db.commit()
        db.refresh(other_company)

        other_client = Client(
            company_id=other_company.id,
            code="HIDDEN001",
            name="Hidden Client"
        )
        db.add(other_client)
        db.commit()
        db.refresh(other_client)

        # Try to access from test user's company
        response = client.get(
            f"/api/v1/clients/{other_client.id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_list_only_shows_own_company(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test listing only shows own company's clients."""
        # Create client for test company
        own_client = Client(
            company_id=test_company.id,
            code="OWN001",
            name="Own Client"
        )
        db.add(own_client)

        # Create another company and client
        other_company = Company(code="OTHER2", name="Other Company 2")
        db.add(other_company)
        db.commit()
        db.refresh(other_company)

        other_client = Client(
            company_id=other_company.id,
            code="FOREIGN001",
            name="Foreign Client"
        )
        db.add(other_client)
        db.commit()

        # List clients
        response = client.get("/api/v1/clients", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        # Should only see own client
        assert data["total"] == 1
        assert data["items"][0]["code"] == "OWN001"
