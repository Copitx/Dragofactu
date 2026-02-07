"""
Tests for diary entries CRUD endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timezone

from app.models import Company
from app.models.diary import DiaryEntry


class TestDiaryEndpoints:
    """Test diary entry CRUD operations."""

    def _diary_data(self):
        return {
            "title": "Nota de prueba",
            "content": "Contenido de la nota de prueba",
            "entry_date": datetime.now(timezone.utc).isoformat(),
            "is_pinned": False
        }

    def test_create_diary_entry(self, client: TestClient, auth_headers: dict):
        """Test creating a new diary entry."""
        data = self._diary_data()

        response = client.post(
            "/api/v1/diary",
            json=data,
            headers=auth_headers
        )

        assert response.status_code == 201
        result = response.json()
        assert result["title"] == "Nota de prueba"
        assert result["content"] == "Contenido de la nota de prueba"
        assert "id" in result

    def test_create_diary_entry_unauthorized(self, client: TestClient):
        """Test creating diary entry without auth fails."""
        response = client.post(
            "/api/v1/diary",
            json=self._diary_data()
        )

        assert response.status_code == 401

    def test_create_diary_entry_pinned(self, client: TestClient, auth_headers: dict):
        """Test creating a pinned diary entry."""
        data = self._diary_data()
        data["is_pinned"] = True

        response = client.post(
            "/api/v1/diary",
            json=data,
            headers=auth_headers
        )

        assert response.status_code == 201
        assert response.json()["is_pinned"] == True

    def test_list_diary_entries(
        self, client: TestClient, auth_headers: dict, db: Session,
        test_company: Company, test_user
    ):
        """Test listing diary entries."""
        for i in range(3):
            db.add(DiaryEntry(
                company_id=test_company.id,
                user_id=test_user.id,
                title=f"Entry {i}",
                content=f"Content {i}",
                entry_date=datetime.now(timezone.utc)
            ))
        db.commit()

        response = client.get("/api/v1/diary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 3

    def test_list_diary_pinned_only(
        self, client: TestClient, auth_headers: dict, db: Session,
        test_company: Company, test_user
    ):
        """Test filtering pinned diary entries."""
        db.add(DiaryEntry(
            company_id=test_company.id, user_id=test_user.id,
            title="Pinned", content="Pinned content",
            entry_date=datetime.now(timezone.utc), is_pinned=True
        ))
        db.add(DiaryEntry(
            company_id=test_company.id, user_id=test_user.id,
            title="Normal", content="Normal content",
            entry_date=datetime.now(timezone.utc), is_pinned=False
        ))
        db.commit()

        response = client.get(
            "/api/v1/diary?pinned_only=true",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Pinned"

    def test_get_diary_entry(
        self, client: TestClient, auth_headers: dict, db: Session,
        test_company: Company, test_user
    ):
        """Test getting a single diary entry."""
        entry = DiaryEntry(
            company_id=test_company.id,
            user_id=test_user.id,
            title="Get Entry",
            content="Get entry content",
            entry_date=datetime.now(timezone.utc)
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)

        response = client.get(
            f"/api/v1/diary/{entry.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Get Entry"

    def test_get_diary_entry_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting nonexistent diary entry."""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/v1/diary/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_diary_entry(
        self, client: TestClient, auth_headers: dict, db: Session,
        test_company: Company, test_user
    ):
        """Test updating a diary entry."""
        entry = DiaryEntry(
            company_id=test_company.id,
            user_id=test_user.id,
            title="Old Title",
            content="Old content",
            entry_date=datetime.now(timezone.utc)
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)

        response = client.put(
            f"/api/v1/diary/{entry.id}",
            json={"title": "New Title", "content": "New content"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["content"] == "New content"

    def test_delete_diary_entry(
        self, client: TestClient, auth_headers: dict, db: Session,
        test_company: Company, test_user
    ):
        """Test deleting a diary entry."""
        entry = DiaryEntry(
            company_id=test_company.id,
            user_id=test_user.id,
            title="Delete Me",
            content="Delete content",
            entry_date=datetime.now(timezone.utc)
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)

        response = client.delete(
            f"/api/v1/diary/{entry.id}",
            headers=auth_headers
        )

        assert response.status_code == 200


class TestDiaryMultiTenancy:
    """Test multi-tenancy isolation for diary entries."""

    def test_cannot_see_other_company_entries(
        self, client: TestClient, auth_headers: dict, db: Session, test_user
    ):
        """Test that diary entries from other companies are not visible."""
        other_company = Company(code="OTHERDIARY", name="Other Diary Co")
        db.add(other_company)
        db.commit()
        db.refresh(other_company)

        other_entry = DiaryEntry(
            company_id=other_company.id,
            user_id=test_user.id,
            title="Hidden Entry",
            content="Hidden",
            entry_date=datetime.now(timezone.utc)
        )
        db.add(other_entry)
        db.commit()
        db.refresh(other_entry)

        response = client.get(
            f"/api/v1/diary/{other_entry.id}",
            headers=auth_headers
        )

        assert response.status_code == 404
