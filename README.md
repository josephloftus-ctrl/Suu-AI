# Nebula Engine v0.4.0

**AI-Powered Kitchen Operating System for CulinArt/Compass Group**

Nebula Engine is a comprehensive inventory management and processing system designed specifically for commercial kitchen operations. It automates inventory sorting, location assignment, and order generation with intelligent rules-based processing.

## Features

- **Intelligent Inventory Processing**: Automatically sort and categorize inventory items
- **Location Assignment**: Smart location assignment based on keywords and categories
- **Multiple Renderers**: Support for OrderMaestro and extensible renderer architecture
- **Robust Data Handling**: Handles missing IDs, malformed data, and various file formats
- **Observability**: Comprehensive logging and monitoring capabilities
- **Template Management**: Validate and manage XLSX templates
- **CLI Interface**: Full-featured command-line interface
- **Integration Testing**: Comprehensive test suite with pipeline integration tests

## Installation

### From Source

```bash
git clone https://github.com/josephloftus-ctrl/Suu-AI.git
cd Suu-AI
pip install -e .
```

### Dependencies

- Python >= 3.10
- pandas >= 2.0.0
- openpyxl >= 3.1.0
- pydantic >= 2.0.0

## Quick Start

### Process Inventory

```bash
# Process inventory file for location KG001
nebula sort imports/sysco_test.csv KG001

# Process with development mode (includes debug columns)
nebula sort imports/sysco_test.csv KG001 --mode development

# Specify custom output directory
nebula sort imports/sysco_test.csv KG001 --output /path/to/output
```

### Check System Health

```bash
nebula health
```

### Verify Templates

```bash
nebula verify-templates
```

### Enable Logging

```bash
# Set log level to DEBUG
nebula --log-level DEBUG sort imports/sysco_test.csv KG001
```

## CLI Commands

### `nebula sort`

Process inventory file and generate sorted output.

**Usage:**
```bash
nebula sort <source_file> <location_code> [options]
```

**Arguments:**
- `source_file`: Path to source inventory file (CSV or Excel)
- `location_code`: Location identifier (e.g., "KG001")

**Options:**
- `--mode {production,development}`: Rendering mode (default: production)
- `--output PATH`: Custom output directory

**Example:**
```bash
nebula sort imports/sysco_test.csv KG001 --mode production
```

### `nebula health`

Check engine health and configuration status.

**Usage:**
```bash
nebula health
```

**Output:**
```json
{
  "engine": "ok",
  "config_dir": "/path/to/nebula/config",
  "config_exists": true,
  "renderer": "ok",
  "inventory_rules_exists": true
}
```

### `nebula verify-templates`

Verify that all templates are valid and accessible.

**Usage:**
```bash
nebula verify-templates
```

### Global Options

- `--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}`: Set logging level (default: INFO)

## Architecture

### Core Components

#### 1. Engine (`nebula/engine.py`)

The main facade for Nebula operations. Handles:
- Source file validation
- Inventory package building
- Rendering coordination
- Logging and observability

**Key Methods:**
- `process_inventory()`: Main processing pipeline
- `health_check()`: System health verification
- `_validate_source_file()`: Input validation
- `_build_inventory_package()`: Package construction

#### 2. Inventory Module (`nebula/inventory/`)

**Schemas (`schemas.py`):**
- `InventoryRow`: Single inventory item
- `InventoryPackage`: Complete inventory package
- `LocationProfile`: Location configuration
- `RenderResult`: Rendering output metadata

**Core Sorter (`core_sorter.py`):**
- `build_inventory_package()`: Build inventory from source
- `assign_location()`: Keyword/category-based location assignment

#### 3. Renderers (`nebula/renderers/`)

**OrderMaestro Renderer (`ordermaestro.py`):**
- Mode gating (production/development)
- Robust ID filling (handles None/NaN/empty strings)
- 5000 row safety guard
- Excel output generation

#### 4. Templates (`nebula/templates/`)

**Template Manager:**
- Load and validate XLSX templates
- List available templates
- Template integrity checking

#### 5. Observability (`nebula/observability.py`)

**Logging Functions:**
- `configure_logging()`: Configure logging system
- `get_logger()`: Get module logger

