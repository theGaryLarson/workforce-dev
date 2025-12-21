"""CanonicalizeStagedDataTool per BRD FR-003 and PRD-TRD Section 5.4."""

from typing import Any, Dict

import pandas as pd

from ..tools import ToolResult


class CanonicalizeStagedDataTool:
    """Transforms validated data to canonical format per BRD FR-003.
    
    Maps staged fields to canonical fields and generates stable POC IDs.
    Simple ID generation for POC (can be replaced with PostgreSQL later).
    """
    
    name = "CanonicalizeStagedDataTool"
    
    # Field mapping from staged to canonical format per BRD FR-003
    FIELD_MAPPING = {
        'first_name': 'first_name',
        'last_name': 'last_name',
        'middle_name': 'middle_name',
        'date_of_birth': 'date_of_birth',
        'address_1': 'address_1',
        'address_2': 'address_2',
        'city': 'city',
        'state': 'state',
        'zip_code': 'zip_code',
        'phone': 'phone',
        'email': 'email',
        'gender': 'gender',
        'ethnicity': 'ethnicity',
        'race': 'race',
        'disability': 'disability',
        'veteran': 'veteran',
        'education_level': 'education_level',
    }
    
    def __call__(self, validated_data: pd.DataFrame) -> ToolResult:
        """Canonicalize validated data per BRD FR-003.
        
        Args:
            validated_data: DataFrame from IngestPartnerFileTool containing validated rows
            
        Returns:
            ToolResult with canonical rows + counts in data (in-memory DataFrame for
            tool chaining). Evidence writer serializes canonical data to outputs/canonical.csv
            once (tools return in-memory data only) per BRD FR-011.
        """
        try:
            canonical_rows = []
            
            # Map staged fields to canonical fields per BRD FR-003
            for idx, row in validated_data.iterrows():
                canonical_row = {}
                
                # Map known fields
                for staged_field, canonical_field in self.FIELD_MAPPING.items():
                    if staged_field in validated_data.columns:
                        canonical_row[canonical_field] = row.get(staged_field)
                
                # Copy any additional fields that don't need mapping
                for col in validated_data.columns:
                    if col not in self.FIELD_MAPPING:
                        canonical_row[col] = row.get(col)
                
                # Generate stable POC ID (P000001, P000002, etc.)
                # Simple ID generation for POC (can be replaced with PostgreSQL later)
                participant_id = f"P{idx + 1:06d}"
                canonical_row['participant_id'] = participant_id
                
                canonical_rows.append(canonical_row)
            
            # Create canonical DataFrame
            canonical_df = pd.DataFrame(canonical_rows)
            
            # Return canonical rows + counts in ToolResult.data (in-memory DataFrame for tool chaining)
            # Note: Evidence writer serializes canonical data to outputs/canonical.csv once
            # (tools return in-memory data only) per BRD FR-011
            return ToolResult(
                ok=True,
                summary=f"Canonicalized {len(canonical_df)} records",
                data={
                    'canonical_dataframe': canonical_df,  # In-memory DataFrame for chaining
                    'record_count': len(canonical_df)
                },
                warnings=[],
                blockers=[]
            )
            
        except Exception as e:
            return ToolResult(
                ok=False,
                summary=f"Failed to canonicalize data: {str(e)}",
                data={},
                warnings=[],
                blockers=[f"Canonicalization error: {str(e)}"]
            )

