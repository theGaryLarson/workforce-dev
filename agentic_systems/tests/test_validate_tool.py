"""Unit tests for ValidateStagedDataTool per PRD-TRD Section 10.1."""

import pandas as pd

from agentic_systems.core.tools import ToolResult
from agentic_systems.core.validation.validate_tool import ValidateStagedDataTool


class TestValidateStagedDataTool:
    """Test suite for ValidateStagedDataTool."""

    def test_tool_exists_and_has_name(self):
        """Verify tool class exists and has required attributes."""
        tool = ValidateStagedDataTool()

        assert hasattr(tool, 'name'), "Tool must have 'name' attribute"
        assert tool.name == "ValidateStagedDataTool"
        assert hasattr(tool, 'REQUIRED_FIELDS'), "Tool must have REQUIRED_FIELDS"
        assert callable(tool), "Tool must be callable"

    def test_required_field_validation(self, sample_dataframe_with_errors):
        """Test required field validation (first_name, last_name, date_of_birth)."""
        tool = ValidateStagedDataTool()
        result = tool(sample_dataframe_with_errors)

        assert isinstance(result, ToolResult), "Must return ToolResult"
        assert 'violations' in result.data, "Result must contain violations list"
        assert not result.ok, "Errors should mark result as not ok"

        violations = result.data['violations']
        assert isinstance(violations, list), "Violations should be a list"

        # Check for required field errors
        required_field_errors = [
            v for v in violations
            if v['field'] in tool.REQUIRED_FIELDS and v['severity'] == 'Error'
        ]
        assert len(required_field_errors) > 0, "Should detect missing required fields"

    def test_row_level_reporting(self, sample_dataframe_with_errors):
        """Test row-level validation reporting (redacted per BRD Section 2.3)."""
        tool = ValidateStagedDataTool()
        result = tool(sample_dataframe_with_errors)

        violations = result.data['violations']

        # Verify row-level entries have correct structure
        for violation in violations:
            assert 'row_index' in violation, "Violation must have row_index"
            assert isinstance(violation['row_index'], int), "row_index must be an int"
            assert 'field' in violation, "Violation must have field"
            assert 'severity' in violation, "Violation must have severity"
            assert 'message' in violation, "Violation must have message"

            # Verify no raw field values (redacted per BRD Section 2.3)
            assert 'value' not in violation, "Violation should not contain raw field values"
            assert violation['severity'] in ['Error', 'Warning'], "Severity must be Error or Warning"

    def test_active_past_graduation_check(self):
        """Test active past graduation date validation rule."""
        # Create DataFrame with active participant past graduation
        past_date = "01/01/2000"
        df = pd.DataFrame({
            'first_name': ['John'],
            'last_name': ['Doe'],
            'date_of_birth': ['01/15/1990'],
            'current_program_status': ['Currently active in program'],
            'training_exit_date____': [past_date]
        })

        tool = ValidateStagedDataTool()
        result = tool(df)

        violations = result.data['violations']

        # Should detect active past graduation error
        active_past_errors = [
            v for v in violations
            if 'active past graduation' in v['message'].lower()
        ]
        assert len(active_past_errors) > 0, "Should detect active past graduation date"
        assert not result.ok, "Errors should mark result as not ok"

    def test_zip_code_validation_integration(self, sample_dataframe):
        """Test zip code validation integration with full validation flow."""
        # Add invalid zip codes to test data
        df = sample_dataframe.copy()
        df.loc[0, 'zip_code'] = '98101.0'  # Float-like string
        df.loc[1, 'zip_code'] = 'invalid'  # Invalid format
        df.loc[2, 'zip_code'] = '60601'  # Valid but wrong state

        tool = ValidateStagedDataTool()
        result = tool(df)

        violations = result.data['violations']
        zip_violations = [v for v in violations if v['field'] == 'zip_code']

        # Should detect zip code format errors
        zip_errors = [v for v in zip_violations if v['severity'] == 'Error']
        assert len(zip_errors) >= 2, "Should detect invalid zip code formats"

        # Should detect state/zip consistency warnings
        zip_warnings = [v for v in zip_violations if v['severity'] == 'Warning']
        assert len(zip_warnings) >= 1, "Should detect zip/state consistency issues"
        assert not result.ok, "Errors should mark result as not ok"

        # Messages should not echo raw zip values
        raw_values = {'98101.0', 'invalid', '60601'}
        for violation in zip_violations:
            for raw_value in raw_values:
                assert raw_value not in violation['message'], "Zip messages should not echo raw values"

    def test_empty_field_warnings(self, sample_dataframe):
        """Test empty field detection (warnings for optional fields)."""
        # Add empty optional fields
        df = sample_dataframe.copy()
        df['middle_name'] = ['', 'Jane', '']
        df['address_2'] = ['', '', '']

        tool = ValidateStagedDataTool()
        result = tool(df)

        violations = result.data['violations']

        # Should generate warnings for empty optional fields
        empty_warnings = [
            v for v in violations
            if v['severity'] == 'Warning' and 'empty' in v['message'].lower()
        ]
        assert len(empty_warnings) > 0, "Should detect empty optional fields"
        assert result.ok, "Warnings should not mark result as failed"

    def test_validation_summary_counts(self, sample_dataframe_with_errors):
        """Test validation summary counts (error_count, warning_count)."""
        tool = ValidateStagedDataTool()
        result = tool(sample_dataframe_with_errors)

        assert 'error_count' in result.data, "Result must contain error_count"
        assert 'warning_count' in result.data, "Result must contain warning_count"
        assert 'total_violations' in result.data, "Result must contain total_violations"

        violations = result.data['violations']
        errors = [v for v in violations if v['severity'] == 'Error']
        warnings = [v for v in violations if v['severity'] == 'Warning']

        assert result.data['error_count'] == len(errors), "Error count should match violations"
        assert result.data['warning_count'] == len(warnings), "Warning count should match violations"
        assert result.data['total_violations'] == len(violations), "Total violations should match list length"
        assert not result.ok, "Errors should mark result as not ok"

    def test_no_errors_on_valid_data(self, sample_dataframe):
        """Test that valid data produces no errors."""
        tool = ValidateStagedDataTool()
        result = tool(sample_dataframe)

        violations = result.data['violations']
        errors = [v for v in violations if v['severity'] == 'Error']

        # Should have no errors for valid required fields
        assert len(errors) == 0, "Valid data should have no errors"
        assert result.ok, "Valid data should mark result as ok"

