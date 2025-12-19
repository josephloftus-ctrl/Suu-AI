"""Temperature evaluation logic for food safety compliance"""

from typing import Optional, Tuple

from nebula.services.templog.models import (
    TempCategory,
    FDA_THRESHOLDS,
    COOKING_TEMPS,
    STATION_CATEGORY_MAP
)


def infer_category(station: str, item: str) -> TempCategory:
    """
    Infer temperature category from station name and item

    Args:
        station: Station name
        item: Item description

    Returns:
        TempCategory enum value
    """
    station_lower = station.lower().strip()
    item_lower = item.lower().strip()

    # Check station mapping first
    for station_key, category in STATION_CATEGORY_MAP.items():
        if station_key in station_lower:
            return category

    # Check item keywords for cooking
    for protein_key in COOKING_TEMPS.keys():
        if protein_key.replace("_", " ") in item_lower:
            return TempCategory.COOKING

    # Default to unknown if can't determine
    return TempCategory.UNKNOWN


def infer_cooking_temp(item: str) -> Optional[float]:
    """
    Infer required cooking temperature from item description

    Args:
        item: Item description

    Returns:
        Required minimum temperature in Fahrenheit, or None if not a cooking item
    """
    item_lower = item.lower().strip()

    # Check each protein keyword
    for protein_key, temp in COOKING_TEMPS.items():
        protein_name = protein_key.replace("_", " ")
        if protein_name in item_lower:
            return temp

    return None


def evaluate_status(
    temp_f: float,
    station: str,
    item: str
) -> Tuple[str, TempCategory, str]:
    """
    Evaluate temperature reading and determine PASS/FAIL/REVIEW status

    Args:
        temp_f: Temperature in Fahrenheit
        station: Station name
        item: Item description

    Returns:
        Tuple of (status, category, reason)
        - status: "PASS", "FAIL", or "REVIEW"
        - category: TempCategory enum value
        - reason: Human-readable explanation
    """
    category = infer_category(station, item)

    # If category unknown, mark for review
    if category == TempCategory.UNKNOWN:
        return (
            "REVIEW",
            category,
            "Unable to determine category from station/item"
        )

    # Handle cooking category specially
    if category == TempCategory.COOKING:
        required_temp = infer_cooking_temp(item)
        if required_temp is None:
            return (
                "REVIEW",
                category,
                "Unable to determine required cooking temperature for protein"
            )

        if temp_f >= required_temp:
            return (
                "PASS",
                category,
                f"Temperature {temp_f}°F meets minimum {required_temp}°F"
            )
        else:
            return (
                "FAIL",
                category,
                f"Temperature {temp_f}°F below minimum {required_temp}°F"
            )

    # Check FDA thresholds for other categories
    if category in FDA_THRESHOLDS:
        min_temp, max_temp = FDA_THRESHOLDS[category]

        # Check minimum threshold
        if min_temp is not None and temp_f < min_temp:
            return (
                "FAIL",
                category,
                f"Temperature {temp_f}°F below minimum {min_temp}°F"
            )

        # Check maximum threshold
        if max_temp is not None and temp_f > max_temp:
            return (
                "FAIL",
                category,
                f"Temperature {temp_f}°F above maximum {max_temp}°F"
            )

        # Within range
        if min_temp is not None:
            return (
                "PASS",
                category,
                f"Temperature {temp_f}°F meets minimum {min_temp}°F"
            )
        else:
            return (
                "PASS",
                category,
                f"Temperature {temp_f}°F meets maximum {max_temp}°F"
            )

    # No threshold defined for this category
    return (
        "REVIEW",
        category,
        f"No threshold defined for category {category.value}"
    )
