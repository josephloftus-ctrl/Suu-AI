"""Template management for Nebula Engine"""

from pathlib import Path
from typing import Optional, List
import openpyxl


class TemplateManager:
    """Manager for loading and validating XLSX templates"""

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize the template manager

        Args:
            template_dir: Optional path to templates directory
        """
        if template_dir is None:
            template_dir = Path(__file__).parent
        self.template_dir = template_dir

    def load_template(self, template_name: str) -> openpyxl.Workbook:
        """
        Load an XLSX template

        Args:
            template_name: Name of the template (without .xlsx extension)

        Returns:
            Loaded openpyxl Workbook

        Raises:
            FileNotFoundError: If template doesn't exist
        """
        template_path = self.template_dir / f"{template_name}.xlsx"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        return openpyxl.load_workbook(template_path)

    def validate_template(self, template_name: str) -> bool:
        """
        Validate that a template exists and is valid

        Args:
            template_name: Name of the template

        Returns:
            True if valid, False otherwise
        """
        try:
            wb = self.load_template(template_name)
            # Basic validation - check if workbook has at least one sheet
            if len(wb.sheetnames) == 0:
                return False
            return True
        except Exception:
            return False

    def list_templates(self, subdirectory: Optional[str] = None) -> List[str]:
        """
        List available templates

        Args:
            subdirectory: Optional subdirectory to search in

        Returns:
            List of template names (without .xlsx extension)
        """
        search_dir = self.template_dir
        if subdirectory:
            search_dir = search_dir / subdirectory

        if not search_dir.exists():
            return []

        templates = []
        for file in search_dir.glob("*.xlsx"):
            # Skip temporary Excel files
            if not file.name.startswith("~$"):
                templates.append(file.stem)

        return sorted(templates)
