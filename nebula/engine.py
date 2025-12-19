"""Nebula Engine - Main facade for the kitchen operating system"""

from pathlib import Path
from typing import Optional
import pandas as pd

from nebula.inventory.core_sorter import build_inventory_package
from nebula.inventory.schemas import InventoryPackage, RenderResult
from nebula.renderers.ordermaestro import OrderMaestroRenderer
from nebula.observability import get_logger

logger = get_logger(__name__)


class NebulaEngine:
    """Main engine facade for Nebula operations"""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize the Nebula Engine

        Args:
            config_dir: Optional path to configuration directory
        """
        self.config_dir = config_dir or Path(__file__).parent / "config"
        self.renderer = OrderMaestroRenderer()
        logger.info(f"NebulaEngine initialized with config_dir: {self.config_dir}")

    def process_inventory(
        self,
        source_file: Path,
        location_code: str,
        mode: str = "production",
        output_dir: Optional[Path] = None
    ) -> RenderResult:
        """
        Process inventory from source file and generate output

        Args:
            source_file: Path to source inventory file (CSV/Excel)
            location_code: Location identifier (e.g., "KG001")
            mode: Rendering mode ("production" or "development")
            output_dir: Optional output directory for exports

        Returns:
            RenderResult with output file path and metadata
        """
        logger.info(f"Processing inventory: source={source_file}, location={location_code}, mode={mode}")

        # Validate source file
        self._validate_source_file(source_file)
        logger.debug(f"Source file validated: {source_file}")

        # Build inventory package
        package = self._build_inventory_package(source_file, location_code)
        logger.info(f"Inventory package built: {len(package.items)} items")

        # Render output
        output_dir = output_dir or Path(__file__).parent / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)

        result = self.renderer.render(package, mode=mode, output_dir=output_dir)
        logger.info(f"Rendering complete: {result.output_file}, {result.rows_written} rows")

        return result

    def _validate_source_file(self, source_file: Path) -> None:
        """
        Validate that source file exists and has supported format

        Args:
            source_file: Path to source inventory file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        if not source_file.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")

        supported_formats = [".csv", ".xlsx", ".xls"]
        if source_file.suffix.lower() not in supported_formats:
            raise ValueError(
                f"Unsupported file format: {source_file.suffix}. "
                f"Supported formats: {', '.join(supported_formats)}"
            )

    def _build_inventory_package(
        self,
        source_file: Path,
        location_code: str
    ) -> InventoryPackage:
        """
        Wrapper around core_sorter.build_inventory_package
        Isolates the core_sorter signature from the engine interface

        Args:
            source_file: Path to source inventory file
            location_code: Location identifier

        Returns:
            InventoryPackage ready for rendering
        """
        return build_inventory_package(
            source_file=source_file,
            location_code=location_code,
            config_dir=self.config_dir
        )

    def health_check(self) -> dict:
        """
        Perform health check on engine components

        Returns:
            Dictionary with health status
        """
        status = {
            "engine": "ok",
            "config_dir": str(self.config_dir),
            "config_exists": self.config_dir.exists(),
            "renderer": "ok"
        }

        # Check for required config files
        rules_file = self.config_dir / "inventory_rules.json"
        status["inventory_rules_exists"] = rules_file.exists()

        return status
