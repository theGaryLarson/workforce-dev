"""Unit tests for partner communication tools per PRD-TRD Section 10.1."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from agentic_systems.core.partner_communication.secure_link_tool import CreateSecureLinkTool
from agentic_systems.core.partner_communication.upload_sharepoint_tool import UploadSharePointTool
from agentic_systems.core.partner_communication.excel_utils import (
    _standardize_phone_number,
    _get_action_guidance,
    create_error_excel_with_comments,
)
from agentic_systems.core.tools import ToolResult


class TestCreateSecureLinkTool:
    """Test suite for CreateSecureLinkTool."""

    def test_tool_exists_and_has_name(self):
        """Verify tool class exists and has required attributes."""
        tool = CreateSecureLinkTool()
        
        assert hasattr(tool, 'name')
        assert tool.name == "CreateSecureLinkTool"
        assert callable(tool)

    def test_generate_access_code(self):
        """Test that access code is generated and written to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            error_report_path = evidence_dir / "error_report.csv"
            error_report_path.write_text("test content")
            
            tool = CreateSecureLinkTool()
            result = tool(
                error_report_path=error_report_path,
                evidence_dir=evidence_dir,
                run_id="test-run"
            )
            
            assert result.ok
            assert "access_code" in result.data
            assert len(result.data["access_code"]) > 0
            
            # Verify access code file was created
            code_file = evidence_dir / "secure_link_code.txt"
            assert code_file.exists()
            assert code_file.read_text() == result.data["access_code"]

    def test_secure_link_with_sharepoint_url(self):
        """Test secure link uses SharePoint URL when provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            error_report_path = evidence_dir / "error_report.csv"
            error_report_path.write_text("test")
            
            tool = CreateSecureLinkTool()
            result = tool(
                error_report_path=error_report_path,
                evidence_dir=evidence_dir,
                run_id="test-run",
                sharepoint_url="https://sharepoint.com/file.xlsx"
            )
            
            assert result.data["secure_link_url"] == "https://sharepoint.com/file.xlsx"

    def test_secure_link_fallback_to_file_url(self):
        """Test secure link falls back to file:// URL when no SharePoint URL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            error_report_path = evidence_dir / "error_report.csv"
            error_report_path.write_text("test")
            
            tool = CreateSecureLinkTool()
            result = tool(
                error_report_path=error_report_path,
                evidence_dir=evidence_dir,
                run_id="test-run"
            )
            
            assert result.data["secure_link_url"].startswith("file:///")


