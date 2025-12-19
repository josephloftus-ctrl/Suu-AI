"""TempLog service for food safety temperature monitoring"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple

from nebula.services.templog.models import (
    TempLogEntry,
    TempLogStats,
    TempCategory,
    FDA_THRESHOLDS,
    COOKING_TEMPS
)
from nebula.services.templog.repository import TempLogRepository
from nebula.services.templog.exporter import TempLogExporter
from nebula.services.templog.evaluator import evaluate_status, infer_category
from nebula.observability import get_logger

logger = get_logger(__name__)


class TempLogService:
    """
    Temperature logging service combining repository and exporter

    Provides high-level API for temperature monitoring operations
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize TempLog service

        Args:
            db_path: Optional path to SQLite database
        """
        self.repository = TempLogRepository(db_path=db_path)
        self.exporter = TempLogExporter()
        logger.info("TempLog service initialized")

    def log_entries(
        self,
        entries: List[TempLogEntry],
        source: str = "api"
    ) -> Dict[str, int]:
        """
        Log temperature entries

        Args:
            entries: List of TempLogEntry objects
            source: Source identifier

        Returns:
            Dict with insertion results
        """
        return self.repository.insert_entries(entries, source=source)

    def get_entries(
        self,
        date: Optional[str] = None,
        unit: Optional[str] = None,
        station: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Get temperature log entries with filters

        Args:
            date: Filter by date
            unit: Filter by unit
            station: Filter by station
            status: Filter by status
            limit: Maximum records

        Returns:
            List of entry dictionaries
        """
        return self.repository.fetch_entries(
            date=date,
            unit=unit,
            station=station,
            status=status,
            limit=limit
        )

    def get_stats(
        self,
        date: Optional[str] = None,
        unit: Optional[str] = None
    ) -> TempLogStats:
        """
        Get statistics for temperature logs

        Args:
            date: Filter by date
            unit: Filter by unit

        Returns:
            TempLogStats object
        """
        return self.repository.get_stats(date=date, unit=unit)

    def get_failures(
        self,
        date: Optional[str] = None,
        unit: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get failed temperature checks

        Args:
            date: Filter by date
            unit: Filter by unit
            limit: Maximum records

        Returns:
            List of FAIL entries
        """
        return self.repository.get_failures(date=date, unit=unit, limit=limit)

    def export_to_excel(
        self,
        date: str,
        unit: Optional[str] = None
    ) -> Path:
        """
        Export temperature logs to Excel

        Args:
            date: Date to export
            unit: Optional unit filter

        Returns:
            Path to exported Excel file
        """
        entries = self.repository.fetch_entries_for_export(date=date, unit=unit)
        return self.exporter.export(entries, date=date, unit=unit)

    def get_thresholds(self) -> Dict[str, Dict]:
        """
        Get FDA temperature thresholds

        Returns:
            Dict with threshold information
        """
        thresholds = {}

        # FDA thresholds
        for category, (min_temp, max_temp) in FDA_THRESHOLDS.items():
            thresholds[category.value] = {
                "min_temp": min_temp,
                "max_temp": max_temp,
                "description": f"{category.value.replace('_', ' ').title()}"
            }

        # Cooking temps
        thresholds["COOKING"] = {
            "proteins": COOKING_TEMPS,
            "description": "Cooking temperatures by protein type"
        }

        return thresholds

    def evaluate_single(
        self,
        temp_f: float,
        station: str,
        item: str
    ) -> Dict[str, any]:
        """
        Evaluate a single temperature reading

        Args:
            temp_f: Temperature in Fahrenheit
            station: Station name
            item: Item description

        Returns:
            Dict with status, category, and reason
        """
        status, category, reason = evaluate_status(temp_f, station, item)

        return {
            "temp_f": temp_f,
            "station": station,
            "item": item,
            "status": status,
            "category": category.value,
            "reason": reason
        }
