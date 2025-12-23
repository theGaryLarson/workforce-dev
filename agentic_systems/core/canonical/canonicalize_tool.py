"""CanonicalizeStagedDataTool per BRD FR-003 and PRD-TRD Section 5.4."""

from typing import Any, Dict, List
import re
import pandas as pd

from ..tools import ToolResult


class CanonicalizeStagedDataTool:
    """Transforms validated data to canonical format per BRD FR-003.
    
    Maps staged fields to canonical fields robustly and generates stable POC IDs.
    """
    
    name = "CanonicalizeStagedDataTool"
    
    # Target canonical fields
    CANONICAL_FIELDS = [
        'first_name', 'last_name', 'middle_name', 'date_of_birth',
        'address_1', 'address_2', 'city', 'state', 'zip_code',
        'phone', 'email', 'gender', 'ethnicity', 'race',
        'disability', 'veteran', 'education_level'
    ]

    def _normalize_header(self, h: str) -> str:
        """Normalize header for mapping."""
        s = str(h).strip().lower()
        s = re.sub(r'\s+', ' ', s)
        s = s.replace('â\x80\x99', "'").replace("\u2019", "'")
        return s

    def _get_mapping(self, columns: List[str]) -> Dict[str, str]:
        """Map actual sheet headers to canonical keys."""
        mapping = {}
        
        # Define patterns for matching
        patterns = {
            'first_name': ["first name"],
            'last_name': ["last name"],
            'middle_name': ["middle name"],
            'date_of_birth': ["date of birth"],
            'address_1': ["address 1"],
            'address_2': ["address 2"],
            'city': ["city"],
            'state': ["state"],
            'zip_code': ["zip code"],
            'phone': ["phone"],
            'email': ["email"],
            'gender': ["gender"],
            'ethnicity': ["ethnicity"],
            'race': ["race"],
            'disability': ["disability"],
            'veteran': ["veteran"],
            'education_level': ["education level", "highest completed education"]
        }

        for col in columns:
            norm = self._normalize_header(col)
            for key, keywords in patterns.items():
                if any(k in norm for k in keywords):
                    mapping[col] = key
                    break
        
        return mapping

    def __call__(self, validated_data: pd.DataFrame) -> ToolResult:
        """Canonicalize validated data per BRD FR-003."""
        try:
            canonical_rows = []
            col_mapping = self._get_mapping(list(validated_data.columns))
            
            # Map staged fields to canonical fields
            for idx, row in validated_data.iterrows():
                # Skip blank rows (just in case they weren't caught by validator)
                if row.isna().all() or (row.astype(str).str.strip() == '').all():
                    continue

                canonical_row = {}
                
                # Apply mapping
                for original_col, canonical_key in col_mapping.items():
                    canonical_row[canonical_key] = row.get(original_col)
                
                # Copy any fields that didn't map (for transparency)
                for col in validated_data.columns:
                    if col not in col_mapping:
                        # Clean up header name for new DF
                        clean_col = self._normalize_header(col).replace(' ', '_')
                        canonical_row[clean_col] = row.get(col)
                
                # Generate stable POC ID (P000001, P000002, etc.)
                participant_id = f"P{idx + 1:06d}"
                canonical_row['participant_id'] = participant_id
                
                canonical_rows.append(canonical_row)
            
            # Create canonical DataFrame
            canonical_df = pd.DataFrame(canonical_rows)
            
            return ToolResult(
                ok=True,
                summary=f"Canonicalized {len(canonical_df)} records",
                data={
                    'canonical_dataframe': canonical_df,
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
