"""Unit tests for ValidateStagedDataTool per updated spreadsheet specifications."""

import pandas as pd
import pytest
from datetime import datetime, timedelta

from agentic_systems.core.tools import ToolResult
from agentic_systems.core.validation.validate_tool import ValidateStagedDataTool


class TestValidateStagedDataTool:
    """Test suite for ValidateStagedDataTool."""

    def test_tool_exists_and_has_name(self):
        """Verify tool class exists and has required attributes."""
        tool = ValidateStagedDataTool()

        assert hasattr(tool, 'name'), "Tool must have 'name' attribute"
        assert tool.name == "ValidateStagedDataTool"
        assert callable(tool), "Tool must be callable"

    def test_header_validation_a_ap(self):
        """Test file-level header validation for A–AP slice."""
        tool = ValidateStagedDataTool()
        
        # Less than 42 columns
        df_small = pd.DataFrame(columns=['First Name', 'Last Name'])
        result = tool(df_small)
        violations = result.data['violations']
        assert any("fewer than 42 columns" in v['message'].lower() for v in violations)
        
        # Required headers missing in A–AP
        headers = [f"Col {i}" for i in range(42)]
        df_missing = pd.DataFrame(columns=headers)
        result = tool(df_missing)
        violations = result.data['violations']
        assert any("Required header \"First Name\" must exist" in v['message'] for v in violations)
        
        # Duplicate headers in A–AP
        headers_dup = ["First Name"] * 42 # Pandas will rename these to First Name.1, etc.
        df_dup = pd.DataFrame(columns=headers_dup)
        result = tool(df_dup)
        dup_errors = [v for v in result.data['violations'] if "duplicate" in v['message'].lower()]
        assert len(dup_errors) > 0

    def test_row_level_termination(self):
        """Test that validation stops at the first row where A–AP are all blank."""
        tool = ValidateStagedDataTool()
        # Create 42 columns
        headers = ["First Name", "Last Name", "Date of Birth (MM/DD/YYYY)", "Address 1", "City", "State", "Zip Code", "Training Start Date \n(MM/DD/YYYY)"]
        headers += [f"Extra {i}" for i in range(42 - len(headers))]
        
        df = pd.DataFrame([
            ["John", "Doe", "01/01/1990", "123 Main St", "Seattle", "WA", "98101", "01/01/2023"] + [""] * 34,
            [""] * 42, # Termination row
            ["Jane", "Smith", "01/01/1990", "456 Oak St", "Seattle", "WA", "98101", "01/01/2023"] + [""] * 34
        ], columns=headers)
        
        result = tool(df)
        violations = result.data['violations']
        
        # Only row 2 (John Doe) should be processed. Row 4 (Jane Smith) should be ignored.
        row_nums = [v['row_index'] for v in violations]
        assert all(rn < 4 for rn in row_nums)

    def test_robust_mapping(self):
        """Test mapping with newlines, smart quotes, and extra whitespace."""
        tool = ValidateStagedDataTool()
        headers = [
            "First\nName", 
            "Date of Birth\n(MM/DD/YYYY)", 
            "Address 1", 
            "Last Name",
            "City", "State", "Zip Code", "Training Start Date"
        ]
        headers += [f"Col {i}" for i in range(42 - len(headers))]
        
        df = pd.DataFrame([
            ["John", "01/01/1990", "123 Main St", "", "Seattle", "WA", "98101", "01/01/2023"] + [""] * 34
        ], columns=headers)
        
        result = tool(df)
        violations = result.data['violations']
        # Should detect missing Last Name using mapping
        assert any("Last Name is required" in v['message'] for v in violations)

    def test_address_validation_strict(self):
        """Test Address 1 restrictions matching the new spec."""
        tool = ValidateStagedDataTool()
        headers = ["First Name", "Last Name", "Date of Birth (MM/DD/YYYY)", "Address 1", "City", "State", "Zip Code", "Training Start Date \n(MM/DD/YYYY)"]
        headers += [f"Col {i}" for i in range(42 - len(headers))]
        
        df = pd.DataFrame([
            ["A", "A", "01/01/1990", "PO Box 123", "C", "S", "Z", "01/01/2023"] + [""] * 34,
            ["B", "B", "01/01/1990", "123 Main St Apt 4", "C", "S", "Z", "01/01/2023"] + [""] * 34,
            ["C", "C", "01/01/1990", "123 Main St Apt. 4", "C", "S", "Z", "01/01/2023"] + [""] * 34,  # With period
            ["D", "D", "01/01/1990", "123 Main St Suite 100", "C", "S", "Z", "01/01/2023"] + [""] * 34,
            ["E", "E", "01/01/1990", "123 Main St #12", "C", "S", "Z", "01/01/2023"] + [""] * 34,
            ["F", "F", "01/01/1990", "51684 Brianna Flats", "C", "S", "Z", "01/01/2023"] + [""] * 34  # Holistic check
        ], columns=headers)
        
        result = tool(df)
        messages = [v['message'] for v in result.data['violations']]
        
        assert any("must not contain a PO Box" in m for m in messages)
        assert any("Apartment/Suite/Unit info must be in Address 2" in m for m in messages)
        # Should catch: Apt 4, Apt. 4, Suite 100, #12, and Flats (via holistic check) = 5 violations
        assert messages.count("Apartment/Suite/Unit info must be in Address 2 (not Address 1).") >= 5

    def test_employment_reverse_check(self):
        """Test that employment details require an employed status."""
        tool = ValidateStagedDataTool()
        headers = ["First Name", "Last Name", "Date of Birth (MM/DD/YYYY)", "Address 1", "City", "State", "Zip Code", "Training Start Date \n(MM/DD/YYYY)", 
                   "Employment Status", "If Employed, Employer Name"]
        headers += [f"Col {i}" for i in range(42 - len(headers))]
        
        df = pd.DataFrame([
            ["A", "A", "01/01/1990", "1", "C", "S", "Z", "01/01/2023", "Still seeking employment in-field", "Some Employer"] + [""] * 32
        ], columns=headers)
        
        result = tool(df)
        violations = result.data['violations']
        assert any("Employment Status must be one of the two “Employed In-field…” options" in v['message'] for v in violations)

    def test_date_validations_no_double_reporting(self):
        """Test that invalid dates don't also report 'required' errors if value is present."""
        tool = ValidateStagedDataTool()
        headers = ["First Name", "Last Name", "Date of Birth (MM/DD/YYYY)", "Address 1", "City", "State", "Zip Code", "Training Start Date \n(MM/DD/YYYY)"]
        headers += [f"Col {i}" for i in range(42 - len(headers))]
        
        df = pd.DataFrame([
            ["A", "A", "invalid-date", "1", "C", "S", "Z", "01/01/2023"] + [""] * 34
        ], columns=headers)
        
        result = tool(df)
        dob_errors = [v for v in result.data['violations'] if "Date of Birth" in v['field']]
        # Should only have "must be a valid date", not "is required"
        assert len(dob_errors) == 1
        assert "must be a valid date" in dob_errors[0]['message']

    def test_valid_case(self):
        """Test a fully valid case."""
        tool = ValidateStagedDataTool()
        headers = ["First Name", "Last Name", "Date of Birth (MM/DD/YYYY)", "Address 1", "City", "State", "Zip Code", "Training Start Date \n(MM/DD/YYYY)", "Current Program Status", "Employment Status"]
        headers += [f"Col {i}" for i in range(42 - len(headers))]
        
        df = pd.DataFrame([
            ["John", "Doe", "01/01/1990", "123 Main St", "Seattle", "WA", "98101", "01/01/2023", "Currently active", "Still seeking employment in-field"] + [""] * 32
        ], columns=headers)
        
        result = tool(df)
        assert result.ok, f"Validation should be OK but got: {result.summary}. Violations: {result.data['violations']}"
