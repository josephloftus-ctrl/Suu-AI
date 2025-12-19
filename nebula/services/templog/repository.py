"""SQLite repository for temperature log data"""

import sqlite3
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from nebula.services.templog.models import TempLogEntry, TempLogStats
from nebula.services.templog.evaluator import evaluate_status
from nebula.observability import get_logger

logger = get_logger(__name__)


class TempLogRepository:
    """Repository for temperature log persistence"""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize repository with SQLite database

        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "templog.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._create_tables()
        logger.info(f"TempLog repository initialized: {self.db_path}")

    def _create_tables(self):
        """Create database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS temp_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    station TEXT NOT NULL,
                    item TEXT NOT NULL,
                    temp_f REAL NOT NULL,
                    status TEXT NOT NULL,
                    category TEXT,
                    corrective_action TEXT DEFAULT '',
                    initials TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    source TEXT DEFAULT 'api',
                    entry_hash TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_date_unit
                ON temp_logs(date, unit)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status
                ON temp_logs(status)
            """)
            conn.commit()

    def _compute_hash(self, entry: TempLogEntry) -> str:
        """
        Compute MD5 hash for duplicate detection

        Args:
            entry: TempLogEntry to hash

        Returns:
            MD5 hash string
        """
        hash_str = f"{entry.date}|{entry.time}|{entry.unit}|{entry.station}|{entry.item}|{entry.temp_f}"
        return hashlib.md5(hash_str.encode()).hexdigest()

    def insert_entries(
        self,
        entries: List[TempLogEntry],
        source: str = "api"
    ) -> Dict[str, int]:
        """
        Insert temperature log entries with duplicate detection

        Args:
            entries: List of TempLogEntry objects
            source: Source identifier (e.g., "api", "import", "manual")

        Returns:
            Dict with counts: {"inserted": int, "duplicates": int, "errors": int}
        """
        inserted = 0
        duplicates = 0
        errors = 0

        with sqlite3.connect(self.db_path) as conn:
            for entry in entries:
                try:
                    # Auto-infer status if not provided
                    if not entry.status:
                        status, category, _ = evaluate_status(
                            temp_f=entry.temp_f,
                            station=entry.station,
                            item=entry.item
                        )
                        entry.status = status
                        category_value = category.value
                    else:
                        # If status provided, still need category
                        _, category, _ = evaluate_status(
                            temp_f=entry.temp_f,
                            station=entry.station,
                            item=entry.item
                        )
                        category_value = category.value

                    # Compute hash for duplicate detection
                    entry_hash = self._compute_hash(entry)

                    # Insert
                    conn.execute("""
                        INSERT INTO temp_logs
                        (date, time, unit, station, item, temp_f, status, category,
                         corrective_action, initials, notes, source, entry_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry.date,
                        entry.time,
                        entry.unit,
                        entry.station,
                        entry.item,
                        entry.temp_f,
                        entry.status,
                        category_value,
                        entry.corrective_action,
                        entry.initials,
                        entry.notes,
                        source,
                        entry_hash
                    ))
                    inserted += 1

                except sqlite3.IntegrityError:
                    # Duplicate entry
                    duplicates += 1
                    logger.debug(f"Duplicate entry detected: {entry_hash}")

                except Exception as e:
                    errors += 1
                    logger.error(f"Error inserting entry: {e}")

            conn.commit()

        logger.info(f"Inserted {inserted} entries, {duplicates} duplicates, {errors} errors")
        return {
            "inserted": inserted,
            "duplicates": duplicates,
            "errors": errors
        }

    def fetch_entries(
        self,
        date: Optional[str] = None,
        unit: Optional[str] = None,
        station: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Fetch temperature log entries with filters

        Args:
            date: Filter by date (YYYY-MM-DD)
            unit: Filter by unit
            station: Filter by station
            status: Filter by status (PASS/FAIL/REVIEW)
            limit: Maximum number of records

        Returns:
            List of entry dictionaries
        """
        query = "SELECT * FROM temp_logs WHERE 1=1"
        params = []

        if date:
            query += " AND date = ?"
            params.append(date)
        if unit:
            query += " AND unit = ?"
            params.append(unit)
        if station:
            query += " AND station = ?"
            params.append(station)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY date DESC, time DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def fetch_entries_for_export(
        self,
        date: str,
        unit: Optional[str] = None
    ) -> List[Dict]:
        """
        Fetch entries for export, ordered by time, station, item

        Args:
            date: Date to export (YYYY-MM-DD)
            unit: Optional unit filter

        Returns:
            List of entry dictionaries ordered for export
        """
        query = """
            SELECT * FROM temp_logs
            WHERE date = ?
        """
        params = [date]

        if unit:
            query += " AND unit = ?"
            params.append(unit)

        query += " ORDER BY time, station, item"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

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
            TempLogStats with aggregated statistics
        """
        query = "SELECT * FROM temp_logs WHERE 1=1"
        params = []

        if date:
            query += " AND date = ?"
            params.append(date)
        if unit:
            query += " AND unit = ?"
            params.append(unit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            entries = [dict(row) for row in cursor.fetchall()]

        if not entries:
            return TempLogStats(
                total_entries=0,
                pass_count=0,
                fail_count=0,
                review_count=0,
                pass_rate=0.0,
                stations={},
                date_range={"start": "", "end": ""}
            )

        # Aggregate statistics
        pass_count = sum(1 for e in entries if e["status"] == "PASS")
        fail_count = sum(1 for e in entries if e["status"] == "FAIL")
        review_count = sum(1 for e in entries if e["status"] == "REVIEW")

        # Station counts
        stations = {}
        for entry in entries:
            station = entry["station"]
            stations[station] = stations.get(station, 0) + 1

        # Date range
        dates = sorted([e["date"] for e in entries])

        return TempLogStats(
            total_entries=len(entries),
            pass_count=pass_count,
            fail_count=fail_count,
            review_count=review_count,
            pass_rate=pass_count / len(entries) * 100 if entries else 0.0,
            stations=stations,
            date_range={"start": dates[0], "end": dates[-1]}
        )

    def get_failures(
        self,
        date: Optional[str] = None,
        unit: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get FAIL entries requiring corrective action

        Args:
            date: Filter by date
            unit: Filter by unit
            limit: Maximum number of records

        Returns:
            List of FAIL entries
        """
        return self.fetch_entries(
            date=date,
            unit=unit,
            status="FAIL",
            limit=limit
        )
