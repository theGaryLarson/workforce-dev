"""OrchestratorAgent per orchestrator plan.

Deterministic orchestrator agent that coordinates intake runs, HITL pauses,
partner uploads, and resumes while reusing a single partner error report file.
Per BRD FR-011/FR-012/FR-013 and PRD-TRD Sections 5.2, 5.4, 7.1, 7.4.
"""

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_agent import BaseAgent
from .simple_intake_agent import SimpleIntakeAgent
from ..core.tools import ToolResult


class OrchestratorState(Enum):
    """Normalized orchestrator-level states."""
    COMPLETED_OK = "COMPLETED_OK"
    HALTED_VALIDATION_ERRORS = "HALTED_VALIDATION_ERRORS"
    HALTED_APPROVAL_REJECTED = "HALTED_APPROVAL_REJECTED"
    AWAITING_PARTNER_UPLOAD = "AWAITING_PARTNER_UPLOAD"
    RESUMED_VALIDATION_FAILED_AGAIN = "RESUMED_VALIDATION_FAILED_AGAIN"
    AWAITING_HITL = "AWAITING_HITL"
    READY_TO_RESUME = "READY_TO_RESUME"


@dataclass
class OrchestratorStateData:
    """Helper dataclass for orchestrator state tracking."""
    state: OrchestratorState
    halt_reason: Optional[str] = None
    current_phase: Optional[str] = None
    partner_error_report_path: Optional[str] = None
    last_corrected_file_path: Optional[str] = None
    resume_attempt_count: int = 0
    run_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['state'] = self.state.value
        return result


