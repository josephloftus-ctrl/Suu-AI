"""Data models for temperature logging service"""

from enum import Enum
from typing import Optional, List, Dict, Tuple
from datetime import date, time
from pydantic import BaseModel, Field


class TempCategory(str, Enum):
    """Temperature monitoring categories"""
    HOT_HOLDING = "HOT_HOLDING"
    COLD_HOLDING = "COLD_HOLDING"
    COOKING = "COOKING"
    RECEIVING_COLD = "RECEIVING_COLD"
    RECEIVING_FROZEN = "RECEIVING_FROZEN"
    COOLING = "COOLING"
    REHEATING = "REHEATING"
    UNKNOWN = "UNKNOWN"


# FDA Temperature Thresholds
# Format: {category: (min_temp, max_temp)} where None means no limit
FDA_THRESHOLDS: Dict[TempCategory, Tuple[Optional[float], Optional[float]]] = {
    TempCategory.HOT_HOLDING: (135.0, None),  # Must be ≥135°F
    TempCategory.COLD_HOLDING: (None, 41.0),  # Must be ≤41°F
    TempCategory.RECEIVING_FROZEN: (None, 0.0),  # Must be ≤0°F
    TempCategory.REHEATING: (165.0, None),  # Must be ≥165°F
}


# Cooking temperatures by protein (minimum internal temperature)
COOKING_TEMPS: Dict[str, float] = {
    # Poultry
    "chicken": 165.0,
    "poultry": 165.0,
    "turkey": 165.0,

    # Ground meats
    "ground_beef": 155.0,
    "burger": 155.0,
    "hamburger": 155.0,

    # Other proteins
    "beef": 145.0,
    "pork": 145.0,
    "steak": 145.0,
    "fish": 145.0,
    "seafood": 145.0,
    "eggs": 145.0,
}


# Station to category mapping
STATION_CATEGORY_MAP: Dict[str, TempCategory] = {
    # Hot holding
    "grill": TempCategory.HOT_HOLDING,
    "hot well": TempCategory.HOT_HOLDING,
    "steam table": TempCategory.HOT_HOLDING,
    "heat lamp": TempCategory.HOT_HOLDING,

    # Cold holding
    "salad bar": TempCategory.COLD_HOLDING,
    "cold well": TempCategory.COLD_HOLDING,
    "walk-in": TempCategory.COLD_HOLDING,
    "cooler": TempCategory.COLD_HOLDING,
    "refrigerator": TempCategory.COLD_HOLDING,

    # Frozen
    "freezer": TempCategory.RECEIVING_FROZEN,

    # Receiving
    "receiving": TempCategory.RECEIVING_COLD,
    "delivery": TempCategory.RECEIVING_COLD,
}


class TempLogEntry(BaseModel):
    """Single temperature log entry"""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    time: str = Field(..., description="Time in HH:MM format")
    unit: str = Field(..., description="Unit/location identifier")
    station: str = Field(..., description="Station name")
    item: str = Field(..., description="Item being monitored")
    temp_f: float = Field(..., description="Temperature in Fahrenheit")
    status: Optional[str] = Field(None, description="PASS/FAIL/REVIEW status")
    corrective_action: str = Field("", description="Corrective action taken")
    initials: str = Field("", description="Employee initials")
    notes: str = Field("", description="Additional notes")


class TempLogBatch(BaseModel):
    """Batch of temperature log entries"""
    entries: List[TempLogEntry] = Field(..., min_length=1, description="List of temperature entries")


class TempLogStats(BaseModel):
    """Statistics for temperature logs"""
    total_entries: int = Field(..., description="Total number of entries")
    pass_count: int = Field(..., description="Number of PASS entries")
    fail_count: int = Field(..., description="Number of FAIL entries")
    review_count: int = Field(..., description="Number of REVIEW entries")
    pass_rate: float = Field(..., description="Percentage of passing entries")
    stations: Dict[str, int] = Field(..., description="Entry count by station")
    date_range: Dict[str, str] = Field(..., description="Start and end dates")
