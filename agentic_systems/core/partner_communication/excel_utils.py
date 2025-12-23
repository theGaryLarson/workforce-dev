"""Utility functions for creating Excel files with error comments.

This module provides utilities for generating Excel files with cell comments
for validation errors. Used by:
- GeneratePartnerErrorReportTool in Part 3 POC
- FR-012 review worksheet generation for human review (BRD Section 3.13)
"""

from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from openpyxl import load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import PatternFill


# Severity-based fill colors per FR-012 (color-coding by severity)
ERROR_FILL = PatternFill(patternType="solid", fgColor="FFC7CE")  # Light red
WARNING_FILL = PatternFill(patternType="solid", fgColor="FFEB9C")  # Light yellow
INFO_FILL = PatternFill(patternType="solid", fgColor="BDD7EE")  # Light blue


def _get_action_guidance(message: str, severity: str) -> str:
    """Generate action guidance based on error message and severity.
    
    Provides specific guidance for common validation error types per FR-012.
    """
    message_lower = message.lower()
    
    # Required field errors
    if 'required' in message_lower or 'missing' in message_lower:
        return "Provide the required value for this field"
    
    # Date validation errors
    if 'date' in message_lower and ('invalid' in message_lower or 'format' in message_lower):
        return "Enter a valid date in MM/DD/YYYY format"
    if 'date' in message_lower and 'earlier' in message_lower:
        return "Date must be earlier than today"
    if 'date' in message_lower and 'after' in message_lower:
        return "Exit date must be on or after start date"
    
    # Address validation errors
    if 'address' in message_lower and ('apartment' in message_lower or 'suite' in message_lower or 'unit' in message_lower):
        return "Move apartment/suite/unit information to Address 2 field"
    if 'address' in message_lower and 'po box' in message_lower:
        return "PO Box addresses are not allowed in Address 1"
    
    # Status validation errors
    if 'status' in message_lower and 'withdrawn' in message_lower:
        return "Provide noncompletion reason when status is Withdrawn/terminated"
    if 'status' in message_lower and 'graduated' in message_lower:
        return "Provide completion type and exit date when status is Graduated/completed"
    
    # Employment validation errors
    if 'employment' in message_lower and 'status' in message_lower:
        return "Select appropriate employment status or provide required employment details"
    if 'employment' in message_lower and ('name' in message_lower or 'type' in message_lower):
        return "Provide all required employment information when employment status is set"
    
    # Default guidance based on severity
    if severity == 'Error':
        return "Correct this error before processing can continue"
    elif severity == 'Warning':
        return "Review and correct if applicable"
    else:
        return "Review for accuracy"


