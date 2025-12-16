"""Template verification utility for Nebula Engine"""

from pathlib import Path
from typing import Dict, List
from nebula.templates import TemplateManager


def verify_templates(verbose: bool = True) -> Dict[str, any]:
    """
    Verify all templates in the templates directory

    Args:
        verbose: If True, print detailed output

    Returns:
        Dictionary with verification results
    """
    results = {
        "success": True,
        "templates_found": 0,
        "templates_by_type": {},
        "errors": []
    }

    if verbose:
        print("Nebula Template Verification")
        print("=" * 50)

    template_manager = TemplateManager()

    # Check OrderMaestro templates
    if verbose:
        print("\nChecking OrderMaestro templates...")

    try:
        ordermaestro_templates = template_manager.list_templates("ordermaestro")
        results["templates_by_type"]["ordermaestro"] = len(ordermaestro_templates)
        results["templates_found"] += len(ordermaestro_templates)

        if not ordermaestro_templates:
            if verbose:
                print("  ⚠ No OrderMaestro templates found")
        else:
            if verbose:
                print(f"  ✓ Found {len(ordermaestro_templates)} template(s):")
                for template in ordermaestro_templates:
                    print(f"    - {template}")
    except Exception as e:
        results["errors"].append(f"OrderMaestro verification failed: {e}")
        results["success"] = False
        if verbose:
            print(f"  ✗ Error: {e}")

    # Summary
    if verbose:
        print("\n" + "=" * 50)
        if results["success"]:
            print(f"✓ Verification complete! Found {results['templates_found']} template(s)")
        else:
            print("✗ Verification failed with errors")
            for error in results["errors"]:
                print(f"  - {error}")

    return results


if __name__ == "__main__":
    import sys
    result = verify_templates()
    sys.exit(0 if result["success"] else 1)
