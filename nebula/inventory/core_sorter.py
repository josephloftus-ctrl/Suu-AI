"""Core inventory sorting and processing logic"""

import json
from pathlib import Path
from typing import Optional, Dict, List
import pandas as pd

from nebula.inventory.schemas import (
    InventoryRow,
    InventoryPackage,
    LocationProfile
)


def build_inventory_package(
    source_file: Path,
    location_code: str,
    config_dir: Optional[Path] = None
) -> InventoryPackage:
    """
    Build an inventory package from source file

    Args:
        source_file: Path to source inventory file (CSV/Excel)
        location_code: Location identifier
        config_dir: Optional path to configuration directory

    Returns:
        InventoryPackage ready for rendering
    """
    # Load configuration
    if config_dir is None:
        config_dir = Path(__file__).parent.parent / "config"

    rules = _load_inventory_rules(config_dir)
    district_map = _load_district_map(config_dir)

    # Load source data
    df = _load_source_file(source_file)

    # Build location profile
    location = _build_location_profile(location_code, district_map)

    # Process inventory items
    items = []
    for _, row in df.iterrows():
        item = _process_inventory_row(row, rules)
        if item:
            items.append(item)

    return InventoryPackage(
        location=location,
        items=items,
        source_file=source_file,
        metadata={
            "total_rows": len(df),
            "processed_items": len(items)
        }
    )


def assign_location(
    item_description: str,
    item_category: Optional[str],
    rules: Dict
) -> Optional[str]:
    """
    Assign location based on keyword/category matching

    Args:
        item_description: Item description text
        item_category: Optional item category
        rules: Inventory rules configuration

    Returns:
        Location code or None
    """
    if not rules or "location_rules" not in rules:
        return None

    location_rules = rules["location_rules"]
    description_lower = item_description.lower() if item_description else ""

    # Check category rules first
    if item_category and "categories" in location_rules:
        category_lower = item_category.lower()
        for rule in location_rules.get("categories", []):
            if rule.get("category", "").lower() == category_lower:
                return rule.get("location")

    # Check keyword rules
    if "keywords" in location_rules:
        for rule in location_rules.get("keywords", []):
            keywords = rule.get("keywords", [])
            location = rule.get("location")
            for keyword in keywords:
                if keyword.lower() in description_lower:
                    return location

    return None


def _load_inventory_rules(config_dir: Path) -> Dict:
    """Load inventory rules from JSON"""
    rules_file = config_dir / "inventory_rules.json"
    if not rules_file.exists():
        return {}

    with open(rules_file, "r") as f:
        return json.load(f)


def _load_district_map(config_dir: Path) -> Dict:
    """Load district map from JSON"""
    data_dir = config_dir.parent / "data"
    map_file = data_dir / "district_map_ken_gruber_v1.json"
    if not map_file.exists():
        return {}

    with open(map_file, "r") as f:
        return json.load(f)


def _load_source_file(source_file: Path) -> pd.DataFrame:
    """Load source file (CSV or Excel)"""
    suffix = source_file.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(source_file)
    elif suffix in [".xlsx", ".xls"]:
        return pd.read_excel(source_file)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def _build_location_profile(
    location_code: str,
    district_map: Dict
) -> LocationProfile:
    """Build location profile from district map"""
    # Look up location in district map
    location_data = district_map.get(location_code, {})

    return LocationProfile(
        code=location_code,
        name=location_data.get("name", location_code),
        district=location_data.get("district"),
        region=location_data.get("region"),
        metadata=location_data
    )


def _process_inventory_row(row: pd.Series, rules: Dict) -> Optional[InventoryRow]:
    """Process a single inventory row"""
    # Extract core fields (adjust based on actual CSV structure)
    item_code = _safe_get(row, "item_code") or _safe_get(row, "Item Code") or _safe_get(row, "SKU")
    description = _safe_get(row, "description") or _safe_get(row, "Description") or _safe_get(row, "Item")
    category = _safe_get(row, "category") or _safe_get(row, "Category")
    quantity = _safe_get_float(row, "quantity") or _safe_get_float(row, "Quantity") or _safe_get_float(row, "Qty")
    unit = _safe_get(row, "unit") or _safe_get(row, "Unit") or _safe_get(row, "UOM")

    # Skip if missing critical data
    if not item_code and not description:
        return None

    # Assign location
    location = assign_location(description, category, rules)

    # Build metadata from remaining columns
    metadata = {}
    for key, value in row.items():
        if key not in ["item_code", "description", "category", "quantity", "unit", "location"]:
            if pd.notna(value):
                metadata[key] = value

    return InventoryRow(
        item_code=str(item_code) if item_code else "",
        description=str(description) if description else "",
        category=category,
        quantity=quantity,
        unit=unit,
        location=location,
        metadata=metadata
    )


def _safe_get(row: pd.Series, key: str) -> Optional[str]:
    """Safely get string value from row"""
    if key not in row:
        return None
    value = row[key]
    if pd.isna(value):
        return None
    return str(value).strip()


def _safe_get_float(row: pd.Series, key: str) -> Optional[float]:
    """Safely get float value from row"""
    if key not in row:
        return None
    value = row[key]
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None
