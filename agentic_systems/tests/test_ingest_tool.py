"""Unit tests for IngestPartnerFileTool per PRD-TRD Section 10.1."""

import hashlib
import tempfile
from pathlib import Path

import pandas as pd

from agentic_systems.core.ingestion.ingest_tool import IngestPartnerFileTool
from agentic_systems.core.tools import ToolResult


class TestIngestPartnerFileTool:
    """Test suite for IngestPartnerFileTool."""

    def test_tool_exists_and_has_name(self):
        """Verify tool class exists and has required attributes."""
        tool = IngestPartnerFileTool()

        assert hasattr(tool, 'name'), "Tool must have 'name' attribute"
        assert tool.name == "IngestPartnerFileTool"
        assert callable(tool), "Tool must be callable"

    def test_csv_ingestion(self, sample_csv_file):
        """Test CSV file ingestion."""
        tool = IngestPartnerFileTool()
        result = tool(sample_csv_file)

        assert isinstance(result, ToolResult), "Must return ToolResult"
        assert result.ok, "Ingestion should succeed"
        assert 'dataframe' in result.data, "Result must contain DataFrame"

        df = result.data['dataframe']
        assert isinstance(df, pd.DataFrame), "Data must be a DataFrame"
        assert len(df) == 3, "Should ingest 3 rows"
        assert 'first_name' in df.columns, "Column names should be normalized"
        assert 'last_name' in df.columns, "Column names should be normalized"

    def test_column_normalization(self, sample_csv_file):
        """Test column name normalization (lowercase, replace spaces)."""
        tool = IngestPartnerFileTool()
        result = tool(sample_csv_file)

        df = result.data['dataframe']
        # Verify column names are normalized
        assert 'first_name' in df.columns, "Spaces should be replaced with underscores"
        assert 'last_name' in df.columns, "Spaces should be replaced with underscores"
        assert 'date_of_birth' in df.columns, "Parentheses should be removed"
        assert 'zip_code' in df.columns, "Spaces should be replaced with underscores"

        # Verify all columns are lowercase
        for col in df.columns:
            assert col.islower() or '_' in col, f"Column '{col}' should be lowercase"

    def test_file_hash_calculation(self, sample_csv_file):
        """Test file hash calculation for idempotency."""
        tool = IngestPartnerFileTool()
        result = tool(sample_csv_file)

        assert 'file_hash' in result.data, "Result must contain file hash"

        # Verify hash matches expected calculation
        with open(sample_csv_file, 'rb') as f:
            expected_hash = hashlib.sha256(f.read()).hexdigest()

        assert result.data['file_hash'] == expected_hash, "Hash should match file content"

    def test_zip_code_preservation(self, sample_csv_file):
        """Test that zip codes are preserved as strings (not floats)."""
        tool = IngestPartnerFileTool()
        result = tool(sample_csv_file)

        df = result.data['dataframe']

        # Verify zip codes are strings, not floats
        zip_values = df['zip_code'].tolist()
        for zip_val in zip_values:
            assert isinstance(zip_val, str) or pd.isna(zip_val), f"Zip code '{zip_val}' should be string, got {type(zip_val)}"
            if isinstance(zip_val, str):
                # Should not have .0 suffix
                assert not zip_val.endswith('.0'), f"Zip code '{zip_val}' should not have .0 suffix"

    def test_metadata_in_result(self, sample_csv_file):
        """Test that result contains required metadata."""
        tool = IngestPartnerFileTool()
        result = tool(sample_csv_file)

        assert 'row_count' in result.data, "Result must contain row_count"
        assert 'columns' in result.data, "Result must contain columns list"
        assert result.data['row_count'] == 3, "Row count should match ingested rows"
        assert isinstance(result.data['columns'], list), "Columns should be a list"
        assert len(result.data['columns']) > 0, "Columns list should not be empty"

    def test_nonexistent_file(self):
        """Test handling of nonexistent file."""
        tool = IngestPartnerFileTool()
        result = tool("nonexistent_file.csv")

        assert isinstance(result, ToolResult), "Must return ToolResult"
        assert not result.ok, "Should fail for nonexistent file"
        assert len(result.blockers) > 0, "Should have blockers for error"

    def test_unsupported_format(self):
        """Test handling of unsupported file format."""
        tool = IngestPartnerFileTool()

        # Create a file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"test content")
            temp_path = Path(f.name)

        try:
            result = tool(str(temp_path))
            assert not result.ok, "Should fail for unsupported format"
            assert len(result.blockers) > 0, "Should have blockers for error"
        finally:
            if temp_path.exists():
                temp_path.unlink()

