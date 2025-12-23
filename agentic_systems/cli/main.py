"""CLI entrypoint and run coordinator per PRD-TRD Section 11.2."""

import argparse
from pathlib import Path
from typing import Any, Dict
import sys
import time

# Load .env files from repository root (before any imports that need env vars)
# Loads .env first (shared defaults), then .env.local (user-specific overrides)
try:
    from dotenv import load_dotenv
    # Get repository root (parent of agentic_systems directory)
    current_dir = Path(__file__).resolve()
    agentic_systems_root = current_dir.parents[1]  # This is 'agentic_systems'
    repo_root = agentic_systems_root.parent  # Repository root
    
    # Load .env first (shared defaults), then .env.local (user-specific overrides)
    # .env.local values will override .env values
    env_file = repo_root / ".env"
    env_local = repo_root / ".env.local"
    
    if env_file.exists():
        load_dotenv(env_file, override=False)  # Load base defaults
    if env_local.exists():
        load_dotenv(env_local, override=True)  # Override with user-specific values
except ImportError:
    # python-dotenv not installed - environment variables must be set manually
    # Calculate repo_root anyway for sys.path
    current_dir = Path(__file__).resolve()
    agentic_systems_root = current_dir.parents[1]  # This is 'agentic_systems'
    repo_root = agentic_systems_root.parent  # Repository root
    pass

# Ensure the agentic_systems package root is on sys.path so that
# absolute imports resolve correctly when running:
#   python -m agentic_systems.cli.main run intake --file ...
# Add parent directory to sys.path to allow absolute imports
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from agentic_systems.agents.simple_intake_agent import SimpleIntakeAgent
from agentic_systems.core.audit.write_evidence import write_evidence_bundle

