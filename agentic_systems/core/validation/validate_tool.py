"""ValidateStagedDataTool per BRD FR-002 and PRD-TRD Section 5.4."""

import re
from datetime import datetime
from typing import Any, Dict, List, Tuple

import pandas as pd

from ..tools import ToolResult


class ValidateStagedDataTool:
    """Validates staged data with basic rules per BRD FR-002.
    
    Implements required field checks and active past graduation rule per
    BRD Section 2.3. Emits row-level validation entries (redacted per BRD Section 2.3):
    {row_index, field, severity, message} - no raw field values per BRD FR-002
    acceptance criteria.
    """
    
    name = "ValidateStagedDataTool"
    
    # Required fields per BRD FR-002
    REQUIRED_FIELDS = ['first_name', 'last_name', 'date_of_birth']
    
    # WA zip code prefixes (common Washington state zip codes)
    # Most WA zips start with 98xxx (Seattle area) or 99xxx (other areas)
    WA_ZIP_PREFIXES = ['98', '99']
    
    def _validate_zip_code_format(self, zip_code: str) -> Tuple[bool, str]:
        """Validate zip code format.
        
        Args:
            zip_code: Zip code string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not zip_code or pd.isna(zip_code):
            return True, ""  # Empty zip is handled by empty field detection
        
        zip_str = str(zip_code).strip()
        
        # Check for invalid patterns
        if zip_str == '00000' or zip_str == '00000-0000':
            return False, "Invalid zip code: all zeros"
        
        # Standard US zip format: 5 digits or 5+4 format (12345-6789)
        zip_pattern = r'^\d{5}(-\d{4})?$'
        if not re.match(zip_pattern, zip_str):
            return False, "Invalid zip code format: must be 5 digits or 5+4 format (e.g., 12345 or 12345-6789)."
        
        # Check for non-numeric characters (except hyphen in ZIP+4)
        if not zip_str.replace('-', '').isdigit():
            return False, "Invalid zip code: contains non-numeric characters"
        
        return True, ""
    
    def _validate_zip_state_consistency(self, zip_code: str, state: str) -> Tuple[bool, str]:
        """Validate zip code matches state (Warning level, not Error).
        
        Args:
            zip_code: Zip code string
            state: State abbreviation (e.g., "WA")
            
        Returns:
            Tuple of (is_consistent, warning_message)
        """
        if not zip_code or pd.isna(zip_code) or not state or pd.isna(state):
            return True, ""  # Skip if either is missing
        
        zip_str = str(zip_code).strip()
        state_str = str(state).strip().upper()
        
        # Extract first 2 digits of zip code
        zip_digits = zip_str.replace('-', '')[:2]
        
        # Check WA zip codes (most start with 98 or 99)
        if state_str == 'WA':
            if not zip_digits.startswith(('98', '99')):
                return False, "Zip code may not match WA state (WA zips typically start with 98 or 99)."
        
        return True, ""
    
    def __call__(self, staged_data: pd.DataFrame) -> ToolResult:
        """Validate staged data and return validation results per BRD FR-002.
        
        Args:
            staged_data: DataFrame from IngestPartnerFileTool containing parsed rows
            
        Returns:
            ToolResult with validation summary counts + row-level list in data
            (in-memory list for tool chaining). Evidence writer serializes validation
            results to outputs/validation_report.csv once (tools return in-memory data only).
        """
        violations = []
        error_count = 0
        warning_count = 0
        
        # Required field validation per BRD FR-002
        for idx, row in staged_data.iterrows():
            # Check required fields
            for field in self.REQUIRED_FIELDS:
                if field not in staged_data.columns:
                    violations.append({
                        'row_index': int(idx),
                        'field': field,
                        'severity': 'Error',
                        'message': f'Required field {field} is missing from file'
                    })
                    error_count += 1
                else:
                    field_value = row[field]
                    # Handle both scalar and Series values
                    if isinstance(field_value, pd.Series):
                        field_value = field_value.iloc[0] if len(field_value) > 0 else None
                    if pd.isna(field_value) or (isinstance(field_value, str) and field_value.strip() == ''):
                        # Row-level validation entry (redacted per BRD Section 2.3)
                        # No raw field values - only metadata: row_index, field, severity, message
                        violations.append({
                            'row_index': int(idx),
                            'field': field,
                            'severity': 'Error',
                            'message': f'Required field {field} is empty'
                        })
                        error_count += 1
            
            # Active past graduation check per BRD Section 2.3 validation rules
            # Check if current_program_status and training exit date columns are present
            # Use current_program_status (not employment_status) for program enrollment status
            program_status_col = 'current_program_status'
            
            # Find training exit date column (may have trailing underscores after normalization)
            exit_date_col = None
            for col in staged_data.columns:
                if 'training' in col.lower() and 'exit' in col.lower() and 'date' in col.lower():
                    exit_date_col = col
                    break
            
            if program_status_col in staged_data.columns and exit_date_col:
                program_status = str(row.get(program_status_col, '')).lower()
                exit_date_str = row.get(exit_date_col)
                
                # Check if participant is marked active past graduation date
                # Look for "active" in program status (case-insensitive)
                if 'active' in program_status and pd.notna(exit_date_str):
                    try:
                        # Try to parse exit_date (handle various formats)
                        if isinstance(exit_date_str, str):
                            # Try common date formats
                            exit_date = None
                            for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y']:
                                try:
                                    exit_date = datetime.strptime(exit_date_str.strip(), fmt)
                                    break
                                except ValueError:
                                    continue
                            if exit_date is None:
                                # If string parsing fails, try pandas to_datetime
                                exit_date = pd.to_datetime(exit_date_str)
                        else:
                            exit_date = pd.to_datetime(exit_date_str)
                        
                        # Check if exit_date has passed (participant should not be active)
                        if exit_date < datetime.now():
                            # Row-level validation entry (redacted per BRD Section 2.3)
                            # No raw field values - only metadata
                            violations.append({
                                'row_index': int(idx),
                                'field': program_status_col,
                                'severity': 'Error',
                                'message': 'Participant marked active past graduation date'
                            })
                            error_count += 1
                    except (ValueError, TypeError):
                        # Date parsing failed - skip this check
                        pass
            
            # Zip code validation
            zip_code_col = 'zip_code'
            state_col = 'state'
            
            if zip_code_col in staged_data.columns:
                zip_value = row.get(zip_code_col)
                # Handle both scalar and Series values
                if isinstance(zip_value, pd.Series):
                    zip_value = zip_value.iloc[0] if len(zip_value) > 0 else None
                
                # Only validate if zip code is not empty (empty is handled by empty field detection)
                if not pd.isna(zip_value) and str(zip_value).strip() != '':
                    # Format validation (Error severity)
                    is_valid_format, format_error = self._validate_zip_code_format(str(zip_value))
                    if not is_valid_format:
                        violations.append({
                            'row_index': int(idx),
                            'field': zip_code_col,
                            'severity': 'Error',
                            'message': format_error
                        })
                        error_count += 1
                    
                    # State/zip consistency validation (Warning severity)
                    if state_col in staged_data.columns:
                        state_value = row.get(state_col)
                        if isinstance(state_value, pd.Series):
                            state_value = state_value.iloc[0] if len(state_value) > 0 else None
                        
                        is_consistent, consistency_warning = self._validate_zip_state_consistency(
                            str(zip_value), str(state_value) if not pd.isna(state_value) else ''
                        )
                        if not is_consistent:
                            violations.append({
                                'row_index': int(idx),
                                'field': zip_code_col,
                                'severity': 'Warning',
                                'message': consistency_warning
                            })
                            warning_count += 1
            
            # Empty field detection (warnings for non-required fields)
            for col in staged_data.columns:
                if col not in self.REQUIRED_FIELDS:
                    col_value = row[col]
                    # Handle both scalar and Series values
                    if isinstance(col_value, pd.Series):
                        col_value = col_value.iloc[0] if len(col_value) > 0 else None
                    if pd.isna(col_value) or (isinstance(col_value, str) and col_value.strip() == ''):
                        violations.append({
                            'row_index': int(idx),
                            'field': col,
                            'severity': 'Warning',
                            'message': f'Optional field {col} is empty'
                        })
                        warning_count += 1
        
        # Return validation summary counts + row-level list in ToolResult.data
        # (in-memory list for tool chaining)
        # Note: Evidence writer serializes validation results to outputs/validation_report.csv
        # once (tools return in-memory data only)
        return ToolResult(
            ok=error_count == 0,
            summary=f"Validation complete: {error_count} errors, {warning_count} warnings",
            data={
                'violations': violations,  # In-memory list for tool chaining
                'error_count': error_count,
                'warning_count': warning_count,
                'total_violations': len(violations)
            },
            warnings=[f"{warning_count} warnings found"] if warning_count > 0 else [],
            blockers=[f"{error_count} errors found"] if error_count > 0 else []
        )

