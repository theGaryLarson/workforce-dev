"""UploadSharePointTool per BRD FR-012 and FR-013.

Simplified implementation using a single uploads/ folder for all file operations:
- Partner file uploads (initial and corrected files) are placed in uploads/{partner_name}/
- Error report publishing creates link.json metadata in uploads/{partner_name}/ pointing 
  to the canonical file in outputs/partner_error_report.xlsx

This tool is intentionally implemented with a local filesystem simulation for the POC:
- For "publish" folder type: Creates link/metadata artifacts (link.json) pointing to 
  the canonical partner_error_report.xlsx file in the evidence bundle outputs/ folder.
- For "upload" folder type: Copies partner files (initial uploads or corrected files) 
  to uploads/{partner_name}/ for processing.
- Returned URLs are file:// URLs pointing at the simulated SharePoint locations

Per orchestrator plan: Single canonical partner_error_report.xlsx per run in outputs/,
with link.json metadata in uploads/{partner_name}/ for publishing/sharing.

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
    "sharepoint_simulation" directory at the repo root (agentic_systems/sharepoint_simulation/).
    This allows us to exercise the full upload workflow without external dependencies while 
    keeping the interface compatible with a future SharePointClient implementation.
    
    Folder types (simplified structure):
    - "publish":    Creates link.json metadata in uploads/{partner_name}/ pointing to the 
                    canonical error report in outputs/partner_error_report.xlsx (for both 
                    internal and partner access)
    - "upload":     Copies partner files (initial uploads or corrected files) to 
                    uploads/{partner_name}/ for processing
    
    PRODUCTION:
    - Replace the local copy logic with SharePointClient.upload_file(...)
    - Use appropriate document libraries or folders with proper permissions
    - Ensure appropriate access controls per BRD FR-012/FR-013
    """

    name = "UploadSharePointTool"

    def __call__(
        self,
        file_path: Path,
        folder_type: str,  # "publish" or "upload" (simplified)
        partner_name: str,
        quarter: str,
        run_id: str,
        evidence_dir: Path,
        demo_mode: bool = True,
    ) -> ToolResult:
        """Upload file to simulated SharePoint (demo) or real SharePoint (future).

        Args:
            file_path: Local file to upload (e.g., partner_error_report.xlsx for publish, 
                      or partner data file for upload)
            folder_type: "publish" to create link.json metadata in uploads/{partner_name}/ 
                         pointing to canonical file, or "upload" to copy partner files
            partner_name: Partner identifier (used in simulated folder structure)
            quarter: Quarter identifier (e.g., "Q1")
            run_id: Run identifier (for metadata only, not used in folder structure)
            evidence_dir: Evidence bundle directory (used to locate canonical file for publish)
            demo_mode: When True, use filesystem simulation; when False, hook up real SharePoint

        Returns:
            ToolResult with sharepoint_url and local_path in data.
        """
        if folder_type not in {"publish", "upload"}:
            return ToolResult(
                ok=False,
                summary=(
                    f"Invalid folder_type '{folder_type}' "
                    "(expected 'publish' or 'upload')"
                ),
                data={},
                warnings=[],
                blockers=[f"Invalid folder_type '{folder_type}'"],
            )

        # DEMO IMPLEMENTATION: Local filesystem "SharePoint" simulation
        if demo_mode:
            # SharePoint simulation lives at repo root: agentic_systems/sharepoint_simulation/
            # Go up from core/partner_communication to agentic_systems, then to sharepoint_simulation
            base_dir = Path(__file__).resolve().parents[2]  # Go up to agentic_systems
            base_sim_dir = base_dir / "sharepoint_simulation"
            
            # Simplified structure: only uploads/{partner_name}/ folder
            uploads_dir = base_sim_dir / "uploads" / partner_name
            uploads_dir.mkdir(parents=True, exist_ok=True)
            
            if folder_type == "publish":
                # Create link.json metadata artifact pointing to canonical file in outputs/
                # The canonical file is in the evidence bundle outputs/ folder
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
                
                # Write link.json to uploads/{partner_name}/ folder
                link_json_path = uploads_dir / "link.json"
                with open(link_json_path, 'w', encoding='utf-8') as f:
                    json.dump(link_metadata, f, indent=2)
                
                # Return file:// URL pointing to canonical file (not the link.json)
                sharepoint_url = f"file:///{canonical_path.as_posix()}"
                
                return ToolResult(
                    ok=True,
                    summary=(
                        f"Created link/metadata artifact in uploads/{partner_name}/ "
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
                # "upload" folder type: Copy the partner file (initial upload or corrected file)
                # File name convention: <partner>_<quarter>_<original_name>
                dest_name = f"{partner_name}_{quarter}_{file_path.name}"
                dest_path = uploads_dir / dest_name
                
                shutil.copy2(file_path, dest_path)
                
                # For demo: return a file:// URL pointing to the simulated SharePoint path
                sharepoint_url = f"file:///{dest_path.as_posix()}"
                
                return ToolResult(
                    ok=True,
                    summary=(
                        f"Uploaded file to simulated SharePoint uploads/{partner_name}/ at "
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



