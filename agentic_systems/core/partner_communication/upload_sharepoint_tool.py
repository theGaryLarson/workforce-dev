"""UploadSharePointTool per BRD FR-012 and FR-013.

Demo implementation for two-stage SharePoint upload workflow:
- Stage 1: Upload validation review worksheet to an internal location for CFA staff review
- Stage 2: After approval, upload report to a partner-accessible location

This tool is intentionally implemented with a local filesystem simulation for the POC:
- For "internal" and "partner" folder types: Creates link/metadata artifacts (link.json) 
  pointing to the canonical partner_error_report.xlsx file instead of copying it.
- For "upload" folder type: Copies corrected files from partner uploads (this represents 
  the partner uploading a new version, not another copy of the error report).
- Returned URLs are file:// URLs pointing at the simulated SharePoint locations

Per orchestrator plan: Single canonical partner_error_report.xlsx per run, with 
internal/partner folders containing only link/metadata artifacts pointing to the same file.

PRODUCTION NOTES:
- Replace filesystem simulation with real SharePoint integration using SharePointClient
  described in PRD-TRD Section 5.4 (SharePoint Integration Tools).
- Use Azure AD app registration and office365-rest-python-client for authentication.
- Folder structure and site URLs should be configurable via environment variables.
"""

from pathlib import Path
from typing import Any, Dict
import json
import shutil

from ..tools import ToolResult


