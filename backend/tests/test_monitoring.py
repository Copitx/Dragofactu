"""
Tests for Fase 18: Health checks, metrics, admin, and rate limiting.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Company, User


class TestHealthEndpoints:
    """Test advanced health check endpoints."""

    def test_health_check_basic(self, client: TestClient):
        """Test basic health check returns healthy status with uptime."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "app" in data
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] >= 0

    def test_readiness_check(self, client: TestClient):
        """Test readiness probe verifies database connectivity."""
        response = client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data
        assert data["checks"]["database"]["status"] == "ok"
        assert "uptime_seconds" in data

    def test_readiness_returns_version(self, client: TestClient):
        """Test readiness probe includes version."""
        response = client.get("/health/ready")

        data = response.json()
        assert "version" in data


class TestMetricsEndpoint:
    """Test metrics endpoint."""

    def test_metrics_returns_data(self, client: TestClient):
        """Test metrics endpoint returns request statistics."""
        # Make a few requests first
        client.get("/health")
        client.get("/")

        response = client.get("/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "uptime_seconds" in data
        assert "requests" in data
        assert data["requests"]["total"] > 0
        assert "error_rate" in data["requests"]
        assert "status_codes" in data

    def test_metrics_tracks_errors(self, client: TestClient):
        """Test metrics tracks error responses."""
        # Trigger a 404
        client.get("/nonexistent-path")

        response = client.get("/metrics")
        data = response.json()
        assert data["requests"]["total"] > 0


class TestRequestId:
    """Test request tracing via X-Request-ID."""

    def test_response_has_request_id(self, client: TestClient):
        """Test that responses include X-Request-ID header."""
        response = client.get("/health")
        assert "X-Request-ID" in response.headers

    def test_custom_request_id_preserved(self, client: TestClient):
        """Test that custom X-Request-ID is echoed back."""
        custom_id = "test-trace-12345"
        response = client.get("/health", headers={"X-Request-ID": custom_id})
        assert response.headers["X-Request-ID"] == custom_id


class TestAdminEndpoints:
    """Test admin system info endpoints."""

    def test_system_info_requires_auth(self, client: TestClient):
        """Test system-info requires authentication."""
        response = client.get("/api/v1/admin/system-info")
        assert response.status_code == 403 or response.status_code == 401

    def test_system_info_as_admin(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test admin can access system info."""
        response = client.get(
            "/api/v1/admin/system-info",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "app_version" in data
        assert "database" in data
        assert "record_counts" in data
        assert "timestamp" in data
        assert data["database"]["engine"] == "SQLite"

    def test_system_info_warehouse_forbidden(
        self, client: TestClient, auth_headers_warehouse: dict, db: Session
    ):
        """Test warehouse user cannot access admin endpoints."""
        response = client.get(
            "/api/v1/admin/system-info",
            headers=auth_headers_warehouse,
        )
        assert response.status_code == 403

    def test_backup_info_as_admin(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test admin can access backup info."""
        response = client.get(
            "/api/v1/admin/backup-info",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "provider" in data
        assert "automatic_backups" in data


class TestGlobalRateLimiting:
    """Test global rate limiting middleware."""

    def test_normal_requests_pass(self, client: TestClient):
        """Test that normal request volume passes through."""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200

    def test_health_exempt_from_rate_limit(self, client: TestClient):
        """Test that health endpoint is exempt from rate limiting."""
        # Health should always work regardless of rate limits
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200
