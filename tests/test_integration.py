"""Integration tests for full Nebula Engine pipeline"""

import pytest
from pathlib import Path
import tempfile
import pandas as pd

from nebula.engine import NebulaEngine
from nebula.inventory.schemas import RenderResult


class TestIntegrationPipeline:
    """Test suite for full pipeline integration"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_csv(self, temp_dir):
        """Create a sample CSV file for testing"""
        csv_file = temp_dir / "test_inventory.csv"
        data = {
            "item_code": ["SKU001", "SKU002", "SKU003"],
            "description": ["Fresh Lettuce", "Whole Milk", "Chicken Breast"],
            "category": ["Produce", "Dairy", "Meat"],
            "quantity": [50, 20, 100],
            "unit": ["lbs", "gal", "lbs"]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_file, index=False)
        return csv_file

    def test_full_pipeline_csv(self, sample_csv, temp_dir):
        """Test full pipeline with CSV input"""
        engine = NebulaEngine()
        output_dir = temp_dir / "exports"

        result = engine.process_inventory(
            source_file=sample_csv,
            location_code="KG001",
            mode="production",
            output_dir=output_dir
        )

        assert isinstance(result, RenderResult)
        assert result.output_file.exists()
        assert result.rows_written == 3
        assert result.output_file.suffix == ".xlsx"

    def test_full_pipeline_development_mode(self, sample_csv, temp_dir):
        """Test full pipeline with development mode"""
        engine = NebulaEngine()
        output_dir = temp_dir / "exports"

        result = engine.process_inventory(
            source_file=sample_csv,
            location_code="KG002",
            mode="development",
            output_dir=output_dir
        )

        assert isinstance(result, RenderResult)
        assert result.output_file.exists()
        assert result.rows_written == 3

        # Verify development mode columns were added
        df = pd.read_excel(result.output_file)
        assert "_dev_mode" in df.columns
        assert "_row_num" in df.columns

    def test_pipeline_with_missing_file(self, temp_dir):
        """Test pipeline with non-existent source file"""
        engine = NebulaEngine()
        missing_file = temp_dir / "nonexistent.csv"

        with pytest.raises(FileNotFoundError):
            engine.process_inventory(
                source_file=missing_file,
                location_code="KG001",
                mode="production"
            )

    def test_pipeline_with_invalid_format(self, temp_dir):
        """Test pipeline with unsupported file format"""
        engine = NebulaEngine()
        invalid_file = temp_dir / "test.txt"
        invalid_file.write_text("test data")

        with pytest.raises(ValueError, match="Unsupported file format"):
            engine.process_inventory(
                source_file=invalid_file,
                location_code="KG001",
                mode="production"
            )

    def test_pipeline_location_assignment(self, sample_csv, temp_dir):
        """Test that location assignment works in pipeline"""
        engine = NebulaEngine()
        output_dir = temp_dir / "exports"

        result = engine.process_inventory(
            source_file=sample_csv,
            location_code="KG001",
            mode="production",
            output_dir=output_dir
        )

        # Read the output and verify locations were assigned
        df = pd.read_excel(result.output_file)
        assert "location" in df.columns

        # Check that at least one item got a location assigned
        # (based on our inventory rules)
        locations = df["location"].dropna()
        assert len(locations) > 0

    def test_pipeline_with_large_dataset(self, temp_dir):
        """Test pipeline with larger dataset"""
        csv_file = temp_dir / "large_inventory.csv"

        # Create dataset with 100 items
        data = {
            "item_code": [f"SKU{i:03d}" for i in range(100)],
            "description": [f"Item {i}" for i in range(100)],
            "category": ["Produce"] * 50 + ["Dairy"] * 50,
            "quantity": [10] * 100,
            "unit": ["lbs"] * 100
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_file, index=False)

        engine = NebulaEngine()
        output_dir = temp_dir / "exports"

        result = engine.process_inventory(
            source_file=csv_file,
            location_code="KG003",
            mode="production",
            output_dir=output_dir
        )

        assert result.rows_written == 100
        assert result.output_file.exists()

    def test_pipeline_with_empty_csv(self, temp_dir):
        """Test pipeline with empty CSV file"""
        csv_file = temp_dir / "empty.csv"
        df = pd.DataFrame(columns=["item_code", "description", "category", "quantity", "unit"])
        df.to_csv(csv_file, index=False)

        engine = NebulaEngine()
        output_dir = temp_dir / "exports"

        result = engine.process_inventory(
            source_file=csv_file,
            location_code="KG001",
            mode="production",
            output_dir=output_dir
        )

        assert result.rows_written == 0
        assert result.output_file.exists()

    def test_pipeline_id_filling(self, temp_dir):
        """Test that missing IDs are properly filled"""
        csv_file = temp_dir / "missing_ids.csv"
        data = {
            "item_code": ["", None, "SKU003"],
            "description": ["Item 1", "Item 2", "Item 3"],
            "category": ["Produce", "Dairy", "Meat"],
            "quantity": [10, 20, 30],
            "unit": ["lbs", "gal", "lbs"]
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_file, index=False)

        engine = NebulaEngine()
        output_dir = temp_dir / "exports"

        result = engine.process_inventory(
            source_file=csv_file,
            location_code="KG001",
            mode="production",
            output_dir=output_dir
        )

        # Read output and verify IDs were filled
        output_df = pd.read_excel(result.output_file)
        assert all(output_df["item_code"].notna())
        assert "AUTO_" in str(output_df["item_code"].iloc[0])
