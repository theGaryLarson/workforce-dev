"""Evidence bundle writer per BRD FR-011 and PRD-TRD Section 3.2.

Writes manifest.json, plan.md, summary.md, and serializes outputs/ directory.
Does NOT write tool_calls.jsonl - that is handled by BaseAgent.execute() which
appends JSONL events directly as tools run.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

# Masked mock data is treated as Internal; PII is redacted per BRD Section 2.3
# (comment in code, not JSON)


def write_manifest(
    run_id: str,
    agent_name: str,
    platform: str,
    evidence_dir: Path,
    model: str = None,
    run_results: Dict[str, Any] = None
) -> None:
    """Write manifest.json per PRD-TRD Section 3.2.
    
    Args:
        run_id: Run identifier
        agent_name: Name of the agent that executed
        platform: Platform used (minimal, langchain, etc.)
        evidence_dir: Directory where evidence bundle is written
        model: LLM model name (for Part 2, None for Part 1)
    """
    manifest = {
        "run_id": run_id,
        "agent": agent_name,
        "platform": platform,
        # Data classification per BRD Section 2.3 - JSON values only (no comments in JSON)
        "data_classification": "Internal",  # Masked mock data is treated as Internal per BRD Section 2.3
        "pii_handling": "redacted",  # PII is redacted per BRD Section 2.3
        # For Part 2: include platform/model metadata per PRD-TRD Section 3.2
        "model": model,
        "egress_approval_ref": None,  # No Restricted data sent to LLM per BRD Section 2.3
        # Part 3: HITL status fields per BRD FR-012
        "hitl_status": None,  # Will be set if HITL workflow is triggered
        "staff_approval_status": None,  # Will be set if staff approval is requested
        "resume_available": False,  # Will be set if resume state is saved
        # Orchestrator fields per orchestrator plan
        "orchestrator_status": None,  # Will be set by orchestrator if used
        "last_orchestrator_action": None  # Will be set by orchestrator to track actions
    }
    
    # Part 3: Check if HITL workflow was triggered per BRD FR-012
    if run_results and run_results.get('_halted'):
        manifest["hitl_status"] = "halted"
        manifest["resume_available"] = True
        
        # Check for staff approval status
        approval_result = run_results.get('RequestStaffApprovalTool')
        if approval_result:
            manifest["staff_approval_status"] = approval_result.data.get('approval_status')
            
            # Include secure link code if approved
            secure_link_result = run_results.get('CreateSecureLinkTool')
            if secure_link_result and secure_link_result.ok:
                manifest["secure_link_code"] = secure_link_result.data.get('access_code')
    
    # Write manifest.json per PRD-TRD Section 3.2
    manifest_path = evidence_dir / "manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)


def write_plan(plan_steps: List[Dict[str, Any]], evidence_dir: Path) -> None:
    """Write human-readable plan.md from structured steps per BRD FR-011.
    
    Args:
        plan_steps: Structured steps returned by agent.plan()
        evidence_dir: Directory where evidence bundle is written
    """
    plan_lines = ["# Execution Plan\n"]
    
    for i, step in enumerate(plan_steps, 1):
        tool_name = step.get('tool', 'Unknown')
        args = step.get('args', {})
        plan_lines.append(f"{i}. {tool_name}")
        if args:
            plan_lines.append(f"   Arguments: {json.dumps(args, indent=2)}")
        plan_lines.append("")
    
    plan_path = evidence_dir / "plan.md"
    with open(plan_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(plan_lines))


def write_summary(summary: str, evidence_dir: Path) -> None:
    """Write summary.md per BRD FR-011.
    
    Args:
        summary: Staff-facing summary from agent.summarize()
        evidence_dir: Directory where evidence bundle is written
    """
    summary_path = evidence_dir / "summary.md"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(f"# Execution Summary\n\n{summary}\n")


def serialize_outputs(run_results: Dict[str, Any], evidence_dir: Path) -> None:
    """Serialize in-memory tool results to outputs/ directory per BRD FR-011.
    
    Tools return in-memory data only; evidence writer handles file serialization.
    Serializes validation results to outputs/validation_report.csv and canonical
    data to outputs/canonical.csv.
    
    Args:
        run_results: Dictionary of tool execution results from agent.execute()
        evidence_dir: Directory where evidence bundle is written
    """
    outputs_dir = evidence_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    
    # Serialize validation results to outputs/validation_report.csv
    # Write validation report whenever violations exist, even if validation failed
    # This allows users to review errors and warnings even when validation fails
    validate_result = run_results.get('ValidateStagedDataTool')
    if validate_result and validate_result.data.get('violations'):
        violations = validate_result.data.get('violations', [])
        if violations:
            violations_df = pd.DataFrame(violations)
            violations_path = outputs_dir / "validation_report.csv"
            violations_df.to_csv(violations_path, index=False)
    
    # Serialize canonical data to outputs/canonical.csv
    canonicalize_result = run_results.get('CanonicalizeStagedDataTool')
    if canonicalize_result and canonicalize_result.ok:
        canonical_df = canonicalize_result.data.get('canonical_dataframe')
        if canonical_df is not None:
            canonical_path = outputs_dir / "canonical.csv"
            canonical_df.to_csv(canonical_path, index=False)
    
    # Part 3: Serialize partner communication outputs per BRD FR-011 / FR-012 / FR-013
    # Note: partner_error_report.xlsx is already written by GeneratePartnerErrorReportTool
    # (uses create_error_excel_with_comments for user-friendly Excel format)
    # secure_link_code.txt is already written by CreateSecureLinkTool
    
    # Serialize email content.
    # We may have both an initial staff-preview email and a final partner-facing
    # email with the secure link and access code.
    # BRD FR-012: Staff review/approval of email content before partner sharing.
    # BRD FR-013: Secure link is only included in partner-facing email after approval.
    email_result_initial = run_results.get('GeneratePartnerEmailTool_initial')
    email_result_final = run_results.get('GeneratePartnerEmailTool')

    # Base email (for reference) – prefer final if available, otherwise initial.
    base_email_result = email_result_final or email_result_initial
    if base_email_result and base_email_result.ok:
        email_content = base_email_result.data.get('email_content')
        if email_content:
            email_path = outputs_dir / "partner_email.txt"
            with open(email_path, 'w', encoding='utf-8') as f:
                f.write(email_content)
        
        email_html = base_email_result.data.get('email_html')
        if email_html:
            email_html_path = outputs_dir / "partner_email.html"
            with open(email_html_path, 'w', encoding='utf-8') as f:
                f.write(email_html)
    
    # Serialize approved email (after staff approval) – must include secure link
    # generated only after approval per BRD FR-012 / FR-013.
    approval_result = run_results.get('RequestStaffApprovalTool')
    if approval_result and approval_result.data.get('approval_status') == 'approved':
        # Use the final post-approval email if available; fall back to base email.
        approved_email_result = email_result_final or base_email_result
        if approved_email_result and approved_email_result.ok:
            email_content = approved_email_result.data.get('email_content')
            if email_content:
                approved_email_path = outputs_dir / "partner_email_approved.txt"
                with open(approved_email_path, 'w', encoding='utf-8') as f:
                    f.write(email_content)
        
        # Serialize staff approval record per BRD FR-012 (HITL audit evidence)
        approval_record = {
            "approval_status": approval_result.data.get('approval_status'),
            "staff_comments": approval_result.data.get('staff_comments'),
            "approval_timestamp": approval_result.data.get('approval_timestamp')
        }
        approval_record_path = outputs_dir / "staff_approval_record.json"
        with open(approval_record_path, 'w', encoding='utf-8') as f:
            json.dump(approval_record, f, indent=2)


def write_evidence_bundle(
    run_id: str,
    agent_name: str,
    platform: str,
    plan_steps: List[Dict[str, Any]],
    summary: str,
    run_results: Dict[str, Any],
    evidence_dir: Path,
    model: str = None
) -> None:
    """Write complete evidence bundle per BRD FR-011 and PRD-TRD Section 3.2.
    
    Writes manifest.json, plan.md, summary.md, and serializes outputs/ directory.
    Does NOT write tool_calls.jsonl - that is handled by BaseAgent.execute().
    
    Args:
        run_id: Run identifier
        agent_name: Name of the agent that executed
        platform: Platform used (minimal, langchain, etc.)
        plan_steps: Structured steps returned by agent.plan()
        summary: Staff-facing summary from agent.summarize()
        run_results: Dictionary of tool execution results from agent.execute()
        evidence_dir: Directory where evidence bundle is written
        model: LLM model name (for Part 2, None for Part 1)
    """
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    # Write manifest.json, plan.md, summary.md from agent state per PRD-TRD Section 3.2
    write_manifest(run_id, agent_name, platform, evidence_dir, model, run_results)
    write_plan(plan_steps, evidence_dir)
    write_summary(summary, evidence_dir)
    
    # Serialize in-memory tool results to outputs/ directory once (after all tools complete)
    serialize_outputs(run_results, evidence_dir)

