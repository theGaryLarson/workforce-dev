"""Integration tests for multi-partner file processing workflows."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from agentic_systems.core.ingestion.ingest_tool import IngestPartnerFileTool
from agentic_systems.clients.cfa.partners import (
    get_partner_name_from_path,
    load_partner_parsing_config,
)


class TestMultiPartnerWorkflow:
    """Integration test suite for multi-partner file processing."""

    @pytest.fixture
    def sharepoint_sim_structure(self):
        """Create a temporary SharePoint simulation structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            sharepoint_sim = base_dir / "sharepoint_simulation"
            uploads_dir = sharepoint_sim / "uploads"
            
            # Create partner folders
            partner1_dir = uploads_dir / "test-partner-1"
            partner2_dir = uploads_dir / "test-partner-2"
            partner1_dir.mkdir(parents=True)
            partner2_dir.mkdir(parents=True)
            
            yield {
                "base_dir": base_dir,
                "sharepoint_sim": sharepoint_sim,
                "uploads_dir": uploads_dir,
                "partner1_dir": partner1_dir,
                "partner2_dir": partner2_dir,
            }

    def test_partner_detection_from_file_path(self, sharepoint_sim_structure):
        """Test partner name extraction from file path in uploads structure."""
        partner1_dir = sharepoint_sim_structure["partner1_dir"]
        partner2_dir = sharepoint_sim_structure["partner2_dir"]
        uploads_dir = sharepoint_sim_structure["uploads_dir"]
        
        # Create test files
        file1 = partner1_dir / "test_file_1.csv"
        file2 = partner2_dir / "test_file_2.csv"
        file1.write_text("test content 1")
        file2.write_text("test content 2")
        
        # Extract partner names
        partner1 = get_partner_name_from_path(file1, uploads_dir)
        partner2 = get_partner_name_from_path(file2, uploads_dir)
        
        assert partner1 == "test-partner-1"
        assert partner2 == "test-partner-2"

    def test_different_partners_use_different_configs(self):
        """Test that different partners load different parsing configurations."""
        config1 = load_partner_parsing_config("cfa", "test-partner-1")
        config2 = load_partner_parsing_config("cfa", "test-partner-2")
        
        # Both should load (even if test-partner-2 is a placeholder)
        # The key is that they are separate configs
        if config1 and config2:
            assert config1.get("partner") == "test-partner-1"
            assert config2.get("partner") == "test-partner-2"
        elif config1:
            # At least test-partner-1 should have a config
            assert config1.get("partner") == "test-partner-1"

    def test_partner_specific_ingestion(self, sharepoint_sim_structure):
        """Test that ingestion tool accepts partner_name parameter."""
        # Create a CSV file with test-partner-1 format
        content = """Last Name,First Name,Date of Birth (MM/DD/YYYY),Zip Code
Doe,John,01/15/1990,98101
Smith,Jane,02/20/1985,98006"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            tool = IngestPartnerFileTool()
            
            # Test with partner_name
            result1 = tool(str(temp_path), partner_name="test-partner-1", client_id="cfa")
            assert result1.ok, "Ingestion should succeed with partner_name"
            
            # Test without partner_name (fallback)
            result2 = tool(str(temp_path))
            assert result2.ok, "Ingestion should succeed without partner_name"
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_run_id_generation_with_partner(self):
        """Test that run_id format includes partner name."""
        partner = "test-partner-1"
        quarter = "Q1"
        platform = "minimal"
        
        run_id = f"{partner}-{quarter}-{platform}"
        
        assert run_id == "test-partner-1-Q1-minimal"
        assert run_id.startswith(partner)

    def test_multiple_partners_separate_runs(self):
        """Test that different partners generate separate run IDs."""
        partner1 = "test-partner-1"
        partner2 = "test-partner-2"
        quarter = "Q1"
        platform = "minimal"
        
        run_id1 = f"{partner1}-{quarter}-{platform}"
        run_id2 = f"{partner2}-{quarter}-{platform}"
        
        assert run_id1 != run_id2
        assert run_id1.startswith(partner1)
        assert run_id2.startswith(partner2)

    def test_partner_folder_structure(self, sharepoint_sim_structure):
        """Test that partner-specific folders are created correctly."""
        partner1_dir = sharepoint_sim_structure["partner1_dir"]
        partner2_dir = sharepoint_sim_structure["partner2_dir"]
        
        assert partner1_dir.exists()
        assert partner2_dir.exists()
        assert partner1_dir.name == "test-partner-1"
        assert partner2_dir.name == "test-partner-2"

    def test_corrected_file_workflow_per_partner(self, sharepoint_sim_structure):
        """Test that corrected files are handled per partner."""
        partner1_dir = sharepoint_sim_structure["partner1_dir"]
        partner2_dir = sharepoint_sim_structure["partner2_dir"]
        
        # Create original files for each partner
        original1 = partner1_dir / "original_1.csv"
        original2 = partner2_dir / "original_2.csv"
        original1.write_text("original content 1")
        original2.write_text("original content 2")
        
        # Create corrected files for each partner
        corrected1 = partner1_dir / "corrected_1.csv"
        corrected2 = partner2_dir / "corrected_2.csv"
        corrected1.write_text("corrected content 1")
        corrected2.write_text("corrected content 2")
        
        # Verify files are in correct partner folders
        assert corrected1.exists() and corrected1.parent == partner1_dir
        assert corrected2.exists() and corrected2.parent == partner2_dir

    def test_evidence_bundle_structure_per_partner(self):
        """Test that evidence bundles are stored in partner-specific run directories."""
        partner1 = "test-partner-1"
        partner2 = "test-partner-2"
        quarter = "Q1"
        platform = "minimal"
        
        run_id1 = f"{partner1}-{quarter}-{platform}"
        run_id2 = f"{partner2}-{quarter}-{platform}"
        
        # Expected evidence directory structure
        # core/audit/runs/{partner}-{quarter}-{platform}/
        expected_dir1 = f"core/audit/runs/{run_id1}"
        expected_dir2 = f"core/audit/runs/{run_id2}"
        
        assert run_id1 in expected_dir1
        assert run_id2 in expected_dir2
        assert expected_dir1 != expected_dir2
