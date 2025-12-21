"""CLI entrypoint and run coordinator per PRD-TRD Section 11.2."""

import argparse
from pathlib import Path
from typing import Any, Dict
import sys

# Ensure the agentic_systems package root is on sys.path so that
# absolute imports resolve correctly when running:
#   python -m agentic_systems.cli.main run intake --file ...
# Add parent directory to sys.path to allow absolute imports
current_dir = Path(__file__).resolve()
agentic_systems_root = current_dir.parents[1]  # This is 'agentic_systems'
if str(agentic_systems_root.parent) not in sys.path:
    sys.path.insert(0, str(agentic_systems_root.parent))

from agentic_systems.agents.simple_intake_agent import SimpleIntakeAgent
from agentic_systems.core.audit.write_evidence import write_evidence_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent run coordinator")
    parser.add_argument("action", choices=["run"], help="Execute an agent workflow")
    parser.add_argument("agent", choices=["intake", "reconciliation", "export"], help="Agent name")
    parser.add_argument("--file", help="Path to partner file (required for intake agent)")
    parser.add_argument("--platform", default="minimal", help="Agent platform to use")
    parser.add_argument("--partner", default="demo", help="Partner identifier")
    parser.add_argument("--quarter", default="Q1", help="Reporting period")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    
    # Keep run_id pattern <partner>-<quarter>-<platform> per PRD-TRD Section 11.2
    run_id = f"{args.partner}-{args.quarter}-{args.platform}"
    evidence_dir = base_dir / "core" / "audit" / "runs" / run_id
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    if args.agent == "intake":
        # Validate file path exists before processing
        if not args.file:
            print("Error: --file argument is required for intake agent")
            return
        
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            return
        
        # CLI directly instantiates platform-specific agents per PRD-TRD Section 6.4
        # No dispatcher needed - CLI routes directly to platform implementations
        if args.platform == "minimal":
            agent = SimpleIntakeAgent(run_id=run_id, evidence_dir=evidence_dir)
        elif args.platform == "langchain":
            # Part 2: LLM orchestration (not implemented yet)
            print(f"Error: Platform 'langchain' not yet implemented")
            return
        else:
            raise ValueError(f"Unknown platform: {args.platform}")
        
        # Demonstrate BaseAgent contract per PRD-TRD Section 5.1
        inputs: Dict[str, Any] = {
            "file_path": str(file_path),
            "run_id": run_id
        }
        
        plan_steps = agent.plan(inputs)
        # Generate human-readable plan from structured steps for display
        plan_text = "\n".join([f"{i+1}. {step['tool']}" for i, step in enumerate(plan_steps)])
        print("=== PLAN ===")
        print(plan_text)  # Per BRD FR-011, plan shown before execution
        
        results = agent.execute(inputs)
        
        summary = agent.summarize(results)
        print("\n=== SUMMARY ===")
        print(summary)  # Per BRD FR-011, summary shown after execution
        
        # Write evidence bundle per BRD FR-011
        write_evidence_bundle(
            run_id=run_id,
            agent_name="SimpleIntakeAgent",
            platform=args.platform,
            plan_steps=plan_steps,
            summary=summary,
            run_results=results,
            evidence_dir=evidence_dir
        )
        
        # Show canonical data summary (row count, column names, sample record count - no raw PII data)
        canonicalize_result = results.get('CanonicalizeStagedDataTool')
        if canonicalize_result and canonicalize_result.ok:
            canonical_df = canonicalize_result.data.get('canonical_dataframe')
            if canonical_df is not None:
                print(f"\n=== CANONICAL DATA SUMMARY ===")
                print(f"Record count: {len(canonical_df)}")
                print(f"Columns: {', '.join(canonical_df.columns[:10])}{'...' if len(canonical_df.columns) > 10 else ''}")
                print(f"Sample record count: {min(5, len(canonical_df))}")
        
        print(f"\nEvidence bundle written to: {evidence_dir}")
    else:
        print(f"Agent '{args.agent}' not yet implemented")


if __name__ == "__main__":
    main()