**Features:**
- Console and file logging
- Configurable log levels
- Structured logging format

#### 6. Tools (`nebula/tools/`)

**Utilities:**
- `verify_templates()`: Template verification tool

### Configuration

#### Inventory Rules (`nebula/config/inventory_rules.json`)

Define location assignment rules based on categories and keywords:

```json
{
  "location_rules": {
    "categories": [
      {"category": "Produce", "location": "COOLER-1"},
      {"category": "Dairy", "location": "COOLER-2"}
    ],
    "keywords": [
      {"keywords": ["lettuce", "tomato"], "location": "COOLER-1"}
    ]
  }
}
```

#### District Map (`nebula/data/district_map_ken_gruber_v1.json`)

Map location codes to facility information:

```json
{
  "KG001": {
    "name": "Central Kitchen Alpha",
    "district": "District 1",
    "region": "Northeast",
    "type": "Production Kitchen"
  }
}
```

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=nebula

# Run specific test file
pytest tests/test_integration.py -v
```

### Test Structure

- `test_engine.py`: Engine core functionality (4 tests)
- `test_core_sorter.py`: Sorting and location assignment (6 tests)
- `test_integration.py`: Full pipeline integration (9 tests)

### Development Mode

Development mode adds debug columns to output:
- `_dev_mode`: Boolean flag
- `_row_num`: Row number for tracking

```bash
nebula sort imports/sysco_test.csv KG001 --mode development
```

## API Usage

### Python API

```python
from pathlib import Path
from nebula.engine import NebulaEngine

# Initialize engine
engine = NebulaEngine()

# Process inventory
result = engine.process_inventory(
    source_file=Path("imports/sysco_test.csv"),
    location_code="KG001",
    mode="production"
)

print(f"Processed {result.rows_written} rows")
print(f"Output: {result.output_file}")
```

### Custom Configuration

```python
from pathlib import Path
from nebula.engine import NebulaEngine

# Use custom config directory
engine = NebulaEngine(config_dir=Path("/path/to/config"))
```

### Observability

```python
from nebula.observability import configure_logging, get_logger

# Configure logging
configure_logging(level="DEBUG", log_file=Path("nebula.log"))

# Get logger for your module
logger = get_logger(__name__)
logger.info("Processing started")
```

## File Formats

### Supported Input Formats

- **CSV** (`.csv`)
- **Excel** (`.xlsx`, `.xls`)

### Expected CSV Columns

- `item_code`: Item identifier (SKU)
- `description`: Item description
- `category`: Item category (optional)
- `quantity`: Quantity (optional)
- `unit`: Unit of measure (optional)

### Output Format

Excel (`.xlsx`) with assigned locations and metadata.

## Performance

### Capacity

- **Max Rows**: 5,000 rows per file (safety guard)
- **Processing Speed**: ~1,000 rows/second
- **Memory Usage**: ~50MB for typical workload

### Optimization

- Bulk processing for large datasets
- Efficient pandas operations
- Minimal memory footprint

## Troubleshooting

### Common Issues

**Issue**: File not found error
```bash
FileNotFoundError: Source file not found: /path/to/file.csv
```
**Solution**: Verify file path and permissions

**Issue**: Unsupported file format
```bash
ValueError: Unsupported file format: .txt
```
**Solution**: Use CSV or Excel format

**Issue**: Template verification fails
```bash
⚠ No OrderMaestro templates found
```
**Solution**: Add templates to `nebula/templates/ordermaestro/`

## Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/josephloftus-ctrl/Suu-AI.git
cd Suu-AI

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linter
ruff check nebula/
```

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: https://github.com/josephloftus-ctrl/Suu-AI/issues
- Email: nebula@culinart.com

## Changelog

### v0.4.0 (Current)
- Added observability module with comprehensive logging
- Added source file validation
- Created nebula/tools/ module with verify_templates
- Added verify-templates CLI subcommand
- Added integration test suite (9 tests)
- Enhanced CLI with --log-level option
- Updated package metadata and includes

### v0.3.0
- Initial release
- Core inventory processing
- OrderMaestro renderer
- Location assignment system
- CLI interface
- Basic test suite
