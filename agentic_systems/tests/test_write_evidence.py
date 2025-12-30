"""Unit tests for write_evidence.py per PRD-TRD Section 10.1."""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from agentic_systems.core.audit.write_evidence import (
    serialize_outputs,
    write_evidence_bundle,
    write_manifest,
    write_plan,
    write_summary,
)
from agentic_systems.core.tools import ToolResult


class TestWriteManifest:
    """Test suite for write_manifest()."""

    def test_manifest_basic_structure(self):
        """Test that manifest.json has required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            write_manifest(
                run_id="test-run",
                agent_name="TestAgent",
                platform="minimal",
                evidence_dir=evidence_dir
            )
            
            manifest_path = evidence_dir / "manifest.json"
            assert manifest_path.exists(), "manifest.json should be created"
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            assert manifest["run_id"] == "test-run"
            assert manifest["agent"] == "TestAgent"
            assert manifest["platform"] == "minimal"
            assert manifest["data_classification"] == "Internal"
            assert manifest["pii_handling"] == "redacted"
            assert manifest["model"] is None
            assert manifest["hitl_status"] is None
            assert manifest["resume_available"] is False

    def test_manifest_with_model(self):
        """Test manifest includes model when provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            write_manifest(
                run_id="test-run",
                agent_name="TestAgent",
                platform="langchain",
                evidence_dir=evidence_dir,
                model="gpt-4o-mini"
            )
            
            manifest_path = evidence_dir / "manifest.json"
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            assert manifest["model"] == "gpt-4o-mini"

    def test_manifest_hitl_status_halted(self):
        """Test manifest sets HITL status when run is halted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            run_results = {
                "_halted": True
            }
            write_manifest(
                run_id="test-run",
                agent_name="TestAgent",
                platform="minimal",
                evidence_dir=evidence_dir,
                run_results=run_results
            )
            
            manifest_path = evidence_dir / "manifest.json"
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            assert manifest["hitl_status"] == "halted"
            assert manifest["resume_available"] is True

    def test_manifest_staff_approval_status(self):
        """Test manifest includes staff approval status when present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            run_results = {
                "_halted": True,
                "RequestStaffApprovalTool": ToolResult(
                    ok=True,
                    summary="Approved",
                    data={"approval_status": "approved"},
                    warnings=[],
                    blockers=[]
                )
            }
            write_manifest(
                run_id="test-run",
                agent_name="TestAgent",
                platform="minimal",
                evidence_dir=evidence_dir,
                run_results=run_results
            )
            
            manifest_path = evidence_dir / "manifest.json"
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            assert manifest["staff_approval_status"] == "approved"

    def test_manifest_secure_link_code(self):
        """Test manifest includes secure link code when approved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            run_results = {
                "_halted": True,
                "RequestStaffApprovalTool": ToolResult(
                    ok=True,
                    summary="Approved",
                    data={"approval_status": "approved"},
                    warnings=[],
                    blockers=[]
                ),
                "CreateSecureLinkTool": ToolResult(
                    ok=True,
                    summary="Link created",
                    data={"access_code": "test-code-123"},
                    warnings=[],
                    blockers=[]
                )
            }
            write_manifest(
                run_id="test-run",
                agent_name="TestAgent",
                platform="minimal",
                evidence_dir=evidence_dir,
                run_results=run_results
            )
            
            manifest_path = evidence_dir / "manifest.json"
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            assert manifest["secure_link_code"] == "test-code-123"


class TestWritePlan:
    """Test suite for write_plan()."""

    def test_plan_basic_format(self):
        """Test that plan.md is created with correct format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            plan_steps = [
                {"step": "ingest", "tool": "IngestPartnerFileTool", "args": {"file_path": "test.csv"}},
                {"step": "validate", "tool": "ValidateStagedDataTool", "args": {}}
            ]
            write_plan(plan_steps, evidence_dir)
            
            plan_path = evidence_dir / "plan.md"
            assert plan_path.exists(), "plan.md should be created"
            
            content = plan_path.read_text(encoding='utf-8')
            assert "# Execution Plan" in content
            assert "IngestPartnerFileTool" in content
            assert "ValidateStagedDataTool" in content
            assert "test.csv" in content

    def test_plan_empty_steps(self):
        """Test plan.md with empty steps list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            write_plan([], evidence_dir)
            
            plan_path = evidence_dir / "plan.md"
            content = plan_path.read_text(encoding='utf-8')
            assert "# Execution Plan" in content


class TestWriteSummary:
    """Test suite for write_summary()."""

    def test_summary_basic_format(self):
        """Test that summary.md is created with correct format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            summary_text = "Test summary content"
            write_summary(summary_text, evidence_dir)
            
            summary_path = evidence_dir / "summary.md"
            assert summary_path.exists(), "summary.md should be created"
            
            content = summary_path.read_text(encoding='utf-8')
            assert "# Execution Summary" in content
            assert "Test summary content" in content