class OrchestratorAgent(BaseAgent):
    """Deterministic orchestrator agent extending BaseAgent contract.
    
    Coordinates intake runs, HITL pauses, partner uploads, and resumes
    while reusing a single partner error report file per run.
    """
    
    def __init__(
        self,
        run_id: Optional[str] = None,
        evidence_dir: Optional[Path] = None,
        sharepoint_sim_root: Optional[Path] = None,
        partner_uploads_dir: Optional[Path] = None
    ):
        """Initialize OrchestratorAgent.
        
        Args:
            run_id: Run identifier for evidence bundle
            evidence_dir: Directory for evidence bundle
            sharepoint_sim_root: Root directory for SharePoint simulation folders
            partner_uploads_dir: Directory to watch for initial partner uploads
        """
        super().__init__(run_id=run_id, evidence_dir=evidence_dir)
        self.sharepoint_sim_root = sharepoint_sim_root
        self.partner_uploads_dir = partner_uploads_dir
        self.state_data: Optional[OrchestratorStateData] = None
        
        # Register all tools used by orchestrator per PRD-TRD Section 5.1 BaseAgent contract
        # These special orchestration tools are handled in _invoke_tool() but must be registered
        # to pass BaseAgent.execute() tool existence check (line 191-193 in base_agent.py)
        self.tools = {
            'SimpleIntakeAgent': None,  # Created per run
            'inspect_run_status': None,  # Handled in _invoke_tool()
            'wait_for_partner_correction': None,  # Handled in _invoke_tool()
            'wait_for_initial_upload': None,  # Handled in _invoke_tool()
            'publish_error_report_internal': None,  # Handled in _invoke_tool()
            'publish_error_report_partner': None,  # Handled in _invoke_tool()
            'handle_persistent_failure': None,  # Handled in _invoke_tool()
        }
    
    def _inspect_run_status(self, run_id: str, evidence_dir: Path) -> OrchestratorStateData:
        """Read evidence bundle to determine halt reason and next state.
        
        Args:
            run_id: Run identifier
            evidence_dir: Evidence bundle directory
            
        Returns:
            OrchestratorStateData with normalized state
        """
        manifest_path = evidence_dir / "manifest.json"
        resume_state_path = evidence_dir / "resume_state.json"
        summary_path = evidence_dir / "summary.md"
        
        # Default state
        state = OrchestratorState.COMPLETED_OK
        halt_reason = None
        current_phase = None
        partner_error_report_path = None
        last_corrected_file_path = None
        resume_attempt_count = 0
        
        # Read manifest.json
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            hitl_status = manifest.get('hitl_status')
            staff_approval_status = manifest.get('staff_approval_status')
            resume_available = manifest.get('resume_available', False)
            
            if hitl_status == "halted":
                if staff_approval_status == "rejected":
                    state = OrchestratorState.HALTED_APPROVAL_REJECTED
                    halt_reason = "Staff approval rejected"
                    current_phase = "AWAITING_HITL"
                elif resume_available:
                    state = OrchestratorState.AWAITING_PARTNER_UPLOAD
                    halt_reason = "Validation errors - awaiting partner correction"
                    current_phase = "AWAITING_PARTNER"
                else:
                    state = OrchestratorState.HALTED_VALIDATION_ERRORS
                    halt_reason = "Validation errors"
                    current_phase = "AWAITING_HITL"
        
        # Read resume_state.json if it exists
        if resume_state_path.exists():
            with open(resume_state_path, 'r', encoding='utf-8') as f:
                resume_state = json.load(f)
            
            partner_error_report_path = resume_state.get('partner_error_report_path')
            last_corrected_file_path = resume_state.get('corrected_file_path')
            resume_attempt_count = resume_state.get('resume_attempt_count', 0)
            
            # Check if validation passed after resume
            validation_passed = resume_state.get('validation_passed', False)
            if resume_attempt_count > 0 and not validation_passed:
                state = OrchestratorState.RESUMED_VALIDATION_FAILED_AGAIN
                halt_reason = f"Validation failed again after {resume_attempt_count} resume attempt(s)"
                current_phase = "AWAITING_PARTNER"
            elif resume_attempt_count > 0 and validation_passed:
                state = OrchestratorState.COMPLETED_OK
                halt_reason = None
                current_phase = "COMPLETED"
        
        return OrchestratorStateData(
            state=state,
            halt_reason=halt_reason,
            current_phase=current_phase,
            partner_error_report_path=partner_error_report_path,
            last_corrected_file_path=last_corrected_file_path,
            resume_attempt_count=resume_attempt_count,
            run_id=run_id
        )
    
    def _detect_initial_file(self, partner: str, quarter: str) -> Optional[Path]:
        """Detect a new initial file for a (partner, quarter) using content signature.
        
        Uses column signature (partner field columns) and latest upload timestamp (mtime)
        to identify the most recent file that matches the expected partner data structure.
        
        Args:
            partner: Partner identifier
            quarter: Quarter identifier
            
        Returns:
            Path to initial file if found, None otherwise
        """
        # #region agent log
        try:
            with open(r"c:\Users\garyl\repos\cfa-projects\cfa-applied-agentic-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": self.run_id or "unknown",
                    "hypothesisId": "H2",
                    "location": "orchestrator_agent.py:_detect_initial_file:entry",
                    "message": "Checking for initial file using content signature",
                    "data": {
                        "partner": partner,
                        "quarter": quarter,
                        "partner_uploads_dir": str(self.partner_uploads_dir) if self.partner_uploads_dir else None,
                        "partner_uploads_dir_exists": bool(self.partner_uploads_dir and self.partner_uploads_dir.exists())
                    },
                    "timestamp": int(time.time() * 1000)
                }) + "\n")
        except Exception:
            pass
        # #endregion
        
        if not self.partner_uploads_dir or not self.partner_uploads_dir.exists():
            # #region agent log
            try:
                with open(r"c:\Users\garyl\repos\cfa-projects\cfa-applied-agentic-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": self.run_id or "unknown",
                        "hypothesisId": "H2",
                        "location": "orchestrator_agent.py:_detect_initial_file:early_return",
                        "message": "partner_uploads_dir is None or doesn't exist",
                        "data": {},
                        "timestamp": int(time.time() * 1000)
                    }) + "\n")
            except Exception:
                pass
            # #endregion
            return None
        
        # Find all files and match by content signature (column headers) + get latest by mtime
        candidate_files = []
        
        # #region agent log
        try:
            all_files = [p.name for p in self.partner_uploads_dir.iterdir() if p.is_file()]
            with open(r"c:\Users\garyl\repos\cfa-projects\cfa-applied-agentic-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": self.run_id or "unknown",
                    "hypothesisId": "H3",
                    "location": "orchestrator_agent.py:_detect_initial_file:scanning",
                    "message": "Scanning files for content signature",
                    "data": {
                        "all_files_in_dir": all_files
                    },
                    "timestamp": int(time.time() * 1000)
                }) + "\n")
        except Exception:
            pass
        # #endregion
        
        for file_path in self.partner_uploads_dir.iterdir():
            if not file_path.is_file():
                continue
            
            # Get content signature (columns + mtime)
            file_sig = self._get_file_column_signature(file_path)
            if not file_sig:
                continue
            
            columns, mtime = file_sig
            
            # Basic validation: ensure file has partner data columns
            # Check for common partner data fields (can be made configurable)
            required_columns = ['first name', 'last name', 'date of birth']
            columns_lower = ' '.join(columns).lower()
            has_required = any(req_col in columns_lower for req_col in required_columns)
            
            # #region agent log
            try:
                with open(r"c:\Users\garyl\repos\cfa-projects\cfa-applied-agentic-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": self.run_id or "unknown",
                        "hypothesisId": "H5",
                        "location": "orchestrator_agent.py:_detect_initial_file:signature_check",
                        "message": "Checking file content signature",
                        "data": {
                            "file_path": str(file_path),
                            "columns_count": len(columns),
                            "columns_sample": list(columns)[:10],
                            "required_columns": required_columns,
                            "columns_lower": columns_lower[:200],
                            "has_required": has_required
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + "\n")
            except Exception:
                pass
            # #endregion
            
            if has_required:
                candidate_files.append((file_path, mtime))
                # #region agent log
                try:
                    with open(r"c:\Users\garyl\repos\cfa-projects\cfa-applied-agentic-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": self.run_id or "unknown",
                            "hypothesisId": "H4",
                            "location": "orchestrator_agent.py:_detect_initial_file:candidate",
                            "message": "Found candidate file with valid content signature",
                            "data": {
                                "file_path": str(file_path),
                                "mtime": mtime,
                                "column_count": len(columns)
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + "\n")
                except Exception:
                    pass
                # #endregion
        
        if not candidate_files:
            # #region agent log
            try:
                with open(r"c:\Users\garyl\repos\cfa-projects\cfa-applied-agentic-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": self.run_id or "unknown",
                        "hypothesisId": "H4",
                        "location": "orchestrator_agent.py:_detect_initial_file:not_found",
                        "message": "No initial file found with valid content signature",
                        "data": {},
                        "timestamp": int(time.time() * 1000)
                    }) + "\n")
            except Exception:
                pass
            # #endregion
            return None
        
        # Return file with latest mtime (most recent upload)
        candidate_files.sort(key=lambda x: x[1], reverse=True)
        selected_file = candidate_files[0][0]
        
        # #region agent log
        try:
            with open(r"c:\Users\garyl\repos\cfa-projects\cfa-applied-agentic-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": self.run_id or "unknown",
                    "hypothesisId": "H4",
                    "location": "orchestrator_agent.py:_detect_initial_file:found",
                    "message": "Selected initial file by content signature and mtime",
                    "data": {
                        "file_path": str(selected_file),
                        "mtime": candidate_files[0][1],
                        "total_candidates": len(candidate_files)
                    },
                    "timestamp": int(time.time() * 1000)
                }) + "\n")
        except Exception:
            pass
        # #endregion
        
        return selected_file
    
    def _get_file_column_signature(self, file_path: Path) -> Optional[tuple]:
        """Extract column signature from a file for content-based matching.
        
        Args:
            file_path: Path to CSV or Excel file
            
        Returns:
            Tuple of (sorted column names tuple, mtime) or None if file can't be read
        """
        try:
            import pandas as pd
            
            # Read just the header row to get column names
            if file_path.suffix.lower() == '.csv':
                for encoding in ['utf-8', 'windows-1252', 'latin-1']:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding, nrows=0)
                        break
                    except (UnicodeDecodeError, pd.errors.EmptyDataError):
                        continue
                else:
                    return None
            elif file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path, engine='openpyxl', nrows=0)
            else:
                return None
            
            # Get column signature: sorted tuple of normalized column names
            columns = tuple(sorted([str(col).strip().lower() for col in df.columns]))
            
            # Get file modification time
            mtime = file_path.stat().st_mtime
            
            return (columns, mtime)
        except Exception:
            return None
    
    def _detect_corrected_file(self, run_id: str) -> Optional[Path]:
        """Detect corrected file in sharepoint_simulation/uploads/<run-id>/ using content signature.
        
        Uses column signature (partner field columns) and latest upload timestamp (mtime)
        to identify the most recent corrected file that matches the expected structure.
        
        Args:
            run_id: Run identifier
            
        Returns:
            Path to corrected file if found, None otherwise
        """
        uploads_dir = (self.sharepoint_sim_root / "uploads" / run_id) if self.sharepoint_sim_root else None

        if not uploads_dir or not uploads_dir.exists():
            return None

        # Get expected column signature from original file (if available)
        expected_signature = None
        if self.evidence_dir:
            resume_state_path = self.evidence_dir / "resume_state.json"
        last_processed_mtime = None
        if resume_state_path.exists():
            try:
                with open(resume_state_path, 'r', encoding='utf-8') as f:
                    resume_state = json.load(f)
                original_file_path = resume_state.get('original_file_path')
                if original_file_path:
                    orig_path = Path(original_file_path)
                    if orig_path.exists():
                        expected_signature = self._get_file_column_signature(orig_path)
                        if expected_signature:
                            expected_signature = tuple(expected_signature[0])  # Just column names, not mtime
                last_processed_mtime = resume_state.get('last_corrected_file_mtime')
                last_processed_file_path = resume_state.get('last_corrected_file_path')
                if not last_processed_mtime and last_processed_file_path:
                    try:
                        last_processed_mtime = Path(last_processed_file_path).stat().st_mtime
                    except Exception:
                        last_processed_mtime = None
            except Exception:
                pass

        # Find all files and match by signature + get latest by mtime
        candidate_files = []
        for file_path in uploads_dir.iterdir():
            if not file_path.is_file():
                continue
            
            file_sig = self._get_file_column_signature(file_path)
            if not file_sig:
                continue
            
            columns, mtime = file_sig

            # #region agent log
            try:
                with open(r"c:\Users\garyl\repos\cfa-projects\cfa-applied-agentic-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": self.run_id or "unknown",
                        "hypothesisId": "H4",
                        "location": "orchestrator_agent.py:_detect_corrected_file:file_sig",
                        "message": "Computed signature for corrected file candidate",
                        "data": {
                            "file_path": str(file_path),
                            "columns": columns,
                            "column_count": len(columns),
                            "matches_expected": bool(expected_signature and columns == tuple(expected_signature)),
                            "expected_signature_length": len(expected_signature) if expected_signature else None,
                            "last_processed_mtime": last_processed_mtime,
                            "candidate_mtime": mtime
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + "\n")
            except Exception:
                pass
            # #endregion

            candidate_sets_match = True
            if expected_signature:
                expected_set = set(expected_signature)
                candidate_set = set(columns)
                candidate_sets_match = expected_set.issubset(candidate_set)

            if candidate_sets_match:
                if last_processed_mtime and mtime <= last_processed_mtime:
                    continue
                candidate_files.append((file_path, mtime))
        
        # #region agent log
        try:
            with open(r"c:\Users\garyl\repos\cfa-projects\cfa-applied-agentic-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": self.run_id or "unknown",
                    "hypothesisId": "H4",
                    "location": "orchestrator_agent.py:_detect_corrected_file:candidates",
                    "message": "Evaluated corrected file candidates",
                    "data": {
                        "uploads_dir": str(uploads_dir),
                        "candidate_count": len(candidate_files),
                        "expected_signature": expected_signature,
                        "candidates": [str(path) for path, _ in candidate_files]
                    },
                    "timestamp": int(time.time() * 1000)
                }) + "\n")
        except Exception:
            pass
        # #endregion

        if not candidate_files:
            return None
        
        # Return file with latest mtime (most recent upload)
        candidate_files.sort(key=lambda x: x[1], reverse=True)
        return candidate_files[0][0]
    
    def plan(self, inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return structured execution steps based on current state.
        
        Args:
            inputs: Dictionary with 'partner', 'quarter', 'platform', etc.
            
        Returns:
            List of step dictionaries
        """
        partner = inputs.get('partner', 'demo')
        quarter = inputs.get('quarter', 'Q1')
        platform = inputs.get('platform', 'minimal')
        run_id = inputs.get('run_id') or f"{partner}-{quarter}-{platform}"
        
        steps = []
        
        # Check if this is an initial run or a resume
        if not self.evidence_dir:
            # Default evidence directory based on run_id
            base_dir = Path(__file__).resolve().parents[2]  # Go up to agentic_systems
            evidence_dir = base_dir / "core" / "audit" / "runs" / run_id
        else:
            evidence_dir = self.evidence_dir

        manifest_path = evidence_dir / "manifest.json"
        resume_state_path = evidence_dir / "resume_state.json"
        
        # #region agent log
        try:
            with open(r"c:\Users\garyl\repos\cfa-projects\cfa-applied-agentic-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": run_id,
                    "hypothesisId": "H1",
                    "location": "orchestrator_agent.py:plan:evidence_check",
                    "message": "Checking if run is existing or new",
                    "data": {
                        "evidence_dir": str(evidence_dir),
                        "evidence_dir_exists": evidence_dir.exists(),
                        "manifest_exists": manifest_path.exists(),
                        "resume_state_exists": resume_state_path.exists(),
                        "is_existing_run": bool(manifest_path.exists() or resume_state_path.exists())
                    },
                    "timestamp": int(time.time() * 1000)
                }) + "\n")
        except Exception:
            pass
        # #endregion
        
        # Treat this as an "existing run" only if we have evidence artifacts that indicate
        # an actual prior execution. The CLI creates the evidence_dir up-front, so
        # evidence_dir.exists() alone is not a reliable signal.
        #
        # Evidence-based signals:
        # - manifest.json: evidence bundle metadata (primary signal)
        # - resume_state.json: HITL/resume state for a halted run
        if (evidence_dir / "manifest.json").exists() or (evidence_dir / "resume_state.json").exists():
            # Existing run - inspect status
            self.state_data = self._inspect_run_status(run_id, evidence_dir)
            
            # #region agent log
            try:
                with open(r"c:\Users\garyl\repos\cfa-projects\cfa-applied-agentic-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": run_id,
                        "hypothesisId": "H1",
                        "location": "orchestrator_agent.py:plan:after_inspect",
                        "message": "After _inspect_run_status, checking state",
                        "data": {
                            "state": self.state_data.state.value if self.state_data and self.state_data.state else None,
                            "state_name": str(self.state_data.state) if self.state_data and self.state_data.state else None,
                            "halt_reason": self.state_data.halt_reason if self.state_data else None,
                            "current_phase": self.state_data.current_phase if self.state_data else None,
                            "resume_attempt_count": self.state_data.resume_attempt_count if self.state_data else None
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + "\n")
            except Exception:
                pass
            # #endregion
            
            steps.append({
                "step": "inspect_run_status",
                "tool": "inspect_run_status",
                "args": {"run_id": run_id}
            })

            corrected_file = self._detect_corrected_file(run_id)
            if corrected_file:
                steps.append({
                    "step": "resume_from_corrected_file",
                    "tool": "SimpleIntakeAgent",
                    "args": {
                        "run_id": run_id,
                        "corrected_file_path": str(corrected_file)
                    }
                })
                return steps

            # Plan next steps based on state
                if self.state_data.state == OrchestratorState.AWAITING_PARTNER_UPLOAD:
                    steps.append({
                        "step": "wait_for_partner_correction",
                        "tool": "wait_for_partner_correction",
                        "args": {"run_id": run_id}
                    })
                elif self.state_data.state == OrchestratorState.COMPLETED_OK:
                    steps.append({
                        "step": "publish_error_report_internal",
                        "tool": "publish_error_report_internal",
                        "args": {"run_id": run_id}
                    })
                elif self.state_data.state == OrchestratorState.HALTED_VALIDATION_ERRORS:
                    steps.append({
                        "step": "publish_error_report_internal",
                        "tool": "publish_error_report_internal",
                        "args": {"run_id": run_id}
                    })
                elif self.state_data.state == OrchestratorState.RESUMED_VALIDATION_FAILED_AGAIN:
                    if self.state_data.resume_attempt_count < 3:
                        steps.append({
                            "step": "publish_error_report_partner",
                            "tool": "publish_error_report_partner",
                            "args": {"run_id": run_id}
                        })
                        steps.append({
                            "step": "wait_for_partner_correction",
                            "tool": "wait_for_partner_correction",
                            "args": {"run_id": run_id}
                        })
                    else:
                        steps.append({
                            "step": "handle_persistent_failure",
                            "tool": "handle_persistent_failure",
                            "args": {"run_id": run_id}
                        })
        else:
            # New run - detect initial file and start intake
            # #region agent log
            try:
                with open(r"c:\Users\garyl\repos\cfa-projects\cfa-applied-agentic-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": run_id,
                        "hypothesisId": "H1",
                        "location": "orchestrator_agent.py:plan:new_run_branch",
                        "message": "Entering new run branch, calling _detect_initial_file",
                        "data": {
                            "partner": partner,
                            "quarter": quarter
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + "\n")
            except Exception:
                pass
            # #endregion
            initial_file = self._detect_initial_file(partner, quarter)
            # #region agent log
            try:
                with open(r"c:\Users\garyl\repos\cfa-projects\cfa-applied-agentic-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": run_id,
                        "hypothesisId": "H1",
                        "location": "orchestrator_agent.py:plan:after_detect",
                        "message": "After _detect_initial_file call",
                        "data": {
                            "initial_file": str(initial_file) if initial_file else None,
                            "initial_file_found": bool(initial_file)
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + "\n")
            except Exception:
                pass
            # #endregion
            if initial_file:
                steps.append({
                    "step": "ingest_and_validate_initial",
                    "tool": "SimpleIntakeAgent",
                    "args": {
                        "run_id": run_id,
                        "file_path": str(initial_file),
                        "partner": partner,
                        "quarter": quarter,
                        "platform": platform
                    }
                })
            else:
                steps.append({
                    "step": "wait_for_initial_upload",
                    "tool": "wait_for_initial_upload",
                    "args": {"partner": partner, "quarter": quarter}
                })
        
        # #region agent log
        try:
            with open(r"c:\Users\garyl\repos\cfa-projects\cfa-applied-agentic-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": run_id,
                    "hypothesisId": "H1",
                    "location": "orchestrator_agent.py:plan:return_steps",
                    "message": "Returning execution plan steps",
                    "data": {
                        "step_count": len(steps),
                        "steps": steps
                    },
                    "timestamp": int(time.time() * 1000)
                }) + "\n")
        except Exception:
            pass
        # #endregion
        
        return steps
    
    def _invoke_tool(self, tool_name: str, tool: Any, tool_args: Dict[str, Any],
                    context: Dict[str, Any]) -> ToolResult:
        """Invoke tool with prepared arguments.
        
        Override to handle orchestrator-specific tools and intake agent invocation.
        """
        if tool_name == "SimpleIntakeAgent":
            # Create intake agent for this run
            run_id = tool_args.get('run_id')
            if not self.evidence_dir:
                # Default evidence directory based on run_id
                base_dir = Path(__file__).resolve().parents[2]  # Go up to agentic_systems
                evidence_dir = base_dir / "core" / "audit" / "runs" / run_id
            else:
                evidence_dir = self.evidence_dir
            evidence_dir.mkdir(parents=True, exist_ok=True)
            
            intake_agent = SimpleIntakeAgent(run_id=run_id, evidence_dir=evidence_dir)
            
            # Check if this is a resume
            if 'corrected_file_path' in tool_args:
                # Resume workflow
                corrected_file_path = Path(tool_args['corrected_file_path'])
                # #region agent log
                try:
                    with open(r"c:\Users\garyl\repos\cfa-projects\cfa-applied-agentic-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": run_id,
                            "hypothesisId": "H6",
                            "location": "orchestrator_agent.py:_invoke_tool:resume_entry",
                            "message": "Preparing to resume intake with corrected file",
                            "data": {
                                "corrected_file_path": str(corrected_file_path),
                                "evidence_dir": str(evidence_dir)
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + "\n")
                except Exception:
                    pass
                # #endregion
                resume_inputs = {
                    "run_id": run_id,
                    "file_path": str(corrected_file_path)
                }
                results = intake_agent.resume(corrected_file_path, resume_inputs)
                
                # After resume, update evidence bundle artifacts (manifest.json, plan.md, summary.md, outputs/)
                # so the run reflects the latest validated/canonicalized state.
                try:
                    from ..core.audit.write_evidence import write_evidence_bundle
                    
                    plan_steps: list[dict[str, Any]] = [
                        {"tool": "IngestPartnerFileTool", "args": {"file_path": str(corrected_file_path)}},
                        {"tool": "ValidateStagedDataTool", "args": {}},
                        {"tool": "CollectWSACAggregatesTool", "args": {}},
                    ]
                    validate_tr = results.get("ValidateStagedDataTool")
                    if isinstance(validate_tr, ToolResult) and validate_tr.ok and validate_tr.data.get("error_count", 0) == 0:
                        plan_steps.append({"tool": "CanonicalizeStagedDataTool", "args": {}})
                    else:
                        plan_steps.append({"tool": "GeneratePartnerErrorReportTool", "args": {}})
                    
                    summary = intake_agent.summarize(results)
                    write_evidence_bundle(
                        run_id=run_id,
                        agent_name="SimpleIntakeAgent",
                        platform="minimal",
                        plan_steps=plan_steps,
                        summary=summary,
                        run_results=results,
                        evidence_dir=evidence_dir,
                        model=None,
                    )
                except Exception:
                    # Evidence writing should never crash resume orchestration.
                    pass

                # #region agent log
                try:
                    with open(r"c:\Users\garyl\repos\cfa-projects\cfa-applied-agentic-ai\.cursor\debug.log", "a", encoding="utf-8") as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": run_id,
                            "hypothesisId": "H7",
                            "location": "orchestrator_agent.py:_invoke_tool:resume_result",
                            "message": "Resume run returned results",
                            "data": {
                                "result_keys": list(results.keys()),
                                "_halted": results.get('_halted'),
                                "_halt_reason": results.get('_halt_reason'),
                                "validation_errors": len(results.get('validation_errors', [])) if results.get('validation_errors') else None,
                                "canonicalized": results.get('canonicalized', False)
                            },
                            "timestamp": int(time.time() * 1000)
                        }) + "\n")
                except Exception:
                    pass
                # #endregion
                
                # Convert results to ToolResult
                if results.get('_halted'):
                    return ToolResult(
                        ok=False,
                        summary=f"Resume halted: {results.get('_halt_reason', 'Unknown reason')}",
                        data=results,
                        warnings=[],
                        blockers=[results.get('_halt_reason', 'Unknown reason')]
                    )
                else:
                    return ToolResult(
                        ok=True,
                        summary="Resume completed successfully",
                        data=results,
                        warnings=[],
                        blockers=[]
                    )
            else:
                # Initial run
                file_path = tool_args.get('file_path')
                inputs = {
                    "file_path": file_path,
                    "run_id": run_id,
                    "partner": tool_args.get('partner', 'demo'),
                    "quarter": tool_args.get('quarter', 'Q1')
                }
                
                plan_steps = intake_agent.plan(inputs)
                results = intake_agent.execute(inputs)
                summary = intake_agent.summarize(results)
                
                # Write evidence bundle
                from ..core.audit.write_evidence import write_evidence_bundle
                write_evidence_bundle(
                    run_id=run_id,
                    agent_name="SimpleIntakeAgent",
                    platform=tool_args.get('platform', 'minimal'),
                    plan_steps=plan_steps,
                    summary=summary,
                    run_results=results,
                    evidence_dir=evidence_dir
                )
                
                # Check if halted
                if results.get('_halted'):
                    return ToolResult(
                        ok=False,
                        summary=f"Intake halted: {results.get('_halt_reason', 'Unknown reason')}",
                        data=results,
                        warnings=[],
                        blockers=[results.get('_halt_reason', 'Unknown reason')]
                    )
                else:
                    return ToolResult(
                        ok=True,
                        summary="Intake completed successfully",
                        data=results,
                        warnings=[],
                        blockers=[]
                    )
        elif tool_name == "inspect_run_status":
            # Already done in plan() - return state data
            return ToolResult(
                ok=True,
                summary=f"Run status: {self.state_data.state.value}",
                data=self.state_data.to_dict() if self.state_data else {},
                warnings=[],
                blockers=[]
            )
        elif tool_name in ["wait_for_partner_correction", "wait_for_initial_upload"]:
            # Polling step - return indication that we should wait with error status info
            run_id = tool_args.get('run_id')
            error_info = {}
            
            # Read error status from resume_state.json if available
            if run_id and self.evidence_dir:
                resume_state_path = self.evidence_dir / "resume_state.json"
                if resume_state_path.exists():
                    try:
                        with open(resume_state_path, 'r', encoding='utf-8') as f:
                            resume_state = json.load(f)
                        
                        violations = resume_state.get('validation_violations', [])
                        error_count = len([v for v in violations if v.get('severity', 'Error') == 'Error'])
                        warning_count = len([v for v in violations if v.get('severity') == 'Warning'])
                        resume_attempt_count = resume_state.get('resume_attempt_count', 0)
                        validation_passed = resume_state.get('validation_passed', False)
                        
                        error_info = {
                            "error_count": error_count,
                            "warning_count": warning_count,
                            "resume_attempt_count": resume_attempt_count,
                            "validation_passed": validation_passed,
                            "has_errors": error_count > 0
                        }
                    except Exception:
                        pass
            
            # Build informative summary message
            if error_info.get('has_errors'):
                if error_info.get('resume_attempt_count', 0) > 0:
                    summary = f"Waiting for partner correction (attempt {error_info['resume_attempt_count'] + 1}): {error_info['error_count']} errors still present"
                else:
                    summary = f"Waiting for partner correction: {error_info['error_count']} errors found"
            else:
                summary = f"Waiting for {tool_name}"
            
            return ToolResult(
                ok=True,
                summary=summary,
                data={"waiting": True, **error_info},
                warnings=[],
                blockers=[]
            )
        elif tool_name in ["publish_error_report_internal", "publish_error_report_partner"]:
            # Publish error report to SharePoint simulation
            run_id = tool_args.get('run_id')
            folder_type = "internal" if "internal" in tool_name else "partner"
            
            if not self.evidence_dir:
                # Default evidence directory based on run_id
                base_dir = Path(__file__).resolve().parents[2]  # Go up to agentic_systems
                evidence_dir = base_dir / "core" / "audit" / "runs" / run_id
            else:
                evidence_dir = self.evidence_dir
            error_report_path = evidence_dir / "outputs" / "partner_error_report.xlsx"
            
            if not error_report_path.exists():
                return ToolResult(
                    ok=False,
                    summary=f"Error report not found: {error_report_path}",
                    data={},
                    warnings=[],
                    blockers=[f"Error report not found: {error_report_path}"]
                )
            
            # Use UploadSharePointTool to create link/metadata artifact
            from ..core.partner_communication.upload_sharepoint_tool import UploadSharePointTool
            upload_tool = UploadSharePointTool()
            
            # Extract partner and quarter from run_id
            parts = run_id.split('-')
            partner = parts[0] if len(parts) > 0 else 'demo'
            quarter = parts[1] if len(parts) > 1 else 'Q1'
            
            result = upload_tool(
                file_path=error_report_path,
                folder_type=folder_type,
                partner_name=partner,
                quarter=quarter,
                run_id=run_id,
                evidence_dir=evidence_dir,
                demo_mode=True
            )
            
            return result
        elif tool_name == "handle_persistent_failure":
            # Mark run as terminal
            run_id = tool_args.get('run_id')
            if not self.evidence_dir:
                # Default evidence directory based on run_id
                base_dir = Path(__file__).resolve().parents[2]  # Go up to agentic_systems
                evidence_dir = base_dir / "core" / "audit" / "runs" / run_id
            else:
                evidence_dir = self.evidence_dir
            
            # Update manifest
            manifest_path = evidence_dir / "manifest.json"
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                manifest['orchestrator_status'] = 'persistent_failure'
                manifest['last_orchestrator_action'] = 'handle_persistent_failure'
                with open(manifest_path, 'w', encoding='utf-8') as f:
                    json.dump(manifest, f, indent=2)
            
            return ToolResult(
                ok=False,
                summary="Persistent validation failures - run marked as terminal",
                data={"terminal": True},
                warnings=[],
                blockers=["Maximum resume attempts exceeded"]
            )
        else:
            return super()._invoke_tool(tool_name, tool, tool_args, context)
    
    def summarize(self, run_results: Dict[str, Any]) -> str:
        """Produce a staff-facing summary describing decisions and outcomes.
        
        Args:
            run_results: Dictionary of tool execution results
            
        Returns:
            Human-readable summary string
        """
        summary_parts = ["# Orchestrator Summary\n"]
        
        if self.state_data:
            summary_parts.append(f"**State:** {self.state_data.state.value}")
            summary_parts.append(f"**Phase:** {self.state_data.current_phase or 'N/A'}")
            if self.state_data.halt_reason:
                summary_parts.append(f"**Halt Reason:** {self.state_data.halt_reason}")
            if self.state_data.resume_attempt_count > 0:
                summary_parts.append(f"**Resume Attempts:** {self.state_data.resume_attempt_count}")
        
        # Summarize tool results
        for tool_name, result in run_results.items():
            if isinstance(result, ToolResult):
                summary_parts.append(f"\n**{tool_name}:** {result.summary}")
        
        return "\n".join(summary_parts) if summary_parts else "No results to summarize"

