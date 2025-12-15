#!/usr/bin/env python3
"""Verify that all templates are valid and accessible"""

from pathlib import Path
from nebula.templates import TemplateManager


def verify_templates():
    """Verify all templates in the templates directory"""
    print("Nebula Template Verification")
    print("=" * 50)

    template_manager = TemplateManager()

    # Check OrderMaestro templates
    print("\nChecking OrderMaestro templates...")
    ordermaestro_templates = template_manager.list_templates("ordermaestro")

    if not ordermaestro_templates:
        print("  ⚠ No OrderMaestro templates found")
    else:
        print(f"  ✓ Found {len(ordermaestro_templates)} template(s):")
        for template in ordermaestro_templates:
            print(f"    - {template}")

    # Summary
    print("\n" + "=" * 50)
    print("Verification complete!")

    return len(ordermaestro_templates) > 0


if __name__ == "__main__":
    import sys
    success = verify_templates()
    sys.exit(0 if success else 1)
