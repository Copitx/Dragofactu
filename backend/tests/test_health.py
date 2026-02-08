"""
Tests for health check and root endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test health and root endpoints."""

    def test_health_check(self, client: TestClient):
        """Test health check returns healthy status with uptime."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "app" in data
        assert "uptime_seconds" in data

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint returns API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Dragofactu" in data["message"]
        assert "docs" in data

    def test_docs_endpoint_accessible(self, client: TestClient):
        """Test OpenAPI docs are accessible."""
        response = client.get("/docs")

        # Should redirect or return HTML
        assert response.status_code in [200, 307]

    def test_openapi_json(self, client: TestClient):
        """Test OpenAPI JSON schema is accessible."""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