class TestSerializeOutputs:
    """Test suite for serialize_outputs()."""

    def test_serialize_validation_report(self):
        """Test that validation report is serialized to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            violations = [
                {"row_index": 2, "field": "First Name", "severity": "Error", "message": "Required"},
                {"row_index": 3, "field": "Last Name", "severity": "Warning", "message": "Invalid"}
            ]
            run_results = {
                "ValidateStagedDataTool": ToolResult(
                    ok=False,
                    summary="Validation failed",
                    data={"violations": violations},
                    warnings=[],
                    blockers=[]
                )
            }
            serialize_outputs(run_results, evidence_dir)
            
            outputs_dir = evidence_dir / "outputs"
            assert outputs_dir.exists(), "outputs/ directory should be created"
            
            validation_path = outputs_dir / "validation_report.csv"
            assert validation_path.exists(), "validation_report.csv should be created"
            
            df = pd.read_csv(validation_path)
            assert len(df) == 2
            assert "row_index" in df.columns
            assert "field" in df.columns

    def test_serialize_canonical_data(self):
        """Test that canonical data is serialized to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            canonical_df = pd.DataFrame({
                "participant_id": ["P000001", "P000002"],
                "first_name": ["John", "Jane"],
                "last_name": ["Doe", "Smith"]
            })
            run_results = {
                "CanonicalizeStagedDataTool": ToolResult(
                    ok=True,
                    summary="Canonicalized 2 records",
                    data={"canonical_dataframe": canonical_df},
                    warnings=[],
                    blockers=[]
                )
            }
            serialize_outputs(run_results, evidence_dir)
            
            outputs_dir = evidence_dir / "outputs"
            canonical_path = outputs_dir / "canonical.csv"
            assert canonical_path.exists(), "canonical.csv should be created"
            
            df = pd.read_csv(canonical_path)
            assert len(df) == 2
            assert "participant_id" in df.columns

    def test_serialize_email_content(self):
        """Test that email content is serialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            run_results = {
                "GeneratePartnerEmailTool": ToolResult(
                    ok=True,
                    summary="Email generated",
                    data={
                        "email_content": "Test email content",
                        "email_html": "<p>Test email content</p>"
                    },
                    warnings=[],
                    blockers=[]
                )
            }
            serialize_outputs(run_results, evidence_dir)
            
            outputs_dir = evidence_dir / "outputs"
            email_txt_path = outputs_dir / "partner_email.txt"
            email_html_path = outputs_dir / "partner_email.html"
            
            assert email_txt_path.exists(), "partner_email.txt should be created"
            assert email_html_path.exists(), "partner_email.html should be created"
            
            assert email_txt_path.read_text(encoding='utf-8') == "Test email content"
            assert "<p>Test email content</p>" in email_html_path.read_text(encoding='utf-8')

    def test_serialize_staff_approval_record(self):
        """Test that staff approval record is serialized."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            run_results = {
                "RequestStaffApprovalTool": ToolResult(
                    ok=True,
                    summary="Approved",
                    data={
                        "approval_status": "approved",
                        "staff_comments": "Looks good",
                        "approval_timestamp": "2024-01-01T00:00:00Z"
                    },
                    warnings=[],
                    blockers=[]
                )
            }
            serialize_outputs(run_results, evidence_dir)
            
            outputs_dir = evidence_dir / "outputs"
            approval_path = outputs_dir / "staff_approval_record.json"
            
            assert approval_path.exists(), "staff_approval_record.json should be created"
            
            with open(approval_path, 'r', encoding='utf-8') as f:
                approval_record = json.load(f)
            
            assert approval_record["approval_status"] == "approved"
            assert approval_record["staff_comments"] == "Looks good"


class TestWriteEvidenceBundle:
    """Test suite for write_evidence_bundle() integration."""

    def test_full_bundle_creation(self):
        """Test that complete evidence bundle is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            plan_steps = [
                {"step": "ingest", "tool": "IngestPartnerFileTool", "args": {}}
            ]
            summary = "Test summary"
            run_results = {
                "IngestPartnerFileTool": ToolResult(
                    ok=True,
                    summary="Ingested 10 rows",
                    data={"row_count": 10},
                    warnings=[],
                    blockers=[]
                )
            }
            
            write_evidence_bundle(
                run_id="test-run",
                agent_name="TestAgent",
                platform="minimal",
                plan_steps=plan_steps,
                summary=summary,
                run_results=run_results,
                evidence_dir=evidence_dir
            )
            
            # Verify all files are created
            assert (evidence_dir / "manifest.json").exists()
            assert (evidence_dir / "plan.md").exists()
            assert (evidence_dir / "summary.md").exists()
            assert (evidence_dir / "outputs").exists()

    def test_bundle_with_validation_and_canonical(self):
        """Test bundle with validation and canonicalization results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            canonical_df = pd.DataFrame({
                "participant_id": ["P000001"],
                "first_name": ["John"]
            })
            run_results = {
                "ValidateStagedDataTool": ToolResult(
                    ok=True,
                    summary="Validation passed",
                    data={"violations": []},
                    warnings=[],
                    blockers=[]
                ),
                "CanonicalizeStagedDataTool": ToolResult(
                    ok=True,
                    summary="Canonicalized 1 record",
                    data={"canonical_dataframe": canonical_df},
                    warnings=[],
                    blockers=[]
                )
            }
            
            write_evidence_bundle(
                run_id="test-run",
                agent_name="TestAgent",
                platform="minimal",
                plan_steps=[],
                summary="Test",
                run_results=run_results,
                evidence_dir=evidence_dir
            )
            
            # Verify canonical CSV is created
            canonical_path = evidence_dir / "outputs" / "canonical.csv"
            assert canonical_path.exists()



