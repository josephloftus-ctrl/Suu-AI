"""Nebula CLI - Command-line interface for the kitchen operating system"""

import argparse
import json
import sys
from pathlib import Path

from nebula.engine import NebulaEngine
from nebula.observability import configure_logging


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Nebula Engine - AI-Powered Kitchen Operating System"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Sort command
    sort_parser = subparsers.add_parser("sort", help="Process inventory file")
    sort_parser.add_argument("source", type=Path, help="Source inventory file")
    sort_parser.add_argument("location", help="Location code (e.g., KG001)")
    sort_parser.add_argument(
        "--mode",
        choices=["production", "development"],
        default="production",
        help="Rendering mode"
    )
    sort_parser.add_argument(
        "--output",
        type=Path,
        help="Output directory for exports"
    )

    # Health command
    health_parser = subparsers.add_parser("health", help="Check engine health")

    # Verify templates command
    verify_parser = subparsers.add_parser("verify-templates", help="Verify template files")

    # Tools command (deprecated - keeping for backward compatibility)
    tools_parser = subparsers.add_parser("tools", help="Run utility tools")
    tools_parser.add_argument(
        "tool",
        choices=["verify-templates"],
        help="Tool to run"
    )

    args = parser.parse_args()

    # Configure logging
    configure_logging(level=args.log_level)

    if args.command == "sort":
        engine = NebulaEngine()
        try:
            result = engine.process_inventory(
                source_file=args.source,
                location_code=args.location,
                mode=args.mode,
                output_dir=args.output
            )
            print(f"✓ Successfully processed inventory")
            print(f"  Output: {result.output_file}")
            print(f"  Rows: {result.rows_written}")
            if result.warnings:
                print(f"  Warnings: {len(result.warnings)}")
                for warning in result.warnings[:5]:
                    print(f"    - {warning}")
        except Exception as e:
            print(f"✗ Error processing inventory: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "health":
        engine = NebulaEngine()
        status = engine.health_check()
        print("Nebula Engine Health Check")
        print("=" * 40)
        print(json.dumps(status, indent=2))
        if not all(v for k, v in status.items() if k.endswith("_exists")):
            sys.exit(1)

    elif args.command == "verify-templates":
        from nebula.tools import verify_templates
        result = verify_templates()
        sys.exit(0 if result["success"] else 1)

    elif args.command == "tools":
        if args.tool == "verify-templates":
            from nebula.tools import verify_templates
            result = verify_templates()
            sys.exit(0 if result["success"] else 1)
        else:
            print(f"Unknown tool: {args.tool}", file=sys.stderr)
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
