"""
Tests for workers CRUD endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from app.models import Company
from app.models.worker import Worker


class TestWorkersEndpoints:
    """Test worker CRUD operations."""

    def _worker_data(self, code="WRK001"):
        return {
            "code": code,
            "first_name": "Juan",
            "last_name": "Garcia",
            "phone": "+34 600 111 222",
            "email": "juan@test.com",
            "position": "Developer",
            "department": "Engineering",
            "salary": 35000.00
        }

    def test_create_worker(self, client: TestClient, auth_headers: dict):
        """Test creating a new worker."""
        data = self._worker_data()

        response = client.post(
            "/api/v1/workers",
            json=data,
            headers=auth_headers
        )

        assert response.status_code == 201
        result = response.json()
        assert result["code"] == "WRK001"
        assert result["first_name"] == "Juan"
        assert result["last_name"] == "Garcia"
        assert result["department"] == "Engineering"
        assert "id" in result

    def test_create_worker_duplicate_code(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test creating worker with duplicate code fails."""
        existing = Worker(
            company_id=test_company.id,
            code="DUPWRK",
            first_name="Existing",
            last_name="Worker"
        )
        db.add(existing)
        db.commit()

        response = client.post(
            "/api/v1/workers",
            json=self._worker_data(code="DUPWRK"),
            headers=auth_headers
        )

        assert response.status_code == 400

    def test_create_worker_unauthorized(self, client: TestClient):
        """Test creating worker without auth fails."""
        response = client.post(
            "/api/v1/workers",
            json=self._worker_data()
        )

        assert response.status_code == 401

    def test_list_workers(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test listing workers."""
        for i in range(4):
            db.add(Worker(
                company_id=test_company.id,
                code=f"LSTWRK{i:03d}",
                first_name=f"Worker{i}",
                last_name="Test"
            ))
        db.commit()

        response = client.get("/api/v1/workers", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 4

    def test_list_workers_filter_department(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test filtering workers by department."""
        db.add(Worker(
            company_id=test_company.id, code="ENG001",
            first_name="Ana", last_name="Dev", department="Engineering"
        ))
        db.add(Worker(
            company_id=test_company.id, code="HR001",
            first_name="Luis", last_name="HR", department="HR"
        ))
        db.commit()

        response = client.get(
            "/api/v1/workers?department=Engineering",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["code"] == "ENG001"

    def test_list_workers_search(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test worker search by name."""
        db.add(Worker(
            company_id=test_company.id, code="SRCH001",
            first_name="Maria", last_name="Gonzalez"
        ))
        db.add(Worker(
            company_id=test_company.id, code="SRCH002",
            first_name="Pedro", last_name="Lopez"
        ))
        db.commit()

        response = client.get(
            "/api/v1/workers?search=Maria",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["first_name"] == "Maria"

    def test_get_worker(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test getting a single worker."""
        worker = Worker(
            company_id=test_company.id,
            code="GETWRK",
            first_name="Get",
            last_name="Worker"
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)

        response = client.get(
            f"/api/v1/workers/{worker.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "GETWRK"
        assert data["first_name"] == "Get"

    def test_get_worker_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting nonexistent worker."""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/v1/workers/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_worker(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test updating a worker."""
        worker = Worker(
            company_id=test_company.id,
            code="UPDWRK",
            first_name="Old",
            last_name="Name"
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)

        response = client.put(
            f"/api/v1/workers/{worker.id}",
            json={"first_name": "New", "department": "Sales"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "New"
        assert data["department"] == "Sales"
        assert data["code"] == "UPDWRK"

    def test_delete_worker(
        self, client: TestClient, auth_headers: dict, db: Session, test_company: Company
    ):
        """Test soft deleting a worker."""
        worker = Worker(
            company_id=test_company.id,
            code="DELWRK",
            first_name="Delete",
            last_name="Worker"
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)

        response = client.delete(
            f"/api/v1/workers/{worker.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        db.refresh(worker)
        assert worker.is_active == False


class TestWorkerCourses:
    """Test worker courses management."""

    @pytest.fixture
    def test_worker(self, db: Session, test_company: Company) -> Worker:
        worker = Worker(
            company_id=test_company.id,
            code="COURSEWRK",
            first_name="Course",
            last_name="Worker"
        )
        db.add(worker)
        db.commit()
        db.refresh(worker)
        return worker

    def test_add_course(
        self, client: TestClient, auth_headers: dict, test_worker: Worker
    ):
        """Test adding a course to a worker."""
        response = client.post(
            f"/api/v1/workers/{test_worker.id}/courses",
            json={
                "name": "Safety Training",
                "provider": "SafetyPro",
                "issue_date": "2026-01-15T00:00:00Z"
            },
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Safety Training"
        assert data["provider"] == "SafetyPro"

    def test_delete_course(
        self, client: TestClient, auth_headers: dict, test_worker: Worker
    ):
        """Test deleting a course from a worker."""
        # First add a course
        resp = client.post(
            f"/api/v1/workers/{test_worker.id}/courses",
            json={"name": "Temp Course"},
            headers=auth_headers
        )
        course_id = resp.json()["id"]

        # Delete it
        response = client.delete(
            f"/api/v1/workers/{test_worker.id}/courses/{course_id}",
            headers=auth_headers
        )

        assert response.status_code == 200


class TestWorkerMultiTenancy:
    """Test multi-tenancy isolation for workers."""

    def test_cannot_see_other_company_workers(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test that workers from other companies are not visible."""
        other_company = Company(code="OTHERWRK", name="Other Worker Co")
        db.add(other_company)
        db.commit()
        db.refresh(other_company)

        other_worker = Worker(
            company_id=other_company.id,
            code="HIDDEN",
            first_name="Hidden",
            last_name="Worker"
        )
        db.add(other_worker)
        db.commit()
        db.refresh(other_worker)

        response = client.get(
            f"/api/v1/workers/{other_worker.id}",
            headers=auth_headers
        )

        assert response.status_code == 404