def create_error_excel_with_comments(
    df: pd.DataFrame,
    violations: List[Dict],
    output_path: Path,
    col_map: Dict[str, str] = None
) -> None:
    """Create an Excel file with rows containing errors and cell comments.
    
    This function creates an Excel file containing only rows with validation errors,
    with cell comments added to cells that have errors. The comments contain the
    error message for that specific field.
    
    Implements FR-012 requirements for review worksheet generation:
    - Color-coding by severity (Error=red, Warning=yellow, Info=blue)
    - Action Required column with specific guidance
    - Notes column for additional context
    
    Args:
        df: Original DataFrame with all data (must include header row)
        violations: List of violation dicts with 'row_index', 'field', 'message', 'severity'
        output_path: Path where Excel file should be saved
        col_map: Optional mapping from canonical keys to sheet headers.
                 If None, will try to match by field name directly.
                 This is used to map field names in violations to DataFrame columns.
    
    Returns:
        None (writes file to output_path)
    
    Note:
        - Row indices in violations are 1-based (row_index 2 = first data row)
        - Header errors (row_index == 1) are not included in the Excel file
        - Cells are color-coded by severity per FR-012: Error=red, Warning=yellow, Info=blue
        - Cell comments contain the error message for that specific field
        - The Excel file includes all original columns plus error metadata columns:
          - _error_fields: Comma-separated list of fields with errors
          - _error_messages: Semicolon-separated list of error messages
          - _severity: Highest severity level for the row
          - Action Required: Specific guidance for correcting the error (per FR-012)
          - Notes: Additional context column (empty by default, can be populated)
    
    Use Cases:
        - Part 3 POC: GeneratePartnerErrorReportTool creates partner error reports
        - FR-012: Generate review worksheet for human review with color-coding and action guidance
    """
    # Filter to rows with errors (row_index > 1, since row_index 1 is header errors)
    error_row_indices = {v['row_index'] for v in violations if v['row_index'] > 1}
    
    if not error_row_indices:
        # No data rows with errors, create empty file with headers only
        df.iloc[:0].to_excel(output_path, index=False, engine='openpyxl')
        return
    
    # Get rows with errors (convert row_index to 0-based index: row_index 2 -> index 0)
    # row_index 2 = first data row = DataFrame index 0
    error_indices = [idx - 2 for idx in error_row_indices if idx >= 2]
    error_df = df.iloc[error_indices].copy()
    
    # Add error metadata columns
    # Group violations by row_index for aggregation
    violations_by_row = {}
    for v in violations:
        if v['row_index'] > 1:  # Skip header errors
            row_idx = v['row_index']
            if row_idx not in violations_by_row:
                violations_by_row[row_idx] = []
            violations_by_row[row_idx].append(v)
    
    # Add aggregated error columns per FR-012 requirements
    error_fields_list = []
    error_messages_list = []
    severity_list = []
    action_required_list = []
    notes_list = []
    
    for orig_row_idx in sorted(error_row_indices):
        if orig_row_idx >= 2:
            row_violations = violations_by_row.get(orig_row_idx, [])
            fields = [v['field'] for v in row_violations]
            messages = [v['message'] for v in row_violations]
            severities = [v.get('severity', 'Error') for v in row_violations]
            
            error_fields_list.append(', '.join(fields))
            error_messages_list.append('; '.join(messages))
            
            # Highest severity: Error > Warning > Info
            if 'Error' in severities:
                highest_severity = 'Error'
            elif 'Warning' in severities:
                highest_severity = 'Warning'
            else:
                highest_severity = 'Info'
            severity_list.append(highest_severity)
            
            # Generate action guidance from first violation (most critical)
            primary_violation = row_violations[0]
            action_guidance = _get_action_guidance(
                primary_violation['message'],
                primary_violation.get('severity', 'Error')
            )
            action_required_list.append(action_guidance)
            
            # Notes column (empty by default, can be populated by caller if needed)
            notes_list.append('')
    
    # Add error metadata columns per FR-012 (color-coding, action required, notes)
    error_df['_error_fields'] = error_fields_list
    error_df['_error_messages'] = error_messages_list
    error_df['_severity'] = severity_list
    error_df['Action Required'] = action_required_list
    error_df['Notes'] = notes_list
    
    # Write to Excel first
    error_df.to_excel(output_path, index=False, engine='openpyxl')
    
    # Load workbook to add comments
    wb = load_workbook(output_path)
    ws = wb.active
    
    # Create a mapping from field name to column index
    # Field names in violations are the actual sheet headers
    field_to_col = {}
    for col_idx, header in enumerate(df.columns, start=1):
        field_to_col[str(header)] = col_idx
    
    # Map original row indices to Excel row numbers
    # Excel row 1 = header, Excel row 2 = first data row
    # Original row_index 2 = first data row = Excel row 2
    excel_row_map = {}  # Maps original row_index to Excel row number
    excel_row = 2  # Start after header row
    for orig_idx in sorted(error_row_indices):
        if orig_idx >= 2:
            excel_row_map[orig_idx] = excel_row
            excel_row += 1
    
    # Add comments and color-coding by severity per FR-012
    for orig_row_idx, row_violations in violations_by_row.items():
        excel_row = excel_row_map.get(orig_row_idx)
        if not excel_row:
            continue
            
        for violation in row_violations:
            field_name = violation['field']
            message = violation['message']
            severity = violation.get('severity', 'Error')
            
            # Find column for this field
            col_idx = field_to_col.get(field_name)
            if col_idx:
                cell = ws.cell(row=excel_row, column=col_idx)
                
                # Add comment with error message
                comment = Comment(message, "Validation Tool")
                cell.comment = comment
                
                # Color-code by severity per FR-012 (Error=red, Warning=yellow, Info=blue)
                if severity == 'Error':
                    cell.fill = ERROR_FILL
                elif severity == 'Warning':
                    cell.fill = WARNING_FILL
                elif severity == 'Info':
                    cell.fill = INFO_FILL
    
    # Save workbook
    wb.save(output_path)