# Part 2: LLM orchestration (optional import)
try:
    from agentic_systems.agents.platforms.langchain.intake_impl import LangChainIntakeAgent
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    LangChainIntakeAgent = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent run coordinator")
    parser.add_argument("action", choices=["run"], help="Execute an agent workflow")
    parser.add_argument("agent", choices=["intake", "reconciliation", "export"], help="Agent name")
    parser.add_argument("--file", help="Path to partner file (required for intake agent, or corrected file for resume)")
    parser.add_argument("--platform", default="minimal", help="Agent platform to use")
    parser.add_argument("--partner", default="demo", help="Partner identifier")
    parser.add_argument("--quarter", default="Q1", help="Reporting period")
    parser.add_argument("--resume", help="Resume processing with corrected file (provide run_id)")
    parser.add_argument(
        "--watch",
        help=(
            "Watch simulated SharePoint uploads/<run-id>/ for corrected files and "
            "automatically resume when a new file appears (demo for BRD FR-012 retry/resume)"
        ),
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    
    # Keep run_id pattern <partner>-<quarter>-<platform> per PRD-TRD Section 11.2
    run_id = f"{args.partner}-{args.quarter}-{args.platform}"
    evidence_dir = base_dir / "core" / "audit" / "runs" / run_id
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    if args.agent == "intake":
        # Part 3: Resume workflow per BRD FR-012
        if args.resume:
            # Resume processing with corrected file
            if not args.file:
                print("Error: --file argument is required when using --resume (provide corrected file path)")
                return
            
            corrected_file_path = Path(args.file)
            if not corrected_file_path.exists():
                print(f"Error: Corrected file not found: {corrected_file_path}")
                return
            
            # Load agent from evidence bundle manifest
            resume_run_id = args.resume
            resume_evidence_dir = base_dir / "core" / "audit" / "runs" / resume_run_id
            
            if not resume_evidence_dir.exists():
                print(f"Error: Evidence bundle not found for run_id: {resume_run_id}")
                return
            
            # Read manifest to determine agent type
            manifest_path = resume_evidence_dir / "manifest.json"
            if not manifest_path.exists():
                print(f"Error: Manifest not found in evidence bundle: {manifest_path}")
                return
            
            import json
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            platform = manifest.get('platform', 'minimal')
            agent_name = manifest.get('agent', 'SimpleIntakeAgent')
            
            # Initialize agent
            if platform == "minimal":
                agent = SimpleIntakeAgent(run_id=resume_run_id, evidence_dir=resume_evidence_dir)
            elif platform == "langchain":
                if not LANGCHAIN_AVAILABLE:
                    print("Error: LangChain dependencies not installed.")
                    return
                try:
                    agent = LangChainIntakeAgent(run_id=resume_run_id, evidence_dir=resume_evidence_dir)
                except Exception as e:
                    print(f"Error initializing LangChain agent: {e}")
                    return
            else:
                print(f"Error: Unknown platform in manifest: {platform}")
                return
            
            # Resume with corrected file
            inputs = {
                "file_path": str(corrected_file_path),
                "run_id": resume_run_id,
                "partner_name": args.partner,
                "quarter": args.quarter
            }
            
            print(f"=== RESUMING RUN: {resume_run_id} ===")
            print(f"Corrected file: {corrected_file_path}")
            
            results = agent.resume(corrected_file_path, inputs)
            
            summary = agent.summarize(results)
            print("\n=== SUMMARY ===")
            print(summary)
            
            # Update evidence bundle
            write_evidence_bundle(
                run_id=resume_run_id,
                agent_name=agent_name,
                platform=platform,
                plan_steps=[],  # Resume doesn't generate new plan
                summary=summary,
                run_results=results,
                evidence_dir=resume_evidence_dir,
                model=manifest.get('model')
            )
            
            print(f"\nEvidence bundle updated at: {resume_evidence_dir}")
            return

        # Part 3 (demo): Polling-based resume per BRD FR-012 validation retry & resume.
        # In production, this would be triggered by a SharePoint webhook; here we
        # simulate that by watching the local sharepoint_simulation/uploads/<run-id>/
        # folder for new corrected files.
        if args.watch:
            watch_run_id = args.watch
            resume_evidence_dir = base_dir / "core" / "audit" / "runs" / watch_run_id

            if not resume_evidence_dir.exists():
                print(f"Error: Evidence bundle not found for run_id: {watch_run_id}")
                return

            # Load manifest to determine platform and agent for the watched run.
            manifest_path = resume_evidence_dir / "manifest.json"
            if not manifest_path.exists():
                print(f"Error: Manifest not found in evidence bundle: {manifest_path}")
                return

            import json

            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            platform = manifest.get("platform", "minimal")
            agent_name = manifest.get("agent", "SimpleIntakeAgent")

            # Initialize agent for the watched run_id.
            if platform == "minimal":
                agent = SimpleIntakeAgent(run_id=watch_run_id, evidence_dir=resume_evidence_dir)
            elif platform == "langchain":
                if not LANGCHAIN_AVAILABLE:
                    print("Error: LangChain dependencies not installed.")
                    return
                try:
                    agent = LangChainIntakeAgent(run_id=watch_run_id, evidence_dir=resume_evidence_dir)
                except Exception as e:
                    print(f"Error initializing LangChain agent: {e}")
                    return
            else:
                print(f"Error: Unknown platform in manifest: {platform}")
                return

            # Determine simulated SharePoint uploads folder for corrected files.
            uploads_dir = (
                resume_evidence_dir
                / "sharepoint_simulation"
                / "uploads"
                / watch_run_id
            )

            uploads_dir.mkdir(parents=True, exist_ok=True)

            print(f"=== WATCH MODE (DEMO) ===")
            print(
                "BRD FR-012: Simulating SharePoint webhook-based validation retry by "
                f"polling for corrected files in:\n  {uploads_dir}\n"
            )
            print("Waiting for a new corrected file to appear... (Ctrl+C to cancel)")

            # Track previously seen files so we only react to new uploads.
            seen_files = {p for p in uploads_dir.glob("*") if p.is_file()}

            corrected_file_path: Path | None = None

            try:
                while True:
                    current_files = [p for p in uploads_dir.glob("*") if p.is_file()]
                    new_files = [p for p in current_files if p not in seen_files]

                    if new_files:
                        # Pick the newest file as the corrected file.
                        corrected_file_path = max(
                            new_files, key=lambda p: p.stat().st_mtime
                        )
                        print(f"\nDetected new corrected file: {corrected_file_path}")
                        break

                    seen_files = set(current_files)
                    time.sleep(5)
            except KeyboardInterrupt:
                print("\nWatch mode cancelled by user.")
                return

            if not corrected_file_path:
                print("No corrected file detected; exiting watch mode.")
                return

            # Resume with detected corrected file, using same path as manual --resume.
            inputs = {
                "file_path": str(corrected_file_path),
                "run_id": watch_run_id,
                "partner_name": args.partner,
                "quarter": args.quarter,
            }

            print(f"\n=== RESUMING RUN VIA WATCH: {watch_run_id} ===")
            print(f"Corrected file: {corrected_file_path}")

            results = agent.resume(corrected_file_path, inputs)

            summary = agent.summarize(results)
            print("\n=== SUMMARY ===")
            print(summary)

            # Update evidence bundle for the watched run.
            write_evidence_bundle(
                run_id=watch_run_id,
                agent_name=agent_name,
                platform=platform,
                plan_steps=[],  # Resume doesn't generate new plan
                summary=summary,
                run_results=results,
                evidence_dir=resume_evidence_dir,
                model=manifest.get("model"),
            )

            print(f"\nEvidence bundle updated at: {resume_evidence_dir}")
            return
        
        # Normal intake workflow
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
            agent_name = "SimpleIntakeAgent"
        elif args.platform == "langchain":
            # Part 2: LLM orchestration per PRD-TRD Section 6.4
            if not LANGCHAIN_AVAILABLE:
                print("Error: LangChain dependencies not installed.")
                print("Install with: pip install langchain langchain-openai openai")
                return
            try:
                agent = LangChainIntakeAgent(run_id=run_id, evidence_dir=evidence_dir)
                agent_name = "LangChainIntakeAgent"
            except Exception as e:
                print(f"Error initializing LangChain agent: {e}")
                print("Make sure OPENAI_API_KEY or ANTHROPIC_API_KEY is set in environment")
                return
        else:
            raise ValueError(f"Unknown platform: {args.platform}")
        
        # Demonstrate BaseAgent contract per PRD-TRD Section 5.1
        # Part 3: Include partner_name and quarter for HITL workflow per BRD FR-012
        inputs: Dict[str, Any] = {
            "file_path": str(file_path),
            "run_id": run_id,
            "partner_name": args.partner,
            "quarter": args.quarter
        }
        
        plan_steps = agent.plan(inputs)
        # Generate human-readable plan from structured steps for display
        plan_text = "\n".join([f"{i+1}. {step['tool']}" for i, step in enumerate(plan_steps)])
        print("=== PLAN ===")
        print(plan_text)  # Per BRD FR-011, plan shown before execution
        
        results = agent.execute(inputs)
        
        # Generate summary per BRD FR-011 (required for evidence bundle)
        summary = agent.summarize(results)
        
        # Write evidence bundle per BRD FR-011
        # Evidence bundle must be created even when halted to ensure completeness
        # This ensures validation_report.csv and other artifacts are available for review
        # Get model name for langchain platform
        model_name = None
        if args.platform == "langchain" and hasattr(agent, 'llm'):
            # Extract model name from LLM instance
            if hasattr(agent.llm, 'model_name'):
                model_name = agent.llm.model_name
            elif hasattr(agent.llm, 'model'):
                model_name = agent.llm.model
            # Fallback to environment variable if LLM object doesn't expose model name
            if not model_name:
                import os
                model_name = os.getenv('OPENAI_MODEL') or os.getenv('ANTHROPIC_MODEL')
        
        write_evidence_bundle(
            run_id=run_id,
            agent_name=agent_name,
            platform=args.platform,
            plan_steps=plan_steps,
            summary=summary,
            run_results=results,
            evidence_dir=evidence_dir,
            model=model_name
        )
        
        # Part 3: Check if execution was halted due to HITL workflow per BRD FR-012
        if results.get('_halted'):
            print(f"\n=== EXECUTION HALTED ===")
            print(f"Reason: {results.get('_halt_reason', 'Unknown')}")
            print(f"\nTo resume with corrected file:")
            print(f"  python -m agentic_systems.cli.main run intake --resume {run_id} --file <corrected_file_path>")
            print(f"\nEvidence bundle written to: {evidence_dir}")
            return
        
        print("\n=== SUMMARY ===")
        print(summary)  # Per BRD FR-011, summary shown after execution
        
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
