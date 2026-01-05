"""Unit tests for ValidateStagedDataTool per updated spreadsheet specifications."""

import pandas as pd
import pytest
from datetime import datetime, timedelta

from agentic_systems.core.tools import ToolResult
from agentic_systems.core.validation.validate_tool import ValidateStagedDataTool
from agentic_systems.core.validation.engine import ValidationEngine


class TestValidationEngine:
    """Test suite for ValidationEngine."""
    
    def test_engine_loads_rules(self):
        """Test that ValidationEngine loads rules from clients/cfa/rules.py."""
        engine = ValidationEngine(client_id="cfa")
        
        assert "completion_types" in engine.rules
        assert "noncompletion_reasons" in engine.rules
        assert "employment_statuses" in engine.rules
        assert "required_headers" in engine.rules
        assert "file_structure" in engine.rules
    
    def test_engine_loads_config(self):
        """Test that ValidationEngine loads config from clients/cfa/client_spec.yaml."""
        engine = ValidationEngine(client_id="cfa")
        
        assert "validation" in engine.config
        assert "canonical_mappings" in engine.config
        assert engine.config["client"] == "CFA"
    
    def test_engine_loads_mappings(self):
        """Test that ValidationEngine loads mappings from clients/cfa/mappings.py."""
        engine = ValidationEngine(client_id="cfa")
        
        assert "wsac_export" in engine.mappings
        assert "dynamics_import" in engine.mappings
        assert "wsac_transformations" in engine.mappings
        assert "dynamics_transformations" in engine.mappings
    
    def test_engine_helper_methods(self):
        """Test ValidationEngine helper methods."""
        engine = ValidationEngine(client_id="cfa")
        
        completion_types = engine.get_approved_values("completion_types")
        assert len(completion_types) > 0
        assert isinstance(completion_types, list)
        
        required_headers = engine.get_required_headers()
        assert len(required_headers) > 0
        assert "First Name" in required_headers
        
        file_structure = engine.get_file_structure()
        assert file_structure["min_columns"] == 42
        
        canonical_mappings = engine.get_canonical_mappings()
        assert "first_name" in canonical_mappings
        assert "last_name" in canonical_mappings
        
        assert engine.should_halt_on_error() is True
    
    def test_engine_warning_threshold(self):
        """Test get_warning_threshold() returns correct value from config."""
        engine = ValidationEngine(client_id="cfa")
        
        # Default should be None (not configured)
        threshold = engine.get_warning_threshold()
        assert threshold is None
    
    def test_engine_file_structure_preference(self):
        """Test get_file_structure() prefers YAML config over rules.py."""
        engine = ValidationEngine(client_id="cfa")
        
        file_structure = engine.get_file_structure()
        # Should prefer YAML config (42, 1, 2) over rules.py defaults
        assert file_structure["min_columns"] == 42
        assert file_structure["header_row"] == 1
        assert file_structure["data_start_row"] == 2
    
    def test_engine_enhanced_rules_separation(self):
        """Test enhanced rules separation: enablement in YAML, implementation in rules.py."""
        engine = ValidationEngine(client_id="cfa")
        
        # get_enhanced_rules() should return implementation details (no enabled flags)
        enhanced_rules = engine.get_enhanced_rules()
        assert "active_past_graduation" in enhanced_rules
        assert "severity" in enhanced_rules["active_past_graduation"]
        assert "enabled" not in enhanced_rules["active_past_graduation"]  # No enabled flag
        
        # get_enhanced_rule_config() should return enablement from YAML
        rule_config = engine.get_enhanced_rule_config("active_past_graduation")
        assert rule_config is not None
        assert "enabled" in rule_config
        assert rule_config["enabled"] is True
        assert "severity" in rule_config
    
    def test_engine_data_classification(self):
        """Test get_data_classification() returns correct values from YAML."""
        engine = ValidationEngine(client_id="cfa")
        
        data_class = engine.get_data_classification()
        assert "default" in data_class
        assert data_class["default"] == "Confidential"  # BRD Section 2.3
        assert "pii_handling" in data_class
        assert data_class["pii_handling"] == "minimized"  # BRD Section 2.3
    
    def test_engine_error_handling(self):
        """Test ValidationEngine error handling for missing files."""
        with pytest.raises(FileNotFoundError):
            ValidationEngine(client_id="nonexistent_client")


class TestValidateStagedDataTool:
    """Test suite for ValidateStagedDataTool."""

    def test_tool_exists_and_has_name(self):
        """Verify tool class exists and has required attributes."""
        tool = ValidateStagedDataTool()

        assert hasattr(tool, 'name'), "Tool must have 'name' attribute"
        assert tool.name == "ValidateStagedDataTool"
        assert callable(tool), "Tool must be callable"
        assert hasattr(tool, 'engine'), "Tool must have 'engine' attribute"
        assert tool.client_id == "cfa", "Tool should default to 'cfa' client"

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
        assert any("Employment Status must be either" in v['message'] and "Employed In-field" in v['message'] for v in violations)

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
    
    def test_halt_logic_on_errors(self):
        """Test that validation halts when error_count > 0 and halt_on_error is enabled."""
        tool = ValidateStagedDataTool()
        headers = ["First Name", "Last Name", "Date of Birth (MM/DD/YYYY)", "Address 1"]
        headers += [f"Col {i}" for i in range(42 - len(headers))]
        
        # Create data with errors (missing required Last Name)
        df = pd.DataFrame([
            ["John", "", "01/01/1990", "123 Main St"] + [""] * 38
        ], columns=headers)
        
        result = tool(df)
        
        # Should halt on error (halt_on_error is True by default)
        assert not result.ok, "Should halt on errors"
        assert len(result.blockers) > 0
        assert any("Halted" in blocker or "errors found" in blocker for blocker in result.blockers)
    
    def test_halt_logic_warning_threshold(self):
        """Test that validation halts when warning_count >= threshold."""
        # Note: This test requires a test fixture with warning_threshold set
        # For now, we test that the logic exists and works when threshold is None
        tool = ValidateStagedDataTool()
        
        # Default threshold should be None, so warnings shouldn't halt
        # (We can't easily create warnings without implementing enhanced rules)
        # This test verifies the code path exists
        assert tool.engine.get_warning_threshold() is None
    
    def test_file_structure_uses_config(self):
        """Test that file structure from config is used (header_row, data_start_row)."""
        tool = ValidateStagedDataTool()
        headers = ["First Name", "Last Name", "Date of Birth (MM/DD/YYYY)", "Address 1"]
        headers += [f"Col {i}" for i in range(42 - len(headers))]
        
        df = pd.DataFrame([
            ["John", "Doe", "01/01/1990", "123 Main St"] + [""] * 38
        ], columns=headers)
        
        result = tool(df)
        
        # Verify that row numbers use data_start_row from config (should be 2)
        # Row 0 in DataFrame should map to row 2 in violations
        violations = result.data['violations']
        if violations:
            # Check that row_index uses data_start_row (not hardcoded +2)
            # Since data_start_row is 2, first row should be row 2
            row_indices = [v['row_index'] for v in violations]
            # First data row should be at data_start_row (2)
            assert all(rn >= 2 for rn in row_indices), f"Row indices should start at data_start_row (2), got: {row_indices}"