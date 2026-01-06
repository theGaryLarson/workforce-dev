"""IngestPartnerFileTool per BRD FR-001 and PRD-TRD Section 5.4."""

import csv
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from ..tools import ToolResult


class IngestPartnerFileTool:
    """Ingests partner files (CSV/Excel) and returns parsed data per BRD FR-001.
    
    Supports CSV and Excel files with encoding detection. Normalizes column names
    and computes file hash for idempotency per PRD-TRD Section 5.4.
    Supports partner-specific parsing configurations for multi-partner support.
    """
    
    name = "IngestPartnerFileTool"
    
    def __call__(self, file_path: str, partner_name: Optional[str] = None, client_id: str = "cfa") -> ToolResult:
        """Parse file and return DataFrame with metadata per BRD FR-001 acceptance criteria.
        
        Args:
            file_path: Path to the partner file (CSV or Excel)
            partner_name: Partner identifier (e.g., "test-partner-1") for partner-specific parsing
            client_id: Client identifier (default: "cfa")
            
        Returns:
            ToolResult with in-memory DataFrame in data for tool chaining.
            Evidence logging will use sanitized metadata only (counts, hash, status).
            Evidence writer will serialize DataFrame to outputs/ later (tools return
            in-memory data only).
        """
        try:
            path = Path(file_path)
            
            # Load partner-specific parsing configuration if partner_name is provided
            parsing_config = None
            if partner_name:
                try:
                    from ...clients.cfa.partners import load_partner_parsing_config
                    parsing_config = load_partner_parsing_config(client_id, partner_name)
                except Exception:
                    # If partner config loading fails, continue with default parsing
                    pass
            
            # Determine encoding preferences from parsing config or use defaults
            encodings = ['utf-8', 'windows-1252', 'latin-1']
            if parsing_config and 'file_structure' in parsing_config:
                file_structure = parsing_config['file_structure']
                if 'encoding_preferences' in file_structure:
                    encodings = file_structure['encoding_preferences']
            
            # Determine header row and data start row from parsing config or use defaults
            header_row = 0  # pandas default
            skiprows = None
            if parsing_config and 'file_structure' in parsing_config:
                file_structure = parsing_config['file_structure']
                header_row = file_structure.get('header_row', 1) - 1  # Convert to 0-based
                data_start_row = file_structure.get('data_start_row', 2)
                if data_start_row > 1:
                    skiprows = list(range(header_row + 1, data_start_row - 1))
            
            # Determine delimiter from parsing config or auto-detect
            delimiter = None
            if parsing_config and 'file_structure' in parsing_config:
                file_structure = parsing_config['file_structure']
                if 'delimiter' in file_structure:
                    delimiter = file_structure['delimiter']
            
            # Parse file per BRD FR-001 acceptance criteria
            if path.suffix.lower() == '.csv':
                # Auto-detect delimiter if not specified in config
                if delimiter is None:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            first_lines = [f.readline() for _ in range(3)]
                        # Use csv.Sniffer for automatic delimiter detection
                        sample = ''.join(first_lines[:3])
                        sniffer = csv.Sniffer()
                        try:
                            delimiter = sniffer.sniff(sample, delimiters=',;\t|').delimiter
                        except Exception:
                            # Fallback: count delimiters in first line
                            if first_lines:
                                semicolon_count = first_lines[0].count(';')
                                comma_count = first_lines[0].count(',')
                                delimiter = ';' if semicolon_count > comma_count else ','
                            else:
                                delimiter = ','  # Default fallback
                    except Exception:
                        delimiter = ','  # Default fallback
                
                # Try multiple encodings per BRD FR-001
                for encoding in encodings:
                    try:
                        read_kwargs = {'encoding': encoding, 'header': header_row, 'sep': delimiter}
                        if skiprows:
                            read_kwargs['skiprows'] = skiprows
                        df = pd.read_csv(file_path, **read_kwargs)
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        if encoding == encodings[-1]:  # Last encoding, re-raise if not UnicodeDecodeError
                            raise
                        continue
                else:
                    return ToolResult(
                        ok=False,
                        summary=f"Failed to decode CSV file with any supported encoding",
                        data={},
                        warnings=[],
                        blockers=[f"Encoding detection failed for {file_path}"]
                    )
            elif path.suffix.lower() in ['.xlsx', '.xls']:
                read_kwargs = {'engine': 'openpyxl', 'header': header_row}
                if skiprows:
                    read_kwargs['skiprows'] = skiprows
                df = pd.read_excel(file_path, **read_kwargs)
            else:
                return ToolResult(
                    ok=False,
                    summary=f"Unsupported file format: {path.suffix}",
                    data={},
                    warnings=[],
                    blockers=[f"File format {path.suffix} not supported. Expected CSV or Excel."]
                )
            
            # Clean up headers (whitespace only) to preserve original sheet names for validator
            df.columns = df.columns.str.strip()
            
            # Apply partner-specific column mappings if parsing config exists
            if parsing_config and 'column_mappings' in parsing_config:
                column_mappings = parsing_config['column_mappings']
                # Rename columns based on partner-specific mappings
                # Map partner column names to canonical field names
                rename_dict = {}
                for partner_col, canonical_field in column_mappings.items():
                    # Find matching column (case-insensitive, handle multi-line headers)
                    for col in df.columns:
                        # Extract first line if multi-line header
                        col_first_line = str(col).split('\n')[0].strip()
                        if col_first_line.lower() == partner_col.lower():
                            rename_dict[col] = canonical_field
                            break
                
                if rename_dict:
                    df = df.rename(columns=rename_dict)
            
            # Preserve zip codes as strings (prevent pandas from converting to float)
            # Find zip code column(s) - may be named 'zip_code', 'zip', etc.
            zip_code_cols = [col for col in df.columns if 'zip' in col.lower()]
            for zip_col in zip_code_cols:
                if zip_col in df.columns:
                    # Convert to string, handling float values (e.g., 98118.0 -> '98118')
                    df[zip_col] = df[zip_col].astype(str).str.replace(r'\.0+$', '', regex=True)
                    # Handle NaN values that became 'nan' string
                    df[zip_col] = df[zip_col].replace('nan', pd.NA)
            
            # Compute file hash for idempotency per PRD-TRD Section 5.4
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            # Return in-memory DataFrame for tool chaining (ToolResult.data holds objects per PRD-TRD Section 5.4)
            # Evidence logging will use sanitized metadata only (counts, hash, status)
            # Evidence writer will serialize DataFrame to outputs/ later (tools return in-memory data only)
            return ToolResult(
                ok=True,
                summary=f"Ingested {len(df)} rows from {file_path}",
                data={
                    "dataframe": df,  # In-memory DataFrame for chaining
                    "row_count": len(df),
                    "columns": list(df.columns),
                    "file_hash": file_hash
                },
                warnings=[],
                blockers=[]
            )
            
        except Exception as e:
            return ToolResult(
                ok=False,
                summary=f"Failed to ingest file {file_path}: {str(e)}",
                data={},
                warnings=[],
                blockers=[f"Ingestion error: {str(e)}"]
            )

