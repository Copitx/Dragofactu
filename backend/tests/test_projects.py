"""
Tests for Projects/Obras endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date
import uuid

from app.models import Client, Company, User
from app.models.project import Project, ProjectStatus, ProjectExpense, ExpenseCategory


@pytest.fixture
def test_client_entity(db: Session, test_company: Company) -> Client:
    client = Client(
        company_id=test_company.id,
        code="PROJCLI001",
        name="Project Test Client"
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@pytest.fixture
def test_project(db: Session, test_company: Company, test_client_entity: Client, test_user: User) -> Project:
    project = Project(
        company_id=test_company.id,
        code="Obra-2026-001",
        name="Piscina García",
        client_id=test_client_entity.id,
        address="Calle Test 1, Madrid",
        status=ProjectStatus.ACTIVE,
        start_date=date(2026, 1, 1),
        estimated_value=50000.0,
        notes="Obra de prueba",
        is_active=True,
        created_by=test_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


class TestProjectCRUD:
    def test_list_projects_empty(self, client: TestClient, auth_headers: dict):
        response = client.get("/api/v1/projects", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_create_project(
        self, client: TestClient, auth_headers: dict, test_client_entity: Client
    ):
        response = client.post(
            "/api/v1/projects",
            json={
                "name": "Piscina Hernández",
                "client_id": str(test_client_entity.id),
                "address": "Calle Mayor 5",
                "estimated_value": 30000.0,
                "notes": "Obra nueva",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Piscina Hernández"
        assert data["status"] == "active"
        assert data["code"].startswith("Obra-")
        assert data["estimated_value"] == 30000.0

    def test_create_project_without_client(self, client: TestClient, auth_headers: dict):
        response = client.post(
            "/api/v1/projects",
            json={"name": "Obra sin cliente", "estimated_value": 10000.0},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["client_id"] is None

    def test_get_project(
        self, client: TestClient, auth_headers: dict, test_project: Project
    ):
        response = client.get(f"/api/v1/projects/{test_project.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_project.id)
        assert data["name"] == "Piscina García"
        assert "expenses" in data
        assert "documents" in data

    def test_get_project_not_found(self, client: TestClient, auth_headers: dict):
        response = client.get(f"/api/v1/projects/{uuid.uuid4()}", headers=auth_headers)
        assert response.status_code == 404

    def test_update_project(
        self, client: TestClient, auth_headers: dict, test_project: Project
    ):
        response = client.put(
            f"/api/v1/projects/{test_project.id}",
            json={"status": "paused", "notes": "Actualizada"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "paused"
        assert data["notes"] == "Actualizada"

    def test_list_projects_with_filter(
        self, client: TestClient, auth_headers: dict, test_project: Project
    ):
        response = client.get(
            "/api/v1/projects?status=active", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_list_projects_search(
        self, client: TestClient, auth_headers: dict, test_project: Project
    ):
        response = client.get(
            "/api/v1/projects?search=García", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert any(p["name"] == "Piscina García" for p in data["items"])

    def test_delete_project(
        self, client: TestClient, auth_headers: dict, test_project: Project
    ):
        response = client.delete(
            f"/api/v1/projects/{test_project.id}", headers=auth_headers
        )
        assert response.status_code == 204
        # Verify soft delete
        response2 = client.get(f"/api/v1/projects/{test_project.id}", headers=auth_headers)
        assert response2.status_code == 404


class TestProjectExpenses:
    def test_add_expense(
        self, client: TestClient, auth_headers: dict, test_project: Project
    ):
        response = client.post(
            f"/api/v1/projects/{test_project.id}/expenses",
            json={
                "date": "2026-03-15",
                "description": "Cemento Holcim 50 sacos",
                "supplier": "Leroy Merlin",
                "document_ref": "ALB-2026-001",
                "amount": 450.0,
                "category": "material",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Cemento Holcim 50 sacos"
        assert data["amount"] == 450.0
        assert data["category"] == "material"

    def test_delete_expense(
        self, client: TestClient, auth_headers: dict,
        test_project: Project, db: Session, test_company: Company
    ):
        expense = ProjectExpense(
            project_id=test_project.id,
            company_id=test_company.id,
            date=date(2026, 3, 1),
            description="Ferralla",
            amount=1200.0,
            category=ExpenseCategory.MATERIAL,
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)

        response = client.delete(
            f"/api/v1/projects/{test_project.id}/expenses/{expense.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    def test_expense_not_found(self, client: TestClient, auth_headers: dict, test_project: Project):
        response = client.delete(
            f"/api/v1/projects/{test_project.id}/expenses/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestProjectSummary:
    def test_summary_no_expenses(
        self, client: TestClient, auth_headers: dict, test_project: Project
    ):
        response = client.get(
            f"/api/v1/projects/{test_project.id}/summary", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["estimated_value"] == 50000.0
        assert data["total_expenses"] == 0.0
        assert data["total_invoiced"] == 0.0
        assert data["margin"] == 50000.0

    def test_summary_with_expenses(
        self, client: TestClient, auth_headers: dict,
        test_project: Project, db: Session, test_company: Company
    ):
        expense = ProjectExpense(
            project_id=test_project.id,
            company_id=test_company.id,
            date=date(2026, 3, 1),
            description="Materiales",
            amount=15000.0,
            category=ExpenseCategory.MATERIAL,
        )
        db.add(expense)
        db.commit()

        response = client.get(
            f"/api/v1/projects/{test_project.id}/summary", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_expenses"] == 15000.0
        assert data["margin"] == 35000.0
        assert data["margin_pct"] == pytest.approx(70.0, rel=0.01)


class TestProjectCodeAutoGeneration:
    def test_code_auto_increments(
        self, client: TestClient, auth_headers: dict
    ):
        r1 = client.post("/api/v1/projects", json={"name": "Obra 1"}, headers=auth_headers)
        r2 = client.post("/api/v1/projects", json={"name": "Obra 2"}, headers=auth_headers)
        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.json()["code"] != r2.json()["code"]
