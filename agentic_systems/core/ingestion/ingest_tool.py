"""IngestPartnerFileTool per BRD FR-001 and PRD-TRD Section 5.4."""

import hashlib
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from ..tools import ToolResult


class IngestPartnerFileTool:
    """Ingests partner files (CSV/Excel) and returns parsed data per BRD FR-001.
    
    Supports CSV and Excel files with encoding detection. Normalizes column names
    and computes file hash for idempotency per PRD-TRD Section 5.4.
    """
    
    name = "IngestPartnerFileTool"
    
    def __call__(self, file_path: str) -> ToolResult:
        """Parse file and return DataFrame with metadata per BRD FR-001 acceptance criteria.
        
        Args:
            file_path: Path to the partner file (CSV or Excel)
            
        Returns:
            ToolResult with in-memory DataFrame in data for tool chaining.
            Evidence logging will use sanitized metadata only (counts, hash, status).
            Evidence writer will serialize DataFrame to outputs/ later (tools return
            in-memory data only).
        """
        try:
            path = Path(file_path)
            
            # Parse file per BRD FR-001 acceptance criteria
            if path.suffix.lower() == '.csv':
                # Try multiple encodings per BRD FR-001
                for encoding in ['utf-8', 'windows-1252', 'latin-1']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        break
                    except UnicodeDecodeError:
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
                df = pd.read_excel(file_path, engine='openpyxl')
            else:
                return ToolResult(
                    ok=False,
                    summary=f"Unsupported file format: {path.suffix}",
                    data={},
                    warnings=[],
                    blockers=[f"File format {path.suffix} not supported. Expected CSV or Excel."]
                )
            
            # Normalize column names (lowercase, replace spaces) per BRD FR-001
            df.columns = df.columns.str.lower().str.replace(' ', '_', regex=False)
            # Remove parentheses and their contents (e.g., "(MM/DD/YYYY)" -> "")
            df.columns = df.columns.str.replace(r'\([^)]*\)', '', regex=True)
            # Remove trailing underscores and whitespace
            df.columns = df.columns.str.strip('_').str.strip()
            
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

