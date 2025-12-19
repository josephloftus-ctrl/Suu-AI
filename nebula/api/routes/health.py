"""Health check endpoints"""

import uuid
import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends

from nebula.engine import NebulaEngine
from nebula.api import __version__
from nebula.api.schemas import JobResponse
from nebula.api.deps import get_engine

router = APIRouter()


@router.get("/health", response_model=JobResponse)
async def health_check(engine: NebulaEngine = Depends(get_engine)):
    """
    Check API and engine health status

    Returns JobResponse with version, engine status, and rules count
    """
    request_id = str(uuid.uuid4())
    started_at = datetime.now()

    # Get engine health
    engine_status = engine.health_check()

    # Count rules
    rules_count = 0
    rules_file = engine.config_dir / "inventory_rules.json"
    if rules_file.exists():
        with open(rules_file, "r") as f:
            rules_data = json.load(f)
            # Count categories + keywords
            location_rules = rules_data.get("location_rules", {})
            rules_count += len(location_rules.get("categories", []))
            rules_count += len(location_rules.get("keywords", []))

    return JobResponse(
        request_id=request_id,
        status="ok",
        started_at=started_at,
        finished_at=datetime.now(),
        message="Nebula Engine is healthy",
        data={
            "version": __version__,
            "engine": engine_status,
            "rules_count": rules_count
        }
    )
