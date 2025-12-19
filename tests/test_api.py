"""Tests for FastAPI endpoints"""

import pytest
from fastapi.testclient import TestClient

from nebula.api.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_health_check(self):
        """Test GET /api/v1/health"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert "request_id" in data
        assert data["status"] == "ok"
        assert "data" in data
        assert "version" in data["data"]
        assert "engine" in data["data"]
        assert "rules_count" in data["data"]


class TestInventoryEndpoints:
    """Tests for inventory endpoints"""

    def test_assign_location_produce(self):
        """Test POST /api/v1/assign-location with produce"""
        payload = {
            "description": "Fresh Lettuce",
            "category": "Produce"
        }
        response = client.post("/api/v1/assign-location", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["description"] == "Fresh Lettuce"
        assert data["location"] is not None
        assert data["matched_by"] in ["category", "keyword"]

    def test_assign_location_keyword(self):
        """Test POST /api/v1/assign-location with keyword match"""
        payload = {
            "description": "Whole Milk"
        }
        response = client.post("/api/v1/assign-location", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["description"] == "Whole Milk"

    def test_assign_location_no_match(self):
        """Test POST /api/v1/assign-location with no match"""
        payload = {
            "description": "Unknown Item XYZ123"
        }
        response = client.post("/api/v1/assign-location", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["location"] is None


class TestRootRedirect:
    """Tests for root endpoint"""

    def test_root_redirects_to_docs(self):
        """Test GET / redirects to /docs"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/docs"
