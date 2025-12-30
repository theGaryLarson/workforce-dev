"""SimpleIntakeAgent per PRD-TRD Section 5.1.

Deterministic baseline agent demonstrating BaseAgent contract with hardcoded orchestration.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .base_agent import BaseAgent
from ..core.tools import ToolResult
from ..core.canonical.canonicalize_tool import CanonicalizeStagedDataTool
from ..core.ingestion.ingest_tool import IngestPartnerFileTool
from ..core.validation.validate_tool import ValidateStagedDataTool
from ..core.partner_communication.collect_wsac_aggregates_tool import CollectWSACAggregatesTool
from ..core.partner_communication.generate_error_report_tool import GeneratePartnerErrorReportTool
from ..core.partner_communication.generate_email_tool import GeneratePartnerEmailTool
from ..core.partner_communication.secure_link_tool import CreateSecureLinkTool
from ..core.partner_communication.request_approval_tool import RequestStaffApprovalTool
from ..core.partner_communication.upload_sharepoint_tool import UploadSharePointTool


class SimpleIntakeAgent(BaseAgent):
    """Simple deterministic intake agent extending BaseAgent contract per PRD-TRD Section 5.1.
    
    Demonstrates contract-first agent design pattern with hardcoded orchestration.
    Implements plan(), execute(), and summarize() methods.
    """
    
    def __init__(self, run_id: str = None, evidence_dir: Path = None):
        """Initialize SimpleIntakeAgent.
        
        Args:
            run_id: Run identifier for evidence bundle
            evidence_dir: Directory for evidence bundle (where tool_calls.jsonl is written)
        """
        super().__init__(run_id=run_id, evidence_dir=evidence_dir)
        
        # Initialize tools per PRD-TRD Section 5.4
        self.ingest_tool = IngestPartnerFileTool()
        self.validate_tool = ValidateStagedDataTool()
        self.canonicalize_tool = CanonicalizeStagedDataTool()
        
        # Part 3: HITL partner communication tools per BRD FR-012
        self.wsac_aggregates_tool = CollectWSACAggregatesTool()
        self.error_report_tool = GeneratePartnerErrorReportTool()
        self.email_tool = GeneratePartnerEmailTool()
        self.secure_link_tool = CreateSecureLinkTool()
        self.approval_tool = RequestStaffApprovalTool()
        self.upload_sharepoint_tool = UploadSharePointTool()
        
        # Tool registry for execute() - populated in BaseAgent
        self.tools = {
            'IngestPartnerFileTool': self.ingest_tool,
            'ValidateStagedDataTool': self.validate_tool,
            'CanonicalizeStagedDataTool': self.canonicalize_tool,
        }
    
    def _categorize_violation(self, violation: Dict[str, Any]) -> str:
        """Categorize violation into specific error type for error summary.
        
        Uses specific patterns first (most specific), then general patterns.
        Ensures categories are mutually exclusive to prevent double-counting.
        
        Args:
            violation: Violation dict with 'message' and 'field' keys
        
        Returns:
            Category string: 'active_past_graduation', 'status_validation', 
            'required_field', 'address_validation', 'date_validation', 
            'zip_code_format', 'employment_validation', or 'other'
        """
        message_lower = violation.get('message', '').lower()
        field_lower = violation.get('field', '').lower()
        
        # Specific patterns first (most specific to avoid overlap)
        
        # Active Past Graduation: Participant marked "Currently active" but end_date has passed
        # (This rule is mentioned in BRD but not yet implemented in validate_tool.py)
        # Reserved category for when rule is implemented
        if 'currently active' in message_lower and 'past' in message_lower:
            return 'active_past_graduation'
        
        # Status Validation: Exit date in past but wrong status
        if 'training exit date' in message_lower and 'past' in message_lower:
            return 'status_validation'
        
        # Status Validation: Missing noncompletion reason when withdrawn/terminated
        if 'withdrawn/terminated' in message_lower and 'required' in message_lower:
            return 'status_validation'
        
        # Status Validation: Missing completion fields when graduated/completed
        if 'graduated/completed' in message_lower and 'required' in message_lower:
            return 'status_validation'
        
        # Status Validation: Status field is required but missing
        if 'current program status' in field_lower and 'required' in message_lower:
            return 'status_validation'
        
        # Status Validation: Any other status-related validation
        if 'status' in message_lower or 'current program status' in field_lower:
            return 'status_validation'
        
        # General patterns (only if not already categorized)
        
        # Required Field: Missing required fields (excluding status which is handled above)
        if 'required' in message_lower or 'missing' in message_lower:
            return 'required_field'
        
        # Address Validation: Address-related errors
        if 'address' in message_lower or 'apartment' in message_lower or 'suite' in message_lower or 'unit' in message_lower or 'po box' in message_lower:
            return 'address_validation'
        
        # Date Validation: Date format, range, or validity errors
        if 'date' in message_lower:
            return 'date_validation'
        
        # Zip Code Format: Zip code format errors
        if 'zip' in message_lower or 'postal' in message_lower:
            return 'zip_code_format'
        
        # Employment Validation: Employment-related errors
        if 'employment' in message_lower or 'employer' in message_lower or 'job' in message_lower or 'wage' in message_lower or 'earnings' in message_lower:
            return 'employment_validation'
        
        # Other: Unclassified errors
        return 'other'
    
    def plan(self, inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return structured execution steps per PRD-TRD Section 5.1.
        
        Human-readable plan.md is generated from structured steps by write_evidence.py
        per BRD FR-011.
        
        Args:
            inputs: Dictionary containing file_path and run_id
            
        Returns:
            List of step dictionaries, each with 'tool' and 'args' keys
        """
        file_path = inputs.get('file_path')
        
        # Return structured steps for ingest → validate → canonicalize sequence
        return [
            {
                'tool': 'IngestPartnerFileTool',
                'args': {'file_path': file_path}
            },
            {
                'tool': 'ValidateStagedDataTool',
                'args': {}  # Will receive dataframe from previous step
            },
            {
                'tool': 'CanonicalizeStagedDataTool',
                'args': {}  # Will receive dataframe from previous step
            }
        ]
    
    def _invoke_tool(self, tool_name: str, tool: Any, tool_args: Dict[str, Any], 
                    context: Dict[str, Any]) -> ToolResult:
        """Invoke tool, handling special cases where tools take DataFrames as positional args.
        
        Args:
            tool_name: Name of the tool
            tool: Tool instance
            tool_args: Prepared arguments dictionary
            context: Execution context
        
        Returns:
            ToolResult from tool execution
        """
        # Some tools take DataFrames as positional arguments, not keyword arguments
        if tool_name in ['ValidateStagedDataTool', 'CanonicalizeStagedDataTool']:
            if 'dataframe' in tool_args:
                # These tools take DataFrame as positional parameter
                dataframe = tool_args.pop('dataframe')
                return tool(dataframe)
        
        # Default: invoke with keyword arguments
        return tool(**tool_args)

    def _prepare_tool_args(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Inject staged_dataframe into tool args when needed.
        
        Args:
            step: Step dictionary with 'tool' and 'args' keys
            context: Execution context (e.g., staged_dataframe from previous steps)
        
        Returns:
            Prepared arguments dictionary
        """
        tool_name = step['tool']
        args = step['args'].copy()
        
        # Inject DataFrame from context for tools that need it
        if tool_name in ['ValidateStagedDataTool', 'CanonicalizeStagedDataTool']:
            if 'staged_dataframe' in context:
                args['dataframe'] = context['staged_dataframe']
        
        return args

    def _handle_tool_result(self, step: Dict[str, Any], result: ToolResult, 
                           context: Dict[str, Any]) -> None:
        """Update context with DataFrames for chaining between steps.
        
        Args:
            step: Step dictionary
            result: ToolResult from tool execution
            context: Execution context (can be modified)
        """
        tool_name = step['tool']
        
        # Store DataFrames in context for chaining
        if tool_name == 'IngestPartnerFileTool' and result.ok:
            context['staged_dataframe'] = result.data.get('dataframe')
        elif tool_name == 'ValidateStagedDataTool' and result.ok:
            # Validation doesn't modify the dataframe, pass it through
            # staged_dataframe should already be in context from previous step
            pass
        elif tool_name == 'CanonicalizeStagedDataTool' and result.ok:
            context['canonical_dataframe'] = result.data.get('canonical_dataframe')
    
    def _handle_custom_orchestration(self, step: Dict[str, Any], result: ToolResult,
                                    context: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle HITL workflow after validation per BRD FR-012.
        
        Args:
            step: Completed step dictionary
            result: ToolResult from step
            context: Execution context
            inputs: Original inputs
        
        Returns:
            Dictionary of additional results from HITL workflow
        """
        tool_name = step['tool']
        results = {}
        
        # Part 3: HITL workflow per BRD FR-012
        # After validation, check for errors and trigger HITL workflow if needed
        if tool_name == 'ValidateStagedDataTool':
            violations = result.data.get('violations', [])
            error_count = result.data.get('error_count', 0)
            
            # If errors found, trigger HITL workflow per BRD FR-012
            if error_count > 0:
                # Get partner name and quarter from inputs (passed from CLI)
                partner_name = inputs.get('partner_name', 'Partner')
                quarter = inputs.get('quarter', 'Q1')
                year = inputs.get('year', str(datetime.now().year))
                
                # Get staged_dataframe from context
                staged_dataframe = context.get('staged_dataframe')
                
                # Collect aggregates from partner data for WSAC submission per BRD FR-004
                self._emit("STEP_START", "Collecting WSAC aggregates from partner data", {
                    "tool": "CollectWSACAggregatesTool"
                })
                
                wsac_result = self.wsac_aggregates_tool(
                    partner_dataframe=staged_dataframe,
                    quarter=quarter,
                    year=int(year) if year.isdigit() else datetime.now().year,
                    wraparound_funding=None  # Will be collected via staff input if needed
                )
                
                self._emit("STEP_END", "Completed CollectWSACAggregatesTool", {
                    "tool": "CollectWSACAggregatesTool",
                    **self._sanitize_tool_result(wsac_result)
                })
                
                aggregates = wsac_result.data.get('aggregates') if wsac_result.ok else None
                
                # Generate error report per BRD FR-012
                # Use Excel format for better user experience (color-coding, comments, action guidance)
                error_report_path = self.evidence_dir / "outputs" / "partner_error_report.xlsx"
                error_report_path.parent.mkdir(parents=True, exist_ok=True)
                
                self._emit("STEP_START", "Generating partner error report", {
                    "tool": "GeneratePartnerErrorReportTool"
                })
                
                error_report_result = self.error_report_tool(
                    staged_dataframe=staged_dataframe,
                    violations=violations,
                    aggregates=aggregates,  # Pass aggregates to include in report
                    output_path=error_report_path
                )
                
                self._emit("STEP_END", "Completed GeneratePartnerErrorReportTool", {
                    "tool": "GeneratePartnerErrorReportTool",
                    **self._sanitize_tool_result(error_report_result)
                })
                
                results['GeneratePartnerErrorReportTool'] = error_report_result
                
                # Generate email template per BRD FR-012
                self._emit("STEP_START", "Generating partner email", {
                    "tool": "GeneratePartnerEmailTool"
                })
                
                email_result = self.email_tool(
                    error_report_path=error_report_path,
                    violations=violations,
                    partner_name=partner_name,
                    quarter=quarter,
                    year=year
                )
                
                self._emit("STEP_END", "Completed GeneratePartnerEmailTool", {
                    "tool": "GeneratePartnerEmailTool",
                    **self._sanitize_tool_result(email_result)
                })
                
                results['GeneratePartnerEmailTool'] = email_result
                
                # Stage 1: Upload review worksheet to internal SharePoint/Dataverse
                # For the POC, this uses a local "sharepoint_simulation" directory
                # under the evidence bundle to avoid external dependencies.
                self._emit("STEP_START", "Uploading review worksheet to internal SharePoint (simulated)", {
                    "tool": "UploadSharePointTool",
                    "stage": "internal"
                })

                internal_upload_result = self.upload_sharepoint_tool(
                    file_path=error_report_path,
                    folder_type="internal",
                    partner_name=partner_name,
                    quarter=quarter,
                    run_id=self.run_id,
                    evidence_dir=self.evidence_dir,
                    demo_mode=True,  # PRODUCTION: set to False and use real SharePointClient
                )

                self._emit("STEP_END", "Completed UploadSharePointTool (internal)", {
                    "tool": "UploadSharePointTool",
                    "stage": "internal",
                    "sharepoint_url": internal_upload_result.data.get("sharepoint_url"),
                    **self._sanitize_tool_result(internal_upload_result)
                })

                results['UploadSharePointTool_internal'] = internal_upload_result

                # Request staff approval per BRD FR-012
                # Categorize violations using precise pattern matching to avoid double-counting
                error_summary = {
                    'total_errors': error_count,
                    'total_warnings': result.data.get('warning_count', 0),
                    'required_field': len([v for v in violations if self._categorize_violation(v) == 'required_field']),
                    'active_past_graduation': len([v for v in violations if self._categorize_violation(v) == 'active_past_graduation']),
                    'zip_code_format': len([v for v in violations if self._categorize_violation(v) == 'zip_code_format']),
                    'date_validation': len([v for v in violations if self._categorize_violation(v) == 'date_validation']),
                    'address_validation': len([v for v in violations if self._categorize_violation(v) == 'address_validation']),
                    'status_validation': len([v for v in violations if self._categorize_violation(v) == 'status_validation']),
                    'employment_validation': len([v for v in violations if self._categorize_violation(v) == 'employment_validation']),
                    'other': len([v for v in violations if self._categorize_violation(v) == 'other']),
                }
                
                self._emit("STEP_START", "Requesting staff approval", {
                    "tool": "RequestStaffApprovalTool"
                })
                
                approval_result = self.approval_tool(
                    email_content=email_result.data.get('email_content', ''),
                    error_report_path=error_report_path,
                    internal_report_url=internal_upload_result.data.get('sharepoint_url'),
                    error_summary=error_summary,
                    aggregates=aggregates,  # Pass aggregates for staff review
                    partner_name=partner_name,
                    quarter=quarter,
                    year=year,
                    demo_mode=True,
                    approval_recipients=None,  # PRODUCTION: pass Teams channel/user group here
                )
                
                sanitized_approval = self._sanitize_tool_result(approval_result)
                sanitized_approval["approval_status"] = approval_result.data.get('approval_status')
                self._emit("STEP_END", "Completed RequestStaffApprovalTool", {
                    "tool": "RequestStaffApprovalTool",
                    **sanitized_approval
                })
                
                results['RequestStaffApprovalTool'] = approval_result
                
                # If approved, upload partner-facing copy and create secure link per BRD FR-013
                if approval_result.ok and approval_result.data.get('approval_status') == 'approved':
                    # Stage 2: Upload report to partner-accessible location
                    # For the POC, this is also a simulated SharePoint directory.
                    self._emit("STEP_START", "Uploading report to partner-accessible SharePoint (simulated)", {
                        "tool": "UploadSharePointTool",
                        "stage": "partner"
                    })

                    partner_upload_result = self.upload_sharepoint_tool(
                        file_path=error_report_path,
                        folder_type="partner",
                        partner_name=partner_name,
                        quarter=quarter,
                        run_id=self.run_id,
                        evidence_dir=self.evidence_dir,
                        demo_mode=True,  # PRODUCTION: set to False and use real SharePointClient
                    )

                    self._emit("STEP_END", "Completed UploadSharePointTool (partner)", {
                        "tool": "UploadSharePointTool",
                        "stage": "partner",
                        "sharepoint_url": partner_upload_result.data.get("sharepoint_url"),
                        **self._sanitize_tool_result(partner_upload_result)
                    })

                    results['UploadSharePointTool_partner'] = partner_upload_result

                    self._emit("STEP_START", "Creating secure link", {
                        "tool": "CreateSecureLinkTool"
                    })
                    
                    secure_link_result = self.secure_link_tool(
                        error_report_path=error_report_path,
                        evidence_dir=self.evidence_dir,
                        run_id=self.run_id,
                        # In the POC, this is a file:// URL from UploadSharePointTool.
                        # PRODUCTION: this would be a real SharePoint URL that
                        # SecureLinkGenerator wraps with code-based or AAD-auth link.
                        # BRD FR-013: Secure link is generated only after staff approval.
                        sharepoint_url=partner_upload_result.data.get("sharepoint_url"),
                    )
                    
                    self._emit("STEP_END", "Completed CreateSecureLinkTool", {
                        "tool": "CreateSecureLinkTool",
                        **self._sanitize_tool_result(secure_link_result)
                    })
                    
                    results['CreateSecureLinkTool'] = secure_link_result

                    # After secure link is created, regenerate partner email so that
                    # the message sent to the partner contains the actual secure link
                    # and access code instead of placeholders.
                    # BRD FR-012 / FR-013: Email with secure link is only prepared
                    # after staff approval and secure link generation.
                    secure_link_url = secure_link_result.data.get("secure_link_url")
                    access_code = secure_link_result.data.get("access_code")

                    self._emit("STEP_START", "Regenerating partner email with secure link", {
                        "tool": "GeneratePartnerEmailTool",
                        "stage": "post_approval"
                    })

                    final_email_result = self.email_tool(
                        error_report_path=error_report_path,
                        violations=violations,
                        partner_name=partner_name,
                        quarter=quarter,
                        year=year,
                        secure_link_url=secure_link_url,
                        access_code=access_code,
                    )

                    self._emit("STEP_END", "Completed GeneratePartnerEmailTool (post_approval)", {
                        "tool": "GeneratePartnerEmailTool",
                        "stage": "post_approval",
                        **self._sanitize_tool_result(final_email_result)
                    })

                    # Keep both initial (staff preview) and final (partner-facing) emails
                    # in results; the final result is the one written to evidence outputs.
                    # BRD FR-011 / FR-012: Evidence bundle must capture the actual
                    # partner communication content.
                    results['GeneratePartnerEmailTool_initial'] = email_result
                    results['GeneratePartnerEmailTool'] = final_email_result

                    # TODO: Send email to partner (demo: just log it)
                    # PRODUCTION: Use email service API to send email
                    print(f"\n[DEMO] Email would be sent to partner with secure link: {secure_link_url}")
                    print(f"[DEMO] Access code: {access_code}")
                    
                    # Store resume state per BRD FR-012 and orchestrator plan
                    # Per orchestrator plan: Include halt_reason, current_phase, partner_error_report_path
                    error_report_path = self.evidence_dir / "outputs" / "partner_error_report.xlsx"
                    resume_state = {
                        "run_id": self.run_id,
                        "original_file_path": str(inputs.get('file_path')),
                        "validation_violations": violations,
                        "secure_link_code": secure_link_result.data.get('access_code'),
                        "secure_link_url": secure_link_result.data.get('secure_link_url'),
                        "halted_at": "ValidateStagedDataTool",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "partner_name": partner_name,
                        "quarter": quarter,
                        "year": year,
                        # Orchestrator fields per orchestrator plan
                        "halt_reason": "Validation errors - awaiting partner correction",
                        "current_phase": "AWAITING_PARTNER",
                        "partner_error_report_path": str(error_report_path.resolve()),
                        "last_corrected_file_path": None,
                        "resume_attempt_count": 0
                    }
                    
                    resume_state_path = self.evidence_dir / "resume_state.json"
                    with open(resume_state_path, 'w', encoding='utf-8') as f:
                        json.dump(resume_state, f, indent=2)
                    
                    # Halt execution and wait for partner corrections per BRD FR-012
                    results['_halted'] = True
                    results['_halt_reason'] = "Validation errors found - waiting for partner corrections"
                    return results
                
                # If rejected, halt execution with rejection reason per BRD FR-012
                else:
                    results['_halted'] = True
                    results['_halt_reason'] = f"Staff approval rejected: {approval_result.data.get('staff_comments', 'No reason provided')}"
                    return results
        
        return results
    
    def summarize(self, run_results: Dict[str, Any]) -> str:
        """Produce staff-facing summary per PRD-TRD Section 5.1.
        
        Summary written to summary.md in evidence bundle per BRD FR-011.
        
        Args:
            run_results: Dictionary of tool execution results from execute()
            
        Returns:
            Human-readable summary string
        """
        ingest_result = run_results.get('IngestPartnerFileTool')
        validate_result = run_results.get('ValidateStagedDataTool')
        canonicalize_result = run_results.get('CanonicalizeStagedDataTool')
        
        summary_parts = []
        
        if ingest_result:
            summary_parts.append(f"File processed: {ingest_result.summary}")
        
        if validate_result:
            error_count = validate_result.data.get('error_count', 0)
            warning_count = validate_result.data.get('warning_count', 0)
            summary_parts.append(f"Validation: {error_count} errors, {warning_count} warnings")
            if validate_result.blockers:
                summary_parts.append(f"Blockers: {', '.join(validate_result.blockers)}")
        
        if canonicalize_result:
            record_count = canonicalize_result.data.get('record_count', 0)
            summary_parts.append(f"Canonicalized: {record_count} records")
        
        return "\n".join(summary_parts) if summary_parts else "No results to summarize"
    
    def resume(self, corrected_file_path: Path, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Resume processing with corrected file per BRD FR-012.
        
        Loads resume state from evidence bundle, re-validates corrected file,
        and continues to canonicalization if validation passes.
        
        Args:
            corrected_file_path: Path to corrected file from partner
            inputs: Dictionary containing run_id and other context
        
        Returns:
            Dictionary with step outcomes (same format as execute())
        """
        # Load resume state from evidence bundle
        resume_state_path = self.evidence_dir / "resume_state.json"
        if not resume_state_path.exists():
            return {
                '_halted': True,
                '_halt_reason': 'Resume state not found - cannot resume'
            }
        
        with open(resume_state_path, 'r', encoding='utf-8') as f:
            resume_state = json.load(f)
        
        corrected_file_mtime = None
        try:
            corrected_file_mtime = corrected_file_path.stat().st_mtime
        except OSError:
            corrected_file_mtime = None

        # Re-run ingestion on corrected file
        self._emit("STEP_START", "Re-ingesting corrected file", {
            "tool": "IngestPartnerFileTool",
            "file_path": str(corrected_file_path)
        })
        
        ingest_result = self.ingest_tool(file_path=str(corrected_file_path))
        staged_dataframe = ingest_result.data.get('dataframe') if ingest_result.ok else None
        
        self._emit("STEP_END", "Completed re-ingestion", {
            "tool": "IngestPartnerFileTool",
            "ok": ingest_result.ok,
            "row_count": ingest_result.data.get('row_count', 0) if ingest_result.ok else 0
        })
        
        if not ingest_result.ok:
            return {
                'IngestPartnerFileTool': ingest_result,
                '_halted': True,
                '_halt_reason': 'Failed to ingest corrected file'
            }
        
        # Re-run validation
        self._emit("STEP_START", "Re-validating corrected file", {
            "tool": "ValidateStagedDataTool"
        })
        
        validate_result = self.validate_tool(staged_dataframe)
        violations = validate_result.data.get('violations', [])
        error_count = validate_result.data.get('error_count', 0)
        
        self._emit("STEP_END", "Completed re-validation", {
            "tool": "ValidateStagedDataTool",
            "ok": validate_result.ok,
            "error_count": error_count,
            "warning_count": validate_result.data.get('warning_count', 0)
        })
        
        # Re-collect aggregates from corrected data per BRD FR-004
        partner_name = resume_state.get('partner_name', 'Partner')
        quarter = resume_state.get('quarter', 'Q1')
        year = resume_state.get('year', str(datetime.now().year))
        
        self._emit("STEP_START", "Re-collecting WSAC aggregates from corrected data", {
            "tool": "CollectWSACAggregatesTool"
        })
        
        wsac_result = self.wsac_aggregates_tool(
            partner_dataframe=staged_dataframe,
            quarter=quarter,
            year=int(year) if year.isdigit() else datetime.now().year,
            wraparound_funding=None  # Or load from previous run if needed
        )
        
        self._emit("STEP_END", "Completed CollectWSACAggregatesTool (resume)", {
            "tool": "CollectWSACAggregatesTool",
            "ok": wsac_result.ok,
            "total_participants": wsac_result.data.get('aggregates', {}).get('total_participants', 0) if wsac_result.ok else 0
        })
        
        aggregates = wsac_result.data.get('aggregates') if wsac_result.ok else None
        
        results = {
            'IngestPartnerFileTool': ingest_result,
            'ValidateStagedDataTool': validate_result,
            'CollectWSACAggregatesTool': wsac_result,
            'validation_errors': violations
        }
        
        # If validation passes, continue to canonicalization
        if validate_result.ok and error_count == 0:
            self._emit("STEP_START", "Canonicalizing corrected data", {
                "tool": "CanonicalizeStagedDataTool"
            })
            
            canonicalize_result = self.canonicalize_tool(staged_dataframe)
            
            self._emit("STEP_END", "Completed canonicalization", {
                "tool": "CanonicalizeStagedDataTool",
                "ok": canonicalize_result.ok,
                "record_count": canonicalize_result.data.get('record_count', 0) if canonicalize_result.ok else 0
            })
            
            results['CanonicalizeStagedDataTool'] = canonicalize_result
            
            # Update resume state to mark as completed
            resume_state['resumed'] = True
            resume_state['resumed_at'] = datetime.utcnow().isoformat() + "Z"
            resume_state['corrected_file_path'] = str(corrected_file_path)
            resume_state['validation_passed'] = True
            resume_state['validation_violations'] = violations
            # Update orchestrator fields
            resume_state['halt_reason'] = None
            resume_state['current_phase'] = "COMPLETED"
            resume_state['last_corrected_file_path'] = str(corrected_file_path)
            if corrected_file_mtime:
                resume_state['last_corrected_file_mtime'] = corrected_file_mtime
            # Increment resume attempt count
            resume_state['resume_attempt_count'] = resume_state.get('resume_attempt_count', 0) + 1
            
            with open(resume_state_path, 'w', encoding='utf-8') as f:
                json.dump(resume_state, f, indent=2)
        
        # If validation fails, regenerate error report per BRD FR-012
        else:
            partner_name = resume_state.get('partner_name', 'Partner')
            quarter = resume_state.get('quarter', 'Q1')
            year = resume_state.get('year', str(datetime.now().year))
            
            # Regenerate error report (Excel format for better user experience)
            error_report_path = self.evidence_dir / "outputs" / "partner_error_report.xlsx"
            error_report_path.parent.mkdir(parents=True, exist_ok=True)
            
            self._emit("STEP_START", "Regenerating partner error report", {
                "tool": "GeneratePartnerErrorReportTool"
            })
            
            error_report_result = self.error_report_tool(
                staged_dataframe=staged_dataframe,
                violations=violations,
                aggregates=aggregates,  # Pass updated aggregates to error report
                output_path=error_report_path
            )
            
            self._emit("STEP_END", "Completed GeneratePartnerErrorReportTool", {
                "tool": "GeneratePartnerErrorReportTool",
                "ok": error_report_result.ok
            })
            
            results['GeneratePartnerErrorReportTool'] = error_report_result
            
            # Update resume state
            resume_state['resumed'] = True
            resume_state['resumed_at'] = datetime.utcnow().isoformat() + "Z"
            resume_state['corrected_file_path'] = str(corrected_file_path)
            resume_state['validation_passed'] = False
            resume_state['validation_violations'] = violations
            # Update orchestrator fields
            resume_state['halt_reason'] = f"Validation still has {error_count} errors - partner corrections incomplete"
            resume_state['current_phase'] = "AWAITING_PARTNER"
            resume_state['partner_error_report_path'] = str(error_report_path.resolve())
            resume_state['last_corrected_file_path'] = str(corrected_file_path)
            if corrected_file_mtime:
                resume_state['last_corrected_file_mtime'] = corrected_file_mtime
            # Increment resume attempt count
            resume_state['resume_attempt_count'] = resume_state.get('resume_attempt_count', 0) + 1
            
            with open(resume_state_path, 'w', encoding='utf-8') as f:
                json.dump(resume_state, f, indent=2)
            
            results['_halted'] = True
            results['_halt_reason'] = f"Validation still has {error_count} errors - partner corrections incomplete"
        
        return results

