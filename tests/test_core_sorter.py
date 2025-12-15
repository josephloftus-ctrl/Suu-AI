"""Tests for core inventory sorting functionality"""

import pytest
from pathlib import Path
from nebula.inventory.core_sorter import assign_location


class TestCoresorter:
    """Test suite for core sorting functionality"""

    def test_assign_location_by_keyword(self):
        """Test location assignment by keyword matching"""
        rules = {
            "location_rules": {
                "keywords": [
                    {
                        "keywords": ["lettuce", "tomato"],
                        "location": "COOLER-1"
                    }
                ]
            }
        }

        location = assign_location("Fresh Lettuce", None, rules)
        assert location == "COOLER-1"

        location = assign_location("Ripe Tomato", None, rules)
        assert location == "COOLER-1"

    def test_assign_location_by_category(self):
        """Test location assignment by category matching"""
        rules = {
            "location_rules": {
                "categories": [
                    {
                        "category": "Produce",
                        "location": "COOLER-1"
                    },
                    {
                        "category": "Dairy",
                        "location": "COOLER-2"
                    }
                ]
            }
        }

        location = assign_location("Some Item", "Produce", rules)
        assert location == "COOLER-1"

        location = assign_location("Milk", "Dairy", rules)
        assert location == "COOLER-2"

    def test_assign_location_category_priority(self):
        """Test that category rules take priority over keyword rules"""
        rules = {
            "location_rules": {
                "categories": [
                    {
                        "category": "Produce",
                        "location": "COOLER-1"
                    }
                ],
                "keywords": [
                    {
                        "keywords": ["lettuce"],
                        "location": "COOLER-2"
                    }
                ]
            }
        }

        # Category should take priority
        location = assign_location("Fresh Lettuce", "Produce", rules)
        assert location == "COOLER-1"

    def test_assign_location_case_insensitive(self):
        """Test that location assignment is case insensitive"""
        rules = {
            "location_rules": {
                "keywords": [
                    {
                        "keywords": ["lettuce"],
                        "location": "COOLER-1"
                    }
                ]
            }
        }

        location = assign_location("FRESH LETTUCE", None, rules)
        assert location == "COOLER-1"

        location = assign_location("fresh lettuce", None, rules)
        assert location == "COOLER-1"

    def test_assign_location_no_match(self):
        """Test that None is returned when no match is found"""
        rules = {
            "location_rules": {
                "keywords": [
                    {
                        "keywords": ["lettuce"],
                        "location": "COOLER-1"
                    }
                ]
            }
        }

        location = assign_location("Unknown Item", None, rules)
        assert location is None

    def test_assign_location_empty_rules(self):
        """Test handling of empty rules"""
        location = assign_location("Some Item", None, {})
        assert location is None

        location = assign_location("Some Item", "Category", {})
        assert location is None
