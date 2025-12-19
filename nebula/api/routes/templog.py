"""Temperature logging endpoints"""

import uuid
import os
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query

from nebula.api.schemas import JobResponse, Artifact
from nebula.services.templog import TempLogService
from nebula.services.templog.models import TempLogBatch
from nebula.observability import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Initialize TempLog service as singleton
_templog_service = TempLogService()


@router.post("/temp-log", response_model=JobResponse)
async def log_temperatures(
    batch: TempLogBatch,
    source: str = Query("api", description="Source identifier")
):
    """
    Log a batch of temperature readings

    Args:
        batch: Batch of temperature entries
        source: Source identifier (e.g., "api", "import", "manual")

    Returns:
        JobResponse with insertion results
    """
    request_id = str(uuid.uuid4())
    started_at = datetime.now()

    # Insert entries
    result = _templog_service.log_entries(batch.entries, source=source)

    status = "ok"
    warnings = []

    if result["duplicates"] > 0:
        status = "warning"
        warnings.append(f"{result['duplicates']} duplicate entries ignored")

    if result["errors"] > 0:
        status = "warning"
        warnings.append(f"{result['errors']} entries failed to insert")

    return JobResponse(
        request_id=request_id,
        status=status,
        started_at=started_at,
        finished_at=datetime.now(),
        message=f"Logged {result['inserted']} temperature entries",
        data={
            "inserted": result["inserted"],
            "duplicates": result["duplicates"],
            "errors": result["errors"],
            "total_submitted": len(batch.entries)
        },
        warnings=warnings if warnings else None
    )


@router.get("/temp-log", response_model=JobResponse)
async def get_temperature_logs(
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    unit: Optional[str] = Query(None, description="Filter by unit"),
    station: Optional[str] = Query(None, description="Filter by station"),
    status: Optional[str] = Query(None, description="Filter by status (PASS/FAIL/REVIEW)"),
    limit: int = Query(1000, description="Maximum records to return")
):
    """
    Query temperature log entries

    Args:
        date: Filter by date
        unit: Filter by unit
        station: Filter by station
        status: Filter by status
        limit: Maximum records

    Returns:
        JobResponse with query results
    """
    request_id = str(uuid.uuid4())
    started_at = datetime.now()

    entries = _templog_service.get_entries(
        date=date,
        unit=unit,
        station=station,
        status=status,
        limit=limit
    )

    return JobResponse(
        request_id=request_id,
        status="ok",
        started_at=started_at,
        finished_at=datetime.now(),
        message=f"Retrieved {len(entries)} temperature entries",
        data={
            "entries": entries,
            "count": len(entries),
            "filters": {
                "date": date,
                "unit": unit,
                "station": station,
                "status": status
            }
        }
    )


@router.post("/temp-log/export", response_model=JobResponse)
async def export_temperature_logs(
    date: str = Query(..., description="Date to export (YYYY-MM-DD)"),
    unit: Optional[str] = Query(None, description="Filter by unit")
):
    """
    Export temperature logs to Excel

    Args:
        date: Date to export
        unit: Optional unit filter

    Returns:
        JobResponse with artifact
    """
    request_id = str(uuid.uuid4())
    started_at = datetime.now()

    # Export to Excel
    output_file = _templog_service.export_to_excel(date=date, unit=unit)

    # Get file size
    file_size = os.path.getsize(output_file)

    # Create artifact
    artifact = Artifact(
        name=output_file.name,
        path=str(output_file),
        size_bytes=file_size,
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    return JobResponse(
        request_id=request_id,
        status="ok",
        started_at=started_at,
        finished_at=datetime.now(),
        message=f"Exported temperature logs for {date}",
        data={
            "date": date,
            "unit": unit,
            "filename": output_file.name
        },
        artifacts=[artifact]
    )


@router.get("/temp-log/stats", response_model=JobResponse)
async def get_temperature_stats(
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    unit: Optional[str] = Query(None, description="Filter by unit")
):
    """
    Get temperature log statistics

    Args:
        date: Filter by date
        unit: Filter by unit

    Returns:
        JobResponse with statistics
    """
    request_id = str(uuid.uuid4())
    started_at = datetime.now()

    stats = _templog_service.get_stats(date=date, unit=unit)

    return JobResponse(
        request_id=request_id,
        status="ok",
        started_at=started_at,
        finished_at=datetime.now(),
        message="Temperature log statistics",
        data=stats.model_dump()
    )


@router.get("/temp-log/failures", response_model=JobResponse)
async def get_temperature_failures(
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    unit: Optional[str] = Query(None, description="Filter by unit"),
    limit: int = Query(100, description="Maximum records to return")
):
    """
    Get failed temperature checks requiring corrective action

    Args:
        date: Filter by date
        unit: Filter by unit
        limit: Maximum records

    Returns:
        JobResponse with failed entries
    """
    request_id = str(uuid.uuid4())
    started_at = datetime.now()

    failures = _templog_service.get_failures(date=date, unit=unit, limit=limit)

    return JobResponse(
        request_id=request_id,
        status="ok",
        started_at=started_at,
        finished_at=datetime.now(),
        message=f"Retrieved {len(failures)} failed temperature checks",
        data={
            "failures": failures,
            "count": len(failures)
        }
    )


@router.get("/temp-log/thresholds", response_model=JobResponse)
async def get_fda_thresholds():
    """
    Get FDA temperature thresholds reference data

    Returns:
        JobResponse with threshold information
    """
    request_id = str(uuid.uuid4())
    started_at = datetime.now()

    thresholds = _templog_service.get_thresholds()

    return JobResponse(
        request_id=request_id,
        status="ok",
        started_at=started_at,
        finished_at=datetime.now(),
        message="FDA temperature thresholds",
        data={"thresholds": thresholds}
    )


@router.post("/temp-log/evaluate", response_model=JobResponse)
async def evaluate_temperature(
    temp_f: float = Query(..., description="Temperature in Fahrenheit"),
    station: str = Query(..., description="Station name"),
    item: str = Query(..., description="Item description")
):
    """
    Evaluate a single temperature reading

    Args:
        temp_f: Temperature in Fahrenheit
        station: Station name
        item: Item description

    Returns:
        JobResponse with evaluation result
    """
    request_id = str(uuid.uuid4())
    started_at = datetime.now()

    evaluation = _templog_service.evaluate_single(temp_f, station, item)

    return JobResponse(
        request_id=request_id,
        status="ok",
        started_at=started_at,
        finished_at=datetime.now(),
        message=f"Temperature evaluation: {evaluation['status']}",
        data=evaluation
    )
