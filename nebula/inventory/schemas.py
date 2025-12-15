"""Data schemas for inventory processing"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd


@dataclass
class InventoryRow:
    """Single inventory item row"""
    item_code: str
    description: str
    category: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "item_code": self.item_code,
            "description": self.description,
            "category": self.category,
            "quantity": self.quantity,
            "unit": self.unit,
            "location": self.location,
            **self.metadata
        }


@dataclass
class LocationProfile:
    """Location profile with configuration"""
    code: str
    name: str
    district: Optional[str] = None
    region: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InventoryPackage:
    """Complete inventory package ready for rendering"""
    location: LocationProfile
    items: List[InventoryRow]
    source_file: Path
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert items to pandas DataFrame"""
        if not self.items:
            return pd.DataFrame()
        return pd.DataFrame([item.to_dict() for item in self.items])


@dataclass
class RenderResult:
    """Result of rendering operation"""
    output_file: Path
    rows_written: int
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
