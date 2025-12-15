"""OrderMaestro renderer for generating formatted inventory outputs"""

from pathlib import Path
from typing import Optional
import pandas as pd
from datetime import datetime

from nebula.inventory.schemas import InventoryPackage, RenderResult


MAX_ROWS = 5000  # Safety guard for maximum rows


class OrderMaestroRenderer:
    """Renderer for OrderMaestro format"""

    def __init__(self):
        """Initialize the OrderMaestro renderer"""
        self.template_dir = Path(__file__).parent.parent / "templates" / "ordermaestro"

    def render(
        self,
        package: InventoryPackage,
        mode: str = "production",
        output_dir: Optional[Path] = None
    ) -> RenderResult:
        """
        Render inventory package to OrderMaestro format

        Args:
            package: InventoryPackage to render
            mode: Rendering mode ("production" or "development")
            output_dir: Output directory for the rendered file

        Returns:
            RenderResult with output file path and metadata
        """
        warnings = []

        # Mode gating
        if mode not in ["production", "development"]:
            raise ValueError(f"Invalid mode: {mode}. Must be 'production' or 'development'")

        # Convert package to DataFrame
        df = package.to_dataframe()

        # Apply MAX_ROWS guard
        if len(df) > MAX_ROWS:
            warnings.append(f"Row count {len(df)} exceeds MAX_ROWS ({MAX_ROWS}). Truncating.")
            df = df.head(MAX_ROWS)

        # Robust ID filling - handle None/NaN/empty strings
        df = self._fill_ids(df)

        # Apply mode-specific transformations
        if mode == "development":
            df = self._apply_development_mode(df)

        # Ensure output directory exists
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        location_code = package.location.code
        output_file = output_dir / f"ordermaestro_{location_code}_{timestamp}.xlsx"

        # Write to Excel
        df.to_excel(output_file, index=False, engine="openpyxl")

        return RenderResult(
            output_file=output_file,
            rows_written=len(df),
            warnings=warnings,
            metadata={
                "mode": mode,
                "location": location_code,
                "timestamp": timestamp
            }
        )

    def _fill_ids(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Robust ID filling - handles None/NaN/empty strings

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with filled IDs
        """
        if "item_code" not in df.columns:
            return df

        # Create a copy to avoid modifying the original
        df = df.copy()

        # Replace None, NaN, and empty strings with generated IDs
        def generate_id(idx, value):
            # Check if value is None, NaN, or empty string
            if pd.isna(value) or value == "" or value is None:
                return f"AUTO_{idx:05d}"
            return value

        df["item_code"] = [
            generate_id(idx, val)
            for idx, val in enumerate(df["item_code"], start=1)
        ]

        return df

    def _apply_development_mode(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply development mode transformations

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with development mode modifications
        """
        # In development mode, add debug columns
        df = df.copy()
        df["_dev_mode"] = True
        df["_row_num"] = range(1, len(df) + 1)

        return df