class UploadSharePointTool:
    """Uploads validation reports to simulated SharePoint locations for HITL workflow.
    
    For the POC, this tool simulates SharePoint by copying files into a local
    "sharepoint_simulation" directory under the evidence bundle. This allows
    us to exercise the full two-stage upload workflow without external
    dependencies while keeping the interface compatible with a future
    SharePointClient implementation.
    
    Folder types (demo simulation of SharePoint libraries):
    - "internal":   Internal CFA staff location used for review before approval (BRD FR-012)
    - "partner":    Partner-accessible location used after staff approval (BRD FR-013)
    - "upload":     Simulated partner upload/drop-off location for corrected files so we can
                    test validation retry/resume flows without real SharePoint webhooks (BRD FR-012)
    
    PRODUCTION:
    - Replace the local copy logic with SharePointClient.upload_file(...)
    - Use distinct document libraries or folders for internal vs partner locations
    - Ensure appropriate permissions and access controls per BRD FR-012/FR-013
    """

    name = "UploadSharePointTool"

    def __call__(
        self,
        file_path: Path,
        folder_type: str,  # "internal", "partner", or "upload" (demo simulation)
        partner_name: str,
        quarter: str,
        run_id: str,
        evidence_dir: Path,
        demo_mode: bool = True,
    ) -> ToolResult:
        """Upload file to simulated SharePoint (demo) or real SharePoint (future).

        Args:
            file_path: Local file to upload (e.g., partner_error_report.xlsx)
            folder_type: "internal" for staff-only location, "partner" for partner-accessible
                         location, or "upload" for simulated partner upload folder.
            partner_name: Partner identifier (used in simulated folder structure)
            quarter: Quarter identifier (e.g., "Q1")
            run_id: Run identifier (used in simulated folder structure)
            evidence_dir: Evidence bundle directory (root for sharepoint_simulation in demo_mode)
            demo_mode: When True, use filesystem simulation; when False, hook up real SharePoint

        Returns:
            ToolResult with sharepoint_url and local_path in data.
        """
        if folder_type not in {"internal", "partner", "upload"}:
            return ToolResult(
                ok=False,
                summary=(
                    f"Invalid folder_type '{folder_type}' "
                    "(expected 'internal', 'partner', or 'upload')"
                ),
                data={},
                warnings=[],
                blockers=[f"Invalid folder_type '{folder_type}'"],
            )

        # DEMO IMPLEMENTATION: Local filesystem "SharePoint" simulation
        if demo_mode:
            base_sim_dir = evidence_dir / "sharepoint_simulation"
            
            # Initialize all three folder types for the run_id (per POC plan structure)
            # This ensures the uploads folder exists even if not immediately used
            # Per POC plan: sharepoint_simulation/internal/, partner_accessible/, and uploads/
            internal_dir = base_sim_dir / "internal" / run_id
            partner_dir = base_sim_dir / "partner_accessible" / run_id
            uploads_dir = base_sim_dir / "uploads" / run_id
            
            # Create all three directories upfront so partners know where to upload corrected files
            internal_dir.mkdir(parents=True, exist_ok=True)
            partner_dir.mkdir(parents=True, exist_ok=True)
            uploads_dir.mkdir(parents=True, exist_ok=True)
            
            # Map folder_type to the appropriate directory
            if folder_type == "internal":
                stage_dir = internal_dir
            elif folder_type == "partner" or folder_type == "partner_accessible":
                stage_dir = partner_dir
            else:
                # "upload": simulated partner upload folder for corrected files.
                # This allows testing resume/polling flows after approval in the POC
                # without real SharePoint + webhooks (BRD FR-012 validation retry).
                stage_dir = uploads_dir

            # Per orchestrator plan: For "internal" and "partner" folder types,
            # create link/metadata artifacts instead of copying the file.
            # This ensures a single canonical partner_error_report.xlsx per run.
            if folder_type in {"internal", "partner", "partner_accessible"}:
                # Create link.json metadata artifact pointing to canonical file
                canonical_path = file_path.resolve()  # Absolute path to canonical file
                link_metadata = {
                    "canonical_file_path": str(canonical_path),
                    "file_url": f"file:///{canonical_path.as_posix()}",
                    "file_name": file_path.name,
                    "partner_name": partner_name,
                    "quarter": quarter,
                    "run_id": run_id,
                    "created_at": str(Path(__file__).stat().st_mtime)  # Simple timestamp
                }
                
                # Write link.json to the appropriate folder
                link_json_path = stage_dir / "link.json"
                with open(link_json_path, 'w', encoding='utf-8') as f:
                    json.dump(link_metadata, f, indent=2)
                
                # Return file:// URL pointing to canonical file (not the link.json)
                sharepoint_url = f"file:///{canonical_path.as_posix()}"
                
                return ToolResult(
                    ok=True,
                    summary=(
                        f"Created link/metadata artifact for simulated SharePoint ({folder_type}) "
                        f"pointing to canonical file at {sharepoint_url}"
                    ),
                    data={
                        "sharepoint_url": sharepoint_url,
                        "link_metadata_path": str(link_json_path),
                        "canonical_file_path": str(canonical_path),
                        "folder_type": folder_type,
                    },
                    warnings=[],
                    blockers=[],
                )
            else:
                # "upload" folder type: Copy the corrected file (partner upload)
                # File name convention: <partner>_<quarter>_<original_name>
                dest_name = f"{partner_name}_{quarter}_{file_path.name}"
                dest_path = stage_dir / dest_name
                
                shutil.copy2(file_path, dest_path)
                
                # For demo: return a file:// URL pointing to the simulated SharePoint path
                sharepoint_url = f"file:///{dest_path.as_posix()}"
                
                return ToolResult(
                    ok=True,
                    summary=(
                        f"Uploaded corrected file to simulated SharePoint ({folder_type}) at "
                        f"{sharepoint_url}"
                    ),
                    data={
                        "sharepoint_url": sharepoint_url,
                        "local_path": str(dest_path),
                        "folder_type": folder_type,
                    },
                    warnings=[],
                    blockers=[],
                )

        # PRODUCTION IMPLEMENTATION PLACEHOLDER:
        # In production, this branch should:
        # - Initialize a SharePointClient with Azure AD credentials
        # - Map folder_type to internal/partner document libraries or folder paths
        # - Read file bytes and call client.upload_file(...)
        # - Return the resulting SharePoint file URL in sharepoint_url
        return ToolResult(
            ok=False,
            summary="SharePoint upload not implemented in production mode yet",
            data={},
            warnings=[],
            blockers=["SharePoint upload not implemented in production mode yet"],
        )



