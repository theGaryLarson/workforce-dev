"""CollectWSACAggregatesTool per BRD FR-004 and PRD-TRD Section 5.4.

Collects aggregates from partner data for submission to WSAC.
Wraparound services mappings are imported from rules.py per BRD Section 2.3 and PRD-TRD Section 5.4.

This tool collects aggregate data (participants, enrollments, employment, wraparound services)
from partner data to ensure accuracy before submission to WSAC. It does not compare against
WSAC prior-quarter data - it only collects aggregates from the current partner submission.
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from ..tools import ToolResult
from ...clients.cfa.rules import (
    WRAPAROUND_SERVICE_CODES,
    WRAPAROUND_SERVICE_NAMES,
    WRAPAROUND_SERVICE_TYPES
)


class CollectWSACAggregatesTool:
    """Collects aggregates from partner data for submission to WSAC.
    
    Per BRD FR-004, this tool collects participant, enrollment, employment, and wraparound
    services aggregates from partner data to ensure accuracy before submission to WSAC.
    
    Wraparound services mappings are imported from rules.py per BRD Section 2.3 and
    PRD-TRD Section 5.4 (business rules belong in rules.py).
    """
    
    name = "CollectWSACAggregatesTool"
    
    def __call__(
        self,
        partner_dataframe: pd.DataFrame,
        quarter: str,
        year: int,
        wraparound_funding: Optional[Dict[str, Dict[str, float]]] = None
    ) -> ToolResult:
        """Collect aggregates from partner data for WSAC submission.
        
        Args:
            partner_dataframe: DataFrame from partner data (from IngestPartnerFileTool or ValidateStagedDataTool)
            quarter: Quarter identifier (e.g., "Q1") for logging and identification
            year: Year for logging and identification
            wraparound_funding: Optional dictionary with GJC and non-GJC funds spent per service type.
                Format: {"transportation": {"gjc": 5000.00, "non_gjc": 1000.00}, ...}
                If not provided, funding amounts will be None in aggregates output.
        
        Returns:
            ToolResult with partner aggregates ready for WSAC submission
        """
        try:
            # Validate partner data
            if partner_dataframe is None or len(partner_dataframe) == 0:
                return ToolResult(
                    ok=False,
                    summary="Partner DataFrame is empty or None",
                    data={},
                    warnings=[],
                    blockers=["Partner DataFrame is empty or None"]
                )
            
            # Calculate partner aggregates
            aggregates = self._calculate_partner_aggregates(
                partner_dataframe,
                wraparound_funding
            )
            
            # Build summary
            summary = (
                f"Collected aggregates: {aggregates.get('total_participants', 0)} participants, "
                f"{aggregates.get('total_enrollments', 0)} enrollments, "
                f"{aggregates.get('total_employment_placements', 0)} employment placements "
                f"for {quarter} {year}"
            )
            
            return ToolResult(
                ok=True,
                summary=summary,
                data={
                    "aggregates": aggregates,
                    "quarter": quarter,
                    "year": year
                },
                warnings=[],
                blockers=[]
            )
            
        except Exception as e:
            return ToolResult(
                ok=False,
                summary=f"Error collecting aggregates: {str(e)}",
                data={},
                warnings=[],
                blockers=[f"Aggregation error: {str(e)}"]
            )
    
    def _calculate_partner_aggregates(
        self,
        df: pd.DataFrame,
        wraparound_funding: Optional[Dict[str, Dict[str, float]]] = None
    ) -> Dict[str, Any]:
        """Calculate aggregates from partner DataFrame."""
        # Find column names (flexible matching)
        first_name_col = self._find_column(df, ["First Name", "first name", "first_name"])
        last_name_col = self._find_column(df, ["Last Name", "last name", "last_name"])
        dob_col = self._find_column(df, ["Date of Birth", "date of birth", "date_of_birth", "DOB", "dob"])
        status_col = self._find_column(df, ["Current Program Status", "current program status", "status"])
        employment_col = self._find_column(df, ["Employment Status", "employment status", "employment_status"])
        wraparound_col = self._find_column(df, ["Wraparound services provided this quarter", "wraparound"])
        
        # Total participants (unique by First Name + Last Name + DOB)
        if first_name_col and last_name_col and dob_col:
            participant_key = df[first_name_col].astype(str) + "|" + \
                            df[last_name_col].astype(str) + "|" + \
                            df[dob_col].astype(str)
            total_participants = participant_key.nunique()
        else:
            # Fallback: count rows
            total_participants = len(df)
        
        # Total enrollments (each row is an enrollment)
        total_enrollments = len(df)
        
        # Total employment placements
        total_employment_placements = 0
        if employment_col:
            employment_values = df[employment_col].astype(str).str.lower()
            total_employment_placements = employment_values.str.contains(
                "employed", case=False, na=False
            ).sum()
        
        # Status breakdowns
        status_breakdown = {"active": 0, "graduated": 0, "withdrawn": 0}
        if status_col:
            status_values = df[status_col].astype(str).str.lower()
            status_breakdown["active"] = status_values.str.contains(
                "active|currently active", case=False, na=False
            ).sum()
            status_breakdown["graduated"] = status_values.str.contains(
                "graduated|completed", case=False, na=False
            ).sum()
            status_breakdown["withdrawn"] = status_values.str.contains(
                "withdrawn|terminated", case=False, na=False
            ).sum()
        
        # Employment status breakdowns
        employment_status_breakdown = {}
        if employment_col:
            employment_counts = df[employment_col].value_counts().to_dict()
            employment_status_breakdown = {
                str(k).lower().replace(" ", "_"): int(v)
                for k, v in employment_counts.items()
            }
        
        # Wraparound services aggregates
        wraparound_services = self._calculate_wraparound_services(
            df,
            wraparound_col,
            wraparound_funding
        )
        
        return {
            "total_participants": int(total_participants),
            "total_enrollments": int(total_enrollments),
            "total_employment_placements": int(total_employment_placements),
            "status_breakdown": status_breakdown,
            "employment_status_breakdown": employment_status_breakdown,
            "wraparound_services": wraparound_services
        }
    
    def _calculate_wraparound_services(
        self,
        df: pd.DataFrame,
        wraparound_col: Optional[str],
        wraparound_funding: Optional[Dict[str, Dict[str, float]]] = None
    ) -> Dict[str, Any]:
        """Calculate wraparound services aggregates using mappings from rules.py."""
        # Initialize usage counts for all service types
        usage_counts = {service_type: 0 for service_type in WRAPAROUND_SERVICE_TYPES}
        
        # Parse wraparound services column if available
        if wraparound_col and wraparound_col in df.columns:
            for idx, row in df.iterrows():
                service_codes_str = str(row[wraparound_col]) if pd.notna(row[wraparound_col]) else ""
                
                if service_codes_str and service_codes_str.strip():
                    # Parse letter codes (e.g., "a,b,c" or "a,e,g")
                    codes = [c.strip().lower() for c in service_codes_str.split(",")]
                    
                    for code in codes:
                        # Map code to service type using WRAPAROUND_SERVICE_CODES from rules.py
                        service_type = WRAPAROUND_SERVICE_CODES.get(code)
                        
                        if service_type and service_type in usage_counts:
                            usage_counts[service_type] += 1
        
        # Initialize funding amounts
        gjc_funds_spent = {service_type: None for service_type in WRAPAROUND_SERVICE_TYPES}
        non_gjc_funds_spent = {service_type: None for service_type in WRAPAROUND_SERVICE_TYPES}
        
        # Populate funding amounts if provided
        if wraparound_funding:
            for service_type in WRAPAROUND_SERVICE_TYPES:
                if service_type in wraparound_funding:
                    funding_data = wraparound_funding[service_type]
                    gjc_funds_spent[service_type] = funding_data.get("gjc")
                    non_gjc_funds_spent[service_type] = funding_data.get("non_gjc")
        
        return {
            "usage_counts": usage_counts,
            "gjc_funds_spent": gjc_funds_spent,
            "non_gjc_funds_spent": non_gjc_funds_spent
        }
    
    
    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """Find column by trying multiple possible names (case-insensitive, handles multi-line headers).
        
        Normalizes column names by removing newlines and extra whitespace for matching.
        This handles multi-line headers like "Wraparound services provided this quarter\nList all letters..."
        """
        # Normalize all column names (remove newlines, normalize whitespace) for matching
        normalized_columns = {}
        for col in df.columns:
            # Normalize: lowercase, remove newlines, collapse whitespace
            normalized = ' '.join(str(col).lower().replace('\n', ' ').split())
            normalized_columns[normalized] = col
        
        for name in possible_names:
            # Normalize search term the same way
            normalized_search = ' '.join(name.lower().replace('\n', ' ').split())
            
            # Try exact match first
            if normalized_search in normalized_columns:
                return normalized_columns[normalized_search]
            
            # Try partial match (search term is contained in column name)
            for normalized_col, original_col in normalized_columns.items():
                if normalized_search in normalized_col:
                    return original_col
        
        return None

