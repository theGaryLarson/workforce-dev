"""GeneratePartnerErrorReportTool per BRD FR-012.

Creates Excel file with full row data for rows containing validation errors.
Uses create_error_excel_with_comments for user-friendly Excel format with
color-coding and cell comments. This file contains PII and must be shared
via secure link only per BRD FR-013.
"""

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from ..tools import ToolResult
from .excel_utils import create_error_excel_with_comments


class GeneratePartnerErrorReportTool:
    """Generates error report Excel file with full row data for error rows per BRD FR-012.
    
    Takes validation violations and staged DataFrame, filters to error rows,
    and uses create_error_excel_with_comments to create user-friendly Excel file
    with color-coding, cell comments, and action guidance.
    
    Security Note: This Excel file contains full PII - must be shared via secure link only,
    never via email attachment per BRD FR-013 and BRD Section 2.3.
    """
    
    name = "GeneratePartnerErrorReportTool"
    
    def __call__(
        self,
        staged_dataframe: pd.DataFrame,
        violations: List[Dict[str, Any]],
        output_path: Path,
    ) -> ToolResult:
        """Generate error report Excel file with full row data for error rows.
        
        Uses create_error_excel_with_comments to create Excel file with:
        - Color-coding by severity (Error=red, Warning=yellow, Info=blue)
        - Cell comments with error messages
        - Action Required column with specific guidance
        - Notes column for additional context
        
        Args:
            staged_dataframe: Original DataFrame from ingestion (with all columns)
            violations: List of violation dicts from ValidateStagedDataTool
                       Each dict has: row_index, field, severity, message
            output_path: Path where Excel file should be written (should be .xlsx)
        
        Returns:
            ToolResult with error_report_path in data
        """
        # Ensure output path is .xlsx
        if output_path.suffix != '.xlsx':
            output_path = output_path.with_suffix('.xlsx')
        
        # Extract unique row_index values from violations (filter out -1 for file-level errors)
        error_row_indices = {v['row_index'] for v in violations if v['row_index'] > 1}
        
        if not error_row_indices:
            # No data rows with errors
            # Create empty Excel file with headers only
            staged_dataframe.iloc[:0].to_excel(output_path, index=False, engine='openpyxl')
            return ToolResult(
                ok=True,
                summary="No data rows with errors found - created empty error report",
                data={"error_report_path": str(output_path)},
                warnings=[],
                blockers=[]
            )
        
        # Use create_error_excel_with_comments to generate Excel file with comments and color-coding
        # This provides a user-friendly format for partners to review and correct errors
        create_error_excel_with_comments(
            df=staged_dataframe,
            violations=violations,
            output_path=output_path
        )
        
        # Count error rows
        error_row_count = len(error_row_indices)
        
        return ToolResult(
            ok=True,
            summary=f"Generated error report Excel file with {error_row_count} rows containing errors",
            data={"error_report_path": str(output_path), "error_row_count": error_row_count},
            warnings=[],
            blockers=[]
        )

