"""Unit tests for CanonicalizeStagedDataTool per PRD-TRD Section 10.1."""

import pandas as pd

from agentic_systems.core.canonical.canonicalize_tool import CanonicalizeStagedDataTool
from agentic_systems.core.tools import ToolResult


class TestCanonicalizeStagedDataTool:
    """Test suite for CanonicalizeStagedDataTool."""

    def test_tool_exists_and_has_name(self):
        """Verify tool class exists and has required attributes."""
        tool = CanonicalizeStagedDataTool()

        assert hasattr(tool, 'name'), "Tool must have 'name' attribute"
        assert tool.name == "CanonicalizeStagedDataTool"
        assert hasattr(tool, 'FIELD_MAPPING'), "Tool must have FIELD_MAPPING"
        assert callable(tool), "Tool must be callable"

    def test_canonical_id_generation(self, sample_dataframe):
        """Test stable POC ID generation (P000001, P000002, etc.)."""
        tool = CanonicalizeStagedDataTool()
        result = tool(sample_dataframe)

        assert isinstance(result, ToolResult), "Must return ToolResult"
        assert result.ok, "Canonicalization should succeed"
        assert 'canonical_dataframe' in result.data, "Result must contain canonical DataFrame"

        canonical_df = result.data['canonical_dataframe']
        assert 'participant_id' in canonical_df.columns, "Canonical data must have participant_id"

        # Verify ID format: P000001, P000002, etc.
        participant_ids = canonical_df['participant_id'].tolist()
        assert participant_ids[0] == 'P000001', "First ID should be P000001"
        assert participant_ids[1] == 'P000002', "Second ID should be P000002"
        assert participant_ids[2] == 'P000003', "Third ID should be P000003"

        # Verify all IDs follow pattern
        for pid in participant_ids:
            assert pid.startswith('P'), f"Participant ID '{pid}' should start with 'P'"
            assert len(pid) == 7, f"Participant ID '{pid}' should be 7 characters (P + 6 digits)"
            assert pid[1:].isdigit(), f"Participant ID '{pid}' should have 6 digits after 'P'"

    def test_field_mapping(self, sample_dataframe):
        """Test field mapping from staged to canonical format."""
        tool = CanonicalizeStagedDataTool()
        result = tool(sample_dataframe)

        canonical_df = result.data['canonical_dataframe']

        # Verify mapped fields exist in canonical data
        for staged_field, canonical_field in tool.FIELD_MAPPING.items():
            if staged_field in sample_dataframe.columns:
                assert canonical_field in canonical_df.columns, f"Canonical field '{canonical_field}' should exist"

        # Verify data values are preserved
        assert canonical_df['first_name'].tolist() == sample_dataframe['first_name'].tolist()
        assert canonical_df['last_name'].tolist() == sample_dataframe['last_name'].tolist()

    def test_additional_fields_preserved(self, sample_dataframe):
        """Test that additional fields not in mapping are preserved."""
        # Add a field not in FIELD_MAPPING
        df = sample_dataframe.copy()
        df['custom_field'] = ['value1', 'value2', 'value3']

        tool = CanonicalizeStagedDataTool()
        result = tool(df)

        canonical_df = result.data['canonical_dataframe']

        # Custom field should be preserved
        assert 'custom_field' in canonical_df.columns, "Additional fields should be preserved"
        assert canonical_df['custom_field'].tolist() == df['custom_field'].tolist()

    def test_record_count(self, sample_dataframe):
        """Test that record count matches input."""
        tool = CanonicalizeStagedDataTool()
        result = tool(sample_dataframe)

        assert 'record_count' in result.data, "Result must contain record_count"
        assert result.data['record_count'] == len(sample_dataframe), "Record count should match input"
        assert result.data['record_count'] == len(result.data['canonical_dataframe']), "Record count should match canonical DataFrame length"

    def test_canonical_dataframe_structure(self, sample_dataframe):
        """Test canonical DataFrame structure and data types."""
        tool = CanonicalizeStagedDataTool()
        result = tool(sample_dataframe)

        canonical_df = result.data['canonical_dataframe']

        assert isinstance(canonical_df, pd.DataFrame), "Canonical data must be a DataFrame"
        assert len(canonical_df) == len(sample_dataframe), "Row count should match"
        # Should have all input columns plus participant_id
        assert len(canonical_df.columns) >= len(sample_dataframe.columns), "Should have at least input columns"
        assert 'participant_id' in canonical_df.columns, "Should have participant_id column"

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame()

        tool = CanonicalizeStagedDataTool()
        result = tool(empty_df)

        assert isinstance(result, ToolResult), "Must return ToolResult"
        assert result.ok, "Should handle empty DataFrame gracefully"
        assert result.data['record_count'] == 0, "Record count should be 0"
        assert len(result.data['canonical_dataframe']) == 0, "Canonical DataFrame should be empty"

    def test_summary_message(self, sample_dataframe):
        """Test summary message includes record count."""
        tool = CanonicalizeStagedDataTool()
        result = tool(sample_dataframe)

        assert 'Canonicalized' in result.summary, "Summary should mention canonicalization"
        assert str(result.data['record_count']) in result.summary, "Summary should include record count"
