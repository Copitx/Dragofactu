"""
Tests for reminders CRUD endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timezone, timedelta

from app.models import Company
from app.models.reminder import Reminder


class TestRemindersEndpoints:
    """Test reminder CRUD operations."""

    def _reminder_data(self, title="Test Reminder"):
        return {
            "title": title,
            "description": "A test reminder description",
            "due_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "priority": "normal"
        }

    def test_create_reminder(self, client: TestClient, auth_headers: dict):
        """Test creating a new reminder."""
        data = self._reminder_data()

        response = client.post(
            "/api/v1/reminders",
            json=data,
            headers=auth_headers
        )

        assert response.status_code == 201
        result = response.json()
        assert result["title"] == "Test Reminder"
        assert result["priority"] == "normal"
        assert result["is_completed"] == False
        assert "id" in result

    def test_create_reminder_high_priority(self, client: TestClient, auth_headers: dict):
        """Test creating a high priority reminder."""
        data = self._reminder_data(title="Urgent Task")
        data["priority"] = "high"

        response = client.post(
            "/api/v1/reminders",
            json=data,
            headers=auth_headers
        )

        assert response.status_code == 201
        assert response.json()["priority"] == "high"

    def test_create_reminder_unauthorized(self, client: TestClient):
        """Test creating reminder without auth fails."""
        response = client.post(
            "/api/v1/reminders",
            json=self._reminder_data()
        )

        assert response.status_code == 401

    def test_list_reminders(
        self, client: TestClient, auth_headers: dict, db: Session,
        test_company: Company, test_user
    ):
        """Test listing reminders."""
        for i in range(3):
            db.add(Reminder(
                company_id=test_company.id,
                created_by=test_user.id,
                title=f"Reminder {i}",
                priority="normal"
            ))
        db.commit()

        response = client.get("/api/v1/reminders", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 3

    def test_list_reminders_filter_priority(
        self, client: TestClient, auth_headers: dict, db: Session,
        test_company: Company, test_user
    ):
        """Test filtering reminders by priority."""
        db.add(Reminder(
            company_id=test_company.id, created_by=test_user.id,
            title="High Priority", priority="high"
        ))
        db.add(Reminder(
            company_id=test_company.id, created_by=test_user.id,
            title="Low Priority", priority="low"
        ))
        db.commit()

        response = client.get(
            "/api/v1/reminders?priority=high",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "High Priority"

    def test_list_reminders_pending_only(
        self, client: TestClient, auth_headers: dict, db: Session,
        test_company: Company, test_user
    ):
        """Test filtering only pending (not completed) reminders."""
        db.add(Reminder(
            company_id=test_company.id, created_by=test_user.id,
            title="Pending", priority="normal", is_completed=False
        ))
        db.add(Reminder(
            company_id=test_company.id, created_by=test_user.id,
            title="Done", priority="normal", is_completed=True
        ))
        db.commit()

        # pending_only=true is the default
        response = client.get(
            "/api/v1/reminders?pending_only=true",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Pending"

    def test_get_reminder(
        self, client: TestClient, auth_headers: dict, db: Session,
        test_company: Company, test_user
    ):
        """Test getting a single reminder."""
        reminder = Reminder(
            company_id=test_company.id,
            created_by=test_user.id,
            title="Get Reminder",
            priority="normal"
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)

        response = client.get(
            f"/api/v1/reminders/{reminder.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Get Reminder"

    def test_get_reminder_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting nonexistent reminder."""
        fake_id = uuid.uuid4()
        response = client.get(
            f"/api/v1/reminders/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_reminder(
        self, client: TestClient, auth_headers: dict, db: Session,
        test_company: Company, test_user
    ):
        """Test updating a reminder."""
        reminder = Reminder(
            company_id=test_company.id,
            created_by=test_user.id,
            title="Old Title",
            priority="low"
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)

        response = client.put(
            f"/api/v1/reminders/{reminder.id}",
            json={"title": "New Title", "priority": "high"},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["priority"] == "high"

    def test_complete_reminder(
        self, client: TestClient, auth_headers: dict, db: Session,
        test_company: Company, test_user
    ):
        """Test marking a reminder as completed."""
        reminder = Reminder(
            company_id=test_company.id,
            created_by=test_user.id,
            title="Complete Me",
            priority="normal",
            is_completed=False
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)

        response = client.post(
            f"/api/v1/reminders/{reminder.id}/complete",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["is_completed"] == True

    def test_delete_reminder(
        self, client: TestClient, auth_headers: dict, db: Session,
        test_company: Company, test_user
    ):
        """Test deleting a reminder."""
        reminder = Reminder(
            company_id=test_company.id,
            created_by=test_user.id,
            title="Delete Me",
            priority="normal"
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)

        response = client.delete(
            f"/api/v1/reminders/{reminder.id}",
            headers=auth_headers
        )

        assert response.status_code == 200


class TestReminderMultiTenancy:
    """Test multi-tenancy isolation for reminders."""

    def test_cannot_see_other_company_reminders(
        self, client: TestClient, auth_headers: dict, db: Session, test_user
    ):
        """Test that reminders from other companies are not visible."""
        other_company = Company(code="OTHERREM", name="Other Reminder Co")
        db.add(other_company)
        db.commit()
        db.refresh(other_company)

        other_reminder = Reminder(
            company_id=other_company.id,
            created_by=test_user.id,
            title="Hidden Reminder",
            priority="normal"
        )
        db.add(other_reminder)
        db.commit()
        db.refresh(other_reminder)

        response = client.get(
            f"/api/v1/reminders/{other_reminder.id}",
            headers=auth_headers
        )

        assert response.status_code == 404
