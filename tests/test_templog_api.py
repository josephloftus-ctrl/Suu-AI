"""Tests for TempLog API endpoints"""

import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from nebula.api.main import app
from nebula.services.templog import TempLogService

client = TestClient(app)


class TestTempLogEndpoints:
    """Tests for temperature logging endpoints"""

    def test_log_single_entry(self):
        """Test POST /api/v1/temp-log with single entry"""
        payload = {
            "entries": [
                {
                    "date": "2025-12-19",
                    "time": "14:30",
                    "unit": "KG001",
                    "station": "grill",
                    "item": "chicken breast",
                    "temp_f": 170.0,
                    "corrective_action": "",
                    "initials": "JD",
                    "notes": ""
                }
            ]
        }
        response = client.post("/api/v1/temp-log", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["ok", "warning"]
        assert "data" in data
        assert data["data"]["inserted"] >= 0

    def test_evaluate_temperature_pass(self):
        """Test POST /api/v1/temp-log/evaluate with passing temp"""
        response = client.post(
            "/api/v1/temp-log/evaluate",
            params={
                "temp_f": 140.0,
                "station": "hot well",
                "item": "mashed potatoes"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "data" in data
        assert data["data"]["status"] == "PASS"

    def test_evaluate_temperature_fail(self):
        """Test POST /api/v1/temp-log/evaluate with failing temp"""
        response = client.post(
            "/api/v1/temp-log/evaluate",
            params={
                "temp_f": 130.0,
                "station": "hot well",
                "item": "gravy"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert data["data"]["status"] == "FAIL"

    def test_get_thresholds(self):
        """Test GET /api/v1/temp-log/thresholds"""
        response = client.get("/api/v1/temp-log/thresholds")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "data" in data
        assert "thresholds" in data["data"]

    def test_get_stats(self):
        """Test GET /api/v1/temp-log/stats"""
        response = client.get("/api/v1/temp-log/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "data" in data


class TestTempLogEvaluator:
    """Tests for temperature evaluation logic"""

    def test_hot_holding_pass(self):
        """Test hot holding temperature evaluation - PASS"""
        from nebula.services.templog.evaluator import evaluate_status

        status, category, reason = evaluate_status(
            temp_f=140.0,
            station="hot well",
            item="soup"
        )
        assert status == "PASS"

    def test_hot_holding_fail(self):
        """Test hot holding temperature evaluation - FAIL"""
        from nebula.services.templog.evaluator import evaluate_status

        status, category, reason = evaluate_status(
            temp_f=130.0,
            station="steam table",
            item="vegetables"
        )
        assert status == "FAIL"

    def test_cold_holding_pass(self):
        """Test cold holding temperature evaluation - PASS"""
        from nebula.services.templog.evaluator import evaluate_status

        status, category, reason = evaluate_status(
            temp_f=38.0,
            station="salad bar",
            item="lettuce"
        )
        assert status == "PASS"

    def test_cold_holding_fail(self):
        """Test cold holding temperature evaluation - FAIL"""
        from nebula.services.templog.evaluator import evaluate_status

        status, category, reason = evaluate_status(
            temp_f=45.0,
            station="cold well",
            item="milk"
        )
        assert status == "FAIL"

    def test_cooking_chicken_pass(self):
        """Test cooking temperature evaluation - chicken PASS"""
        from nebula.services.templog.evaluator import evaluate_status

        status, category, reason = evaluate_status(
            temp_f=170.0,
            station="grill",
            item="chicken breast"
        )
        assert status == "PASS"

    def test_cooking_chicken_fail(self):
        """Test cooking temperature evaluation - chicken FAIL"""
        from nebula.services.templog.evaluator import evaluate_status

        status, category, reason = evaluate_status(
            temp_f=160.0,
            station="oven",
            item="turkey"
        )
        assert status == "FAIL"
