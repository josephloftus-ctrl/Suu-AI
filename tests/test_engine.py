"""Tests for Nebula Engine core functionality"""

import pytest
from pathlib import Path
from nebula.engine import NebulaEngine


class TestNebulaEngine:
    """Test suite for NebulaEngine"""

    def test_engine_initialization(self):
        """Test that engine initializes correctly"""
        engine = NebulaEngine()
        assert engine is not None
        assert engine.config_dir is not None
        assert engine.renderer is not None

    def test_health_check(self):
        """Test engine health check"""
        engine = NebulaEngine()
        status = engine.health_check()

        assert "engine" in status
        assert status["engine"] == "ok"
        assert "config_dir" in status
        assert "config_exists" in status
        assert "renderer" in status

    def test_custom_config_dir(self, tmp_path):
        """Test engine with custom config directory"""
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        engine = NebulaEngine(config_dir=config_dir)
        assert engine.config_dir == config_dir

    def test_health_check_reports_missing_config(self, tmp_path):
        """Test that health check reports missing configuration files"""
        config_dir = tmp_path / "empty_config"
        config_dir.mkdir()

        engine = NebulaEngine(config_dir=config_dir)
        status = engine.health_check()

        assert status["inventory_rules_exists"] is False
