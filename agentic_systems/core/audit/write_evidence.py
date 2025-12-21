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
    model: str = None
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
        "egress_approval_ref": None  # No Restricted data sent to LLM per BRD Section 2.3
    }
    
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
    write_manifest(run_id, agent_name, platform, evidence_dir, model)
    write_plan(plan_steps, evidence_dir)
    write_summary(summary, evidence_dir)
    
    # Serialize in-memory tool results to outputs/ directory once (after all tools complete)
    serialize_outputs(run_results, evidence_dir)