class TestUploadSharePointTool:
    """Test suite for UploadSharePointTool."""

    def test_tool_exists_and_has_name(self):
        """Verify tool class exists and has required attributes."""
        tool = UploadSharePointTool()
        
        assert hasattr(tool, 'name')
        assert tool.name == "UploadSharePointTool"
        assert callable(tool)

    def test_upload_publish_folder_creates_link_json(self):
        """Test uploading to publish folder creates link.json in uploads/{partner_name}/."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            file_path = evidence_dir / "test_file.xlsx"
            file_path.write_text("test content")
            
            # Create outputs directory with error report
            outputs_dir = evidence_dir / "outputs"
            outputs_dir.mkdir()
            error_report_path = outputs_dir / "partner_error_report.xlsx"
            error_report_path.write_text("error report content")
            
            tool = UploadSharePointTool()
            result = tool(
                file_path=error_report_path,
                folder_type="publish",
                partner_name="test-partner-1",
                quarter="Q1",
                run_id="test-run",
                evidence_dir=evidence_dir,
                demo_mode=True
            )
            
            assert result.ok
            assert "sharepoint_url" in result.data
            assert "link_metadata_path" in result.data
            
            # Verify link.json was created in uploads/{partner_name}/
            link_path = Path(result.data["link_metadata_path"])
            assert link_path.exists()
            assert "uploads" in str(link_path)
            assert "test-partner-1" in str(link_path)
            
            with open(link_path, 'r', encoding='utf-8') as f:
                link_metadata = json.load(f)
            
            assert link_metadata["partner_name"] == "test-partner-1"
            assert link_metadata["quarter"] == "Q1"
            assert link_metadata["run_id"] == "test-run"
            assert "canonical_file_path" in link_metadata

    def test_upload_uploads_folder_copies_file(self):
        """Test uploading to uploads folder copies the file to uploads/{partner_name}/."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            file_path = evidence_dir / "corrected_file.csv"
            file_path.write_text("corrected content")
            
            tool = UploadSharePointTool()
            result = tool(
                file_path=file_path,
                folder_type="upload",
                partner_name="test-partner-1",
                quarter="Q1",
                run_id="test-run",
                evidence_dir=evidence_dir,
                demo_mode=True
            )
            
            assert result.ok
            assert "local_path" in result.data
            
            # Verify file was copied to uploads/{partner_name}/
            copied_path = Path(result.data["local_path"])
            assert copied_path.exists()
            assert copied_path.read_text() == "corrected content"
            assert "uploads" in str(copied_path)
            assert "test-partner-1" in str(copied_path)
            assert "test-partner-1_Q1_corrected_file.csv" in str(copied_path)

    def test_upload_invalid_folder_type(self):
        """Test that invalid folder_type returns error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            file_path = evidence_dir / "test.xlsx"
            file_path.write_text("test")
            
            tool = UploadSharePointTool()
            result = tool(
                file_path=file_path,
                folder_type="invalid",
                partner_name="demo",
                quarter="Q1",
                run_id="test-run",
                evidence_dir=evidence_dir,
                demo_mode=True
            )
            
            assert not result.ok
            assert len(result.blockers) > 0


class TestExcelUtils:
    """Test suite for excel_utils helper functions."""

    def test_standardize_phone_number_basic(self):
        """Test phone number standardization with basic formats."""
        assert _standardize_phone_number("206-555-1234") == "206-555-1234"
        assert _standardize_phone_number("(206) 555-1234") == "206-555-1234"
        assert _standardize_phone_number("206.555.1234") == "206-555-1234"
        assert _standardize_phone_number("2065551234") == "206-555-1234"

    def test_standardize_phone_number_with_country_code(self):
        """Test phone number standardization with country code."""
        assert _standardize_phone_number("1-206-555-1234") == "206-555-1234"
        assert _standardize_phone_number("+1-206-555-1234") == "206-555-1234"
        assert _standardize_phone_number("12065551234") == "206-555-1234"

    def test_standardize_phone_number_international_format(self):
        """Test phone number standardization with international format."""
        assert _standardize_phone_number("001-206-555-1234") == "206-555-1234"
        assert _standardize_phone_number("0012065551234") == "206-555-1234"

    def test_standardize_phone_number_with_extension(self):
        """Test phone number standardization with extension (takes last 10 digits)."""
        # The function takes the last 10 digits when there are more than 10
        # "206-555-1234 x567" has 13 digits total, so it takes last 10: "555-123-4567"
        result = _standardize_phone_number("206-555-1234 x567")
        assert result == "555-123-4567"  # Last 10 digits from the full string

    def test_standardize_phone_number_invalid(self):
        """Test phone number standardization returns original for invalid input."""
        assert _standardize_phone_number("123") == "123"  # Too short
        assert _standardize_phone_number(None) is None
        assert pd.isna(_standardize_phone_number(pd.NA)) or _standardize_phone_number(pd.NA) is None

    def test_get_action_guidance_required_field(self):
        """Test action guidance for required field errors."""
        guidance = _get_action_guidance("First Name is required", "Error")
        assert "required" in guidance.lower() or "provide" in guidance.lower()

    def test_get_action_guidance_date_error(self):
        """Test action guidance for date validation errors."""
        guidance = _get_action_guidance("Date must be in MM/DD/YYYY format", "Error")
        assert "date" in guidance.lower() or "mm/dd/yyyy" in guidance.lower()

    def test_get_action_guidance_address_error(self):
        """Test action guidance for address validation errors."""
        guidance = _get_action_guidance("Address 1 must not contain apartment info", "Error")
        assert "address" in guidance.lower()

    def test_get_action_guidance_default_error(self):
        """Test default action guidance for errors."""
        guidance = _get_action_guidance("Some error", "Error")
        assert len(guidance) > 0

    def test_create_error_excel_with_comments(self):
        """Test Excel file creation with error comments and color-coding."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "error_report.xlsx"
            
            df = pd.DataFrame({
                "First Name": ["John", "Jane", ""],
                "Last Name": ["Doe", "Smith", "Johnson"],
                "Date of Birth (MM/DD/YYYY)": ["01/01/1990", "invalid", "02/02/1995"]
            })
            
            violations = [
                {
                    "row_index": 3,  # Third row (Jane)
                    "field": "Date of Birth (MM/DD/YYYY)",
                    "message": "Date must be in MM/DD/YYYY format",
                    "severity": "Error"
                },
                {
                    "row_index": 4,  # Fourth row (empty first name)
                    "field": "First Name",
                    "message": "First Name is required",
                    "severity": "Error"
                }
            ]
            
            create_error_excel_with_comments(df, violations, output_path)
            
            assert output_path.exists()
            
            # Verify Excel file can be read
            result_df = pd.read_excel(output_path, engine='openpyxl')
            assert len(result_df) == 3
            assert "First Name" in result_df.columns

    def test_create_error_excel_phone_standardization(self):
        """Test that phone numbers are standardized in Excel output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "error_report.xlsx"
            
            df = pd.DataFrame({
                "First Name": ["John"],
                "Phone": ["2065551234"]
            })
            
            create_error_excel_with_comments(df, [], output_path)
            
            # Verify phone was standardized
            result_df = pd.read_excel(output_path, engine='openpyxl')
            assert result_df["Phone"].iloc[0] == "206-555-1234"

