"""Inventory processing endpoints"""

import uuid
import tempfile
import os
from datetime import datetime
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException

from nebula.engine import NebulaEngine
from nebula.api.schemas import JobResponse, Artifact, AssignLocationRequest, AssignLocationResponse
from nebula.api.deps import get_engine
from nebula.inventory.core_sorter import assign_location
from nebula.observability import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/sort", response_model=JobResponse)
async def sort_inventory(
    file: UploadFile = File(...),
    location_code: str = Form(...),
    mode: Literal["production", "development"] = Form("production"),
    dry_run: bool = Form(False),
    engine: NebulaEngine = Depends(get_engine)
):
    """
    Process inventory file and generate sorted output

    Args:
        file: Uploaded inventory file (CSV or Excel)
        location_code: Location identifier (e.g., "KG001")
        mode: Processing mode (production or development)
        dry_run: If true, validate only without processing

    Returns:
        JobResponse with artifact details
    """
    request_id = str(uuid.uuid4())
    started_at = datetime.now()
    warnings = []

    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in [".csv", ".xlsx", ".xls"]:
        raise ValueError(
            f"Unsupported file format: {file_ext}. "
            f"Supported formats: .csv, .xlsx, .xls"
        )

    # Validate mode
    if mode not in ["production", "development"]:
        raise ValueError(f"Invalid mode: {mode}. Must be 'production' or 'development'")

    if dry_run:
        logger.info(f"Dry run mode - validation only [{request_id}]")
        return JobResponse(
            request_id=request_id,
            status="ok",
            started_at=started_at,
            finished_at=datetime.now(),
            message="Validation successful (dry run)",
            data={
                "filename": file.filename,
                "location_code": location_code,
                "mode": mode,
                "dry_run": True
            },
            warnings=["Dry run mode - no processing performed"]
        )

    # Save uploaded file to temporary location
    temp_dir = tempfile.mkdtemp()
    temp_file = Path(temp_dir) / file.filename

    try:
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"Processing file: {file.filename} [{request_id}]")

        # Process via engine
        result = engine.process_inventory(
            source_file=temp_file,
            location_code=location_code,
            mode=mode
        )

        # Get file size
        file_size = os.path.getsize(result.output_file)

        # Create artifact
        artifact = Artifact(
            name=result.output_file.name,
            path=str(result.output_file),
            size_bytes=file_size,
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Add result warnings
        if result.warnings:
            warnings.extend(result.warnings)

        return JobResponse(
            request_id=request_id,
            status="ok" if not warnings else "warning",
            started_at=started_at,
            finished_at=datetime.now(),
            message=f"Successfully processed {result.rows_written} rows",
            data={
                "rows_written": result.rows_written,
                "location_code": location_code,
                "mode": mode
            },
            artifacts=[artifact],
            warnings=warnings if warnings else None
        )

    finally:
        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()
        if Path(temp_dir).exists():
            Path(temp_dir).rmdir()


@router.post("/assign-location", response_model=AssignLocationResponse)
async def assign_item_location(
    request: AssignLocationRequest,
    engine: NebulaEngine = Depends(get_engine)
):
    """
    Assign location for a single item based on description and category

    Args:
        request: Item description and optional category

    Returns:
        AssignLocationResponse with assigned location and match method
    """
    # Load inventory rules
    import json
    rules_file = engine.config_dir / "inventory_rules.json"
    rules = {}
    if rules_file.exists():
        with open(rules_file, "r") as f:
            rules = json.load(f)

    # Assign location
    location = assign_location(
        item_description=request.description,
        item_category=request.category,
        rules=rules
    )

    # Determine match method
    matched_by = None
    if location:
        # Check if matched by category
        if request.category and "location_rules" in rules:
            categories = rules["location_rules"].get("categories", [])
            for cat_rule in categories:
                if cat_rule.get("category", "").lower() == request.category.lower():
                    matched_by = "category"
                    break

        # If not category, must be keyword
        if not matched_by:
            matched_by = "keyword"

    return AssignLocationResponse(
        location=location,
        matched_by=matched_by,
        description=request.description,
        category=request.category
    )
