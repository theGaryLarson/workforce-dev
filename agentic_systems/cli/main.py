"""CLI entrypoint and run coordinator per PRD-TRD Section 11.2."""

import argparse
from pathlib import Path
from typing import Any, Dict
import sys
import time
import json

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
from agentic_systems.agents.orchestrator_agent import OrchestratorAgent
from agentic_systems.core.audit.write_evidence import write_evidence_bundle
from agentic_systems.core.tools import ToolResult

# Part 2: LLM orchestration (optional import)
try:
    from agentic_systems.agents.platforms.langchain.intake_impl import LangChainIntakeAgent
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    LangChainIntakeAgent = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent run coordinator")
    parser.add_argument("action", choices=["run", "orchestrate"], help="Execute an agent workflow or orchestrate intake runs")
    parser.add_argument("agent", choices=["intake", "reconciliation", "export"], help="Agent name (required for 'run' action)")
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
    # Orchestrate-specific arguments
    parser.add_argument("--sharepoint-sim-root", help="Root directory for SharePoint simulation folders (orchestrate only)")
    parser.add_argument("--poll-interval", type=int, default=5, help="Polling interval in seconds (orchestrate only, default: 5)")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    
    # Orchestrate action per orchestrator plan
    if args.action == "orchestrate":
        if args.agent != "intake":
            print("Error: Orchestrate action currently only supports 'intake' agent")
            return
        
        # Keep run_id pattern <partner>-<quarter>-<platform> per PRD-TRD Section 11.2
        # NOTE: Don't create evidence_dir here - wait until partner is detected from file
        # This prevents creating demo-Q1-minimal folder when actual partner is different
        run_id = f"{args.partner}-{args.quarter}-{args.platform}"
        # Don't create evidence_dir yet - wait for file detection
        # This prevents creating demo-Q1-minimal folder when actual partner is different
        evidence_dir = None  # Will be set when partner is detected from file
        
        # SharePoint simulation root should be at repo root (agentic_systems/sharepoint_simulation/)
        # Simplified structure: sharepoint_simulation/uploads/{partner_name}/
        if args.sharepoint_sim_root:
            sharepoint_sim_root = Path(args.sharepoint_sim_root).resolve()
        else:
            # Default to repo root: agentic_systems/sharepoint_simulation/
            sharepoint_sim_root = base_dir / "sharepoint_simulation"
        
        # Watch directory is now sharepoint_simulation/uploads/ (simplified structure)
        watch_dir = sharepoint_sim_root / "uploads"
        watch_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize orchestrator agent (partner_uploads_dir is now None - we use sharepoint_sim_root/uploads/)
        # evidence_dir is None initially - will be set when partner is detected
        orchestrator = OrchestratorAgent(
            run_id=run_id,
            evidence_dir=None,  # Will be set when partner is detected from file
            sharepoint_sim_root=sharepoint_sim_root,
            partner_uploads_dir=None  # No longer used - files come from sharepoint_simulation/uploads/
        )
        
        print(f"=== ORCHESTRATOR MODE (DEMO) ===")
        print(f"BRD FR-012/FR-013: Simulating SharePoint webhook-based orchestration")
        print(f"Partner: {args.partner}, Quarter: {args.quarter}, Platform: {args.platform}")
        print(f"Watch directory: {watch_dir} (recursive)")
        print(f"SharePoint simulation root: {sharepoint_sim_root}")
        
        # Use watchdog for file system events instead of polling
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler, FileSystemEvent
            WATCHDOG_AVAILABLE = True
        except ImportError:
            WATCHDOG_AVAILABLE = False
            print(f"Warning: watchdog not installed, falling back to polling (interval: {args.poll_interval}s)")
            print("Install with: pip install watchdog")
        
        if WATCHDOG_AVAILABLE:
            print("Using file system events (watchdog) for file detection")
            print("\nWaiting for initial upload or corrected files... (Ctrl+C to cancel)")
            
            # Event handler for file system events
            class OrchestratorEventHandler(FileSystemEventHandler):
                """Handle file system events for orchestrator file detection."""
                
                def __init__(self, orchestrator: OrchestratorAgent, inputs: Dict[str, Any], 
                           evidence_dir: Path, sharepoint_sim_root: Path, run_id: str):
                    self.orchestrator = orchestrator
                    self.inputs = inputs
                    self.evidence_dir = evidence_dir
                    self.sharepoint_sim_root = sharepoint_sim_root
                    self.run_id = run_id
                    self.processed_files = set()  # Track processed files to avoid duplicates
                    self.lock = False  # Simple lock to prevent concurrent processing
                
                def on_created(self, event: FileSystemEvent):
                    """Handle file creation events using content signature matching."""
                    if event.is_directory:
                        return
                    
                    file_path = Path(event.src_path)
                    # Use resolved path for comparison to handle symlinks and path normalization
                    file_path_resolved = file_path.resolve()
                    if file_path_resolved in self.processed_files or file_path in self.processed_files:
                        return
                    
                    # Debounce: wait a moment for file to finish writing
                    import time
                    time.sleep(0.5)
                    
                    if not file_path.exists() or not file_path.is_file():
                        return
                    
                    # Use content signature matching instead of filename patterns
                    file_sig = self.orchestrator._get_file_column_signature(file_path)
                    if not file_sig:
                        return
                    
                    columns, mtime = file_sig
                    
                    # All files are in sharepoint_simulation/uploads/{partner_name}/
                    # Extract partner name from file path
                    detected_partner = None
                    uploads_dir = self.sharepoint_sim_root / "uploads" if self.sharepoint_sim_root else None
                    if uploads_dir:
                        try:
                            # File path should be: sharepoint_simulation/uploads/{partner_name}/filename
                            relative_path = file_path.relative_to(uploads_dir)
                            if len(relative_path.parts) > 1:
                                detected_partner = relative_path.parts[0]
                        except (ValueError, AttributeError):
                            pass
                    
                    # Determine if this is an initial file or corrected file
                    # Initial files: new files in uploads/{partner_name}/ that haven't been processed
                    # Corrected files: files in uploads/{partner_name}/ that match a run's expected signature
                    is_initial = False
                    is_corrected = False
                    
                    if detected_partner and uploads_dir:
                        partner_uploads_dir = uploads_dir / detected_partner
                        try:
                            uploads_dir_resolved = uploads_dir.resolve()
                            file_path_resolved = file_path.resolve()
                            # Check if file is within uploads/{partner_name}/
                            if uploads_dir_resolved.exists() and str(file_path_resolved).startswith(str(uploads_dir_resolved)):
                                # Check if this matches a run's expected signature (corrected file)
                                # or is a new file (initial file)
                                # For now, treat as initial if no resume_state.json exists for this partner
                                # This is a simplification - in production, we'd use more sophisticated matching
                                is_initial = True  # Will be refined by checking against existing runs
                                is_corrected = False  # Will be refined by checking resume_state.json
                        except (AttributeError, ValueError, OSError):
                            pass
                    
                    # Validate content signature for partner data
                    if is_initial or is_corrected:
                        # Basic validation: ensure file has partner data columns
                        required_columns = ['first name', 'last name', 'date of birth']
                        columns_lower = ' '.join(columns).lower()
                        has_required = any(req_col in columns_lower for req_col in required_columns)
                        
                        if has_required:
                            # Add both resolved and original path to processed_files to handle path variations
                            self.processed_files.add(file_path)
                            self.processed_files.add(file_path_resolved)
                            self._process_file(file_path, is_initial, is_corrected, detected_partner)
                
                def on_modified(self, event: FileSystemEvent):
                    """Handle file modification events using content signature matching."""
                    # Only process if file wasn't already processed
                    if event.is_directory:
                        return
                    
                    file_path = Path(event.src_path)
                    # Use resolved path for comparison to handle symlinks and path normalization
                    file_path_resolved = file_path.resolve()
                    if file_path_resolved in self.processed_files or file_path in self.processed_files:
                        return
                    
                    # Small delay to ensure file write is complete
                    import time
                    time.sleep(0.5)
                    
                    if not file_path.exists() or not file_path.is_file():
                        return
                    
                    # Use content signature matching
                    file_sig = self.orchestrator._get_file_column_signature(file_path)
                    if not file_sig:
                        return
                    
                    columns, mtime = file_sig
                    
                    # All files are in sharepoint_simulation/uploads/{partner_name}/
                    # Extract partner name from file path
                    detected_partner = None
                    uploads_dir = self.sharepoint_sim_root / "uploads" if self.sharepoint_sim_root else None
                    if uploads_dir:
                        try:
                            # File path should be: sharepoint_simulation/uploads/{partner_name}/filename
                            relative_path = file_path.relative_to(uploads_dir)
                            if len(relative_path.parts) > 1:
                                detected_partner = relative_path.parts[0]
                        except (ValueError, AttributeError):
                            pass
                    
                    # Determine if this is an initial file or corrected file
                    is_initial = False
                    is_corrected = False
                    
                    if detected_partner and uploads_dir:
                        partner_uploads_dir = uploads_dir / detected_partner
                        try:
                            uploads_dir_resolved = uploads_dir.resolve()
                            file_path_resolved = file_path.resolve()
                            # Check if file is within uploads/{partner_name}/
                            if uploads_dir_resolved.exists() and str(file_path_resolved).startswith(str(uploads_dir_resolved)):
                                is_initial = True  # Will be refined by checking against existing runs
                                is_corrected = False  # Will be refined by checking resume_state.json
                        except (AttributeError, ValueError, OSError):
                            pass
                    
                    # Validate content signature for partner data
                    if (is_initial or is_corrected) and file_path_resolved not in self.processed_files and file_path not in self.processed_files:
                        required_columns = ['first name', 'last name', 'date of birth']
                        columns_lower = ' '.join(columns).lower()
                        has_required = any(req_col in columns_lower for req_col in required_columns)
                        
                        if has_required:
                            # Add both resolved and original path to processed_files to handle path variations
                            self.processed_files.add(file_path)
                            self.processed_files.add(file_path_resolved)
                            self._process_file(file_path, is_initial, is_corrected, detected_partner)
                
                def _process_file(self, file_path: Path, is_initial: bool, is_corrected: bool, detected_partner: str = None):
                    """Process a detected file."""
                    if self.lock:
                        return  # Already processing
                    
                    self.lock = True
                    try:
                        print(f"\n[Orchestrator] Detected file: {file_path.name}")
                        if detected_partner:
                            print(f"[Orchestrator] Detected partner: {detected_partner}")
                        
                        # Update inputs with detected partner if found
                        process_inputs = self.inputs.copy()
                        process_evidence_dir = self.evidence_dir
                        if detected_partner:
                            process_inputs['partner'] = detected_partner
                            # Update run_id to include detected partner
                            quarter = process_inputs.get('quarter', 'Q1')
                            platform = process_inputs.get('platform', 'minimal')
                            new_run_id = f"{detected_partner}-{quarter}-{platform}"
                            process_inputs['run_id'] = new_run_id
                            # Update evidence directory for new run_id
                            base_dir = Path(__file__).resolve().parents[1]
                            process_evidence_dir = base_dir / "core" / "audit" / "runs" / new_run_id
                            process_evidence_dir.mkdir(parents=True, exist_ok=True)
                        # Ensure orchestrator evidence_dir and run_id are set before execute()
                        # This ensures orchestrator steps are logged to the correct tool_calls.jsonl
                        self.orchestrator.evidence_dir = process_evidence_dir
                        self.orchestrator.run_id = process_inputs.get('run_id', self.run_id)
                        
                        # Plan and execute
                        plan_steps = self.orchestrator.plan(process_inputs)
                        
                        if plan_steps:
                            # Execute steps
                            results = self.orchestrator.execute(process_inputs)
                            
                            # Flatten SimpleIntakeAgent results into orchestrator's run_results
                            # so that serialize_outputs() can find CanonicalizeStagedDataTool, GeneratePartnerEmailTool, etc.
                            if 'SimpleIntakeAgent' in results:
                                intake_result = results['SimpleIntakeAgent']
                                if isinstance(intake_result, ToolResult) and intake_result.data:
                                    # Merge intake agent's results into orchestrator's results
                                    intake_results = intake_result.data
                                    if isinstance(intake_results, dict):
                                        # Add intake agent's tool results to orchestrator's results
                                        for key, value in intake_results.items():
                                            if key not in results:  # Don't overwrite orchestrator-level results
                                                results[key] = value
                            
                            summary = self.orchestrator.summarize(results)
                            
                            # Write orchestrator evidence bundle per BRD FR-011
                            # This includes orchestrator coordination steps and SimpleIntakeAgent execution
                            from agentic_systems.core.audit.write_evidence import write_evidence_bundle
                            try:
                                write_evidence_bundle(
                                    run_id=process_inputs.get('run_id', self.run_id),
                                    agent_name="OrchestratorAgent",
                                    platform=process_inputs.get('platform', 'minimal'),
                                    plan_steps=plan_steps,
                                    summary=summary,
                                    run_results=results,  # Now includes flattened SimpleIntakeAgent results
                                    evidence_dir=process_evidence_dir,
                                    model=None
                                )
                            except Exception as e:
                                # Evidence writing should never crash orchestration
                                print(f"Warning: Failed to write orchestrator evidence bundle: {e}")
                            
                            # Check if we should continue or exit
                            if any(step.get('step') in ['handle_persistent_failure', 'finalize_run'] for step in plan_steps):
                                print("\n=== ORCHESTRATOR SUMMARY ===")
                                print(summary)
                                print(f"\nEvidence bundle at: {process_evidence_dir}")
                                # Note: In production, this would stop the observer
                            else:
                                # Re-plan AFTER evidence bundle is written to pick up updated manifest.json state
                                # Temporarily disable corrected file detection to force wait step after approval
                                # We want to wait for a NEW corrected file, not resume with an old one
                                original_sharepoint_sim_root = self.orchestrator.sharepoint_sim_root
                                self.orchestrator.sharepoint_sim_root = None  # Temporarily disable corrected file detection
                                updated_plan_steps = self.orchestrator.plan(process_inputs)
                                self.orchestrator.sharepoint_sim_root = original_sharepoint_sim_root  # Restore
                                # Print wait status using updated plan
                                waiting_steps = [s for s in updated_plan_steps if 'wait' in s.get('step', '').lower()]
                                if waiting_steps:
                                    wait_step = waiting_steps[0]
                                    wait_tool = wait_step.get('tool', '')
                                    wait_args = wait_step.get('args', {})
                                    
                                    wait_result = self.orchestrator._invoke_tool(wait_tool, None, wait_args, {})
                                    if wait_result and hasattr(wait_result, 'summary'):
                                        print(f"[Orchestrator] {wait_result.summary}")
                                else:
                                    # Not waiting: show summary so users can see whether the
                                    # corrected upload re-validation passed and canonicalization ran.
                                    print("\n=== ORCHESTRATOR SUMMARY ===")
                                    print(summary)
                                    print(f"\nEvidence bundle at: {process_evidence_dir}")
                    finally:
                        self.lock = False
            
            # Set up file system observer
            event_handler = OrchestratorEventHandler(orchestrator, {
                "partner": args.partner,
                "quarter": args.quarter,
                "platform": args.platform,
                "run_id": run_id
            }, evidence_dir, sharepoint_sim_root, run_id)
            
            observer = Observer()
            
            # Watch only sharepoint_simulation/uploads/ recursively (simplified structure)
            observer.schedule(event_handler, str(watch_dir), recursive=True)
            
            # Check for existing files on startup
            # Note: _detect_initial_file now looks in sharepoint_simulation/uploads/{partner}/
            initial_file = orchestrator._detect_initial_file(args.partner, args.quarter)
            if initial_file:
                print(f"[Orchestrator] Found existing initial file: {initial_file.name}")
                # Extract partner from file path
                detected_partner = args.partner
                try:
                    relative_path = initial_file.relative_to(watch_dir)
                    if len(relative_path.parts) > 1:
                        detected_partner = relative_path.parts[0]
                except (ValueError, AttributeError):
                    pass
                event_handler._process_file(initial_file, True, False, detected_partner)
            
            corrected_file = orchestrator._detect_corrected_file(run_id, args.partner)
            if corrected_file:
                print(f"[Orchestrator] Found existing corrected file: {corrected_file.name}")
                event_handler._process_file(corrected_file, False, True, args.partner)
            
            observer.start()
            
            try:
                # Keep the main thread alive
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nOrchestrator cancelled by user.")
                observer.stop()
            observer.join()
        else:
            # Fallback to polling mode
            print(f"Polling interval: {args.poll_interval} seconds")
            print("\nWaiting for initial upload or corrected files... (Ctrl+C to cancel)")
            
            try:
                loop_i = 0
                while True:
                    loop_i += 1
                    # Plan next steps
                    inputs = {
                        "partner": args.partner,
                        "quarter": args.quarter,
                        "platform": args.platform,
                        "run_id": run_id
                    }
                    
                    # Ensure orchestrator evidence_dir and run_id are set before execute()
                    orchestrator.evidence_dir = evidence_dir
                    orchestrator.run_id = run_id
                    
                    plan_steps = orchestrator.plan(inputs)
                    
                    if plan_steps:
                        # Execute steps
                        results = orchestrator.execute(inputs)
                        
                        # Flatten SimpleIntakeAgent results into orchestrator's run_results
                        # so that serialize_outputs() can find CanonicalizeStagedDataTool, GeneratePartnerEmailTool, etc.
                        if 'SimpleIntakeAgent' in results:
                            intake_result = results['SimpleIntakeAgent']
                            if isinstance(intake_result, ToolResult) and intake_result.data:
                                # Merge intake agent's results into orchestrator's results
                                intake_results = intake_result.data
                                if isinstance(intake_results, dict):
                                    # Add intake agent's tool results to orchestrator's results
                                    for key, value in intake_results.items():
                                        if key not in results:  # Don't overwrite orchestrator-level results
                                            results[key] = value
                        
                        summary = orchestrator.summarize(results)
                        
                        # Write orchestrator evidence bundle per BRD FR-011
                        # This includes orchestrator coordination steps and SimpleIntakeAgent execution
                        from agentic_systems.core.audit.write_evidence import write_evidence_bundle
                        try:
                            write_evidence_bundle(
                                run_id=run_id,
                                agent_name="OrchestratorAgent",
                                platform=inputs.get('platform', 'minimal'),
                                plan_steps=plan_steps,
                                summary=summary,
                                run_results=results,  # Now includes flattened SimpleIntakeAgent results
                                evidence_dir=evidence_dir,
                                model=None
                            )
                        except Exception as e:
                            # Evidence writing should never crash orchestration
                            print(f"Warning: Failed to write orchestrator evidence bundle: {e}")
                        
                        # Check if we should continue or exit
                        if any(step.get('step') in ['handle_persistent_failure', 'finalize_run'] for step in plan_steps):
                            print("\n=== ORCHESTRATOR SUMMARY ===")
                            print(summary)
                            print(f"\nEvidence bundle at: {evidence_dir}")
                            break
                        
                        # Re-plan AFTER evidence bundle is written to pick up updated manifest.json state
                        # Temporarily disable corrected file detection to force wait step after approval
                        # We want to wait for a NEW corrected file, not resume with an old one
                        original_sharepoint_sim_root_polling = orchestrator.sharepoint_sim_root
                        orchestrator.sharepoint_sim_root = None  # Temporarily disable corrected file detection
                        updated_plan_steps = orchestrator.plan(inputs)
                        orchestrator.sharepoint_sim_root = original_sharepoint_sim_root_polling  # Restore
                        # If waiting, print status and continue polling (using updated plan)
                        waiting_steps = [s for s in updated_plan_steps if 'wait' in s.get('step', '').lower()]
                        if waiting_steps:
                            wait_step = waiting_steps[0]
                            wait_tool = wait_step.get('tool', '')
                            wait_args = wait_step.get('args', {})
                            
                            # Get detailed wait message from tool execution
                            # OrchestratorAgent is already imported at module level
                            if isinstance(orchestrator, OrchestratorAgent):
                                wait_result = orchestrator._invoke_tool(wait_tool, None, wait_args, {})
                                if wait_result and hasattr(wait_result, 'summary'):
                                    print(f"\n[Orchestrator] {wait_result.summary}")
                                else:
                                    print(f"\n[Orchestrator] {wait_step.get('step', 'Waiting')}...")
                            else:
                                print(f"\n[Orchestrator] {wait_step.get('step', 'Waiting')}...")
                    
                    time.sleep(args.poll_interval)
                    
            except KeyboardInterrupt:
                print("\nOrchestrator cancelled by user.")
                return
    
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
            # Extract partner from run_id
            parts = watch_run_id.split('-')
            partner_name = parts[0] if len(parts) > 0 else 'demo'
            
            # SharePoint simulation is at repo root, not in evidence_dir
            base_dir = Path(__file__).resolve().parents[1]
            uploads_dir = base_dir / "sharepoint_simulation" / "uploads" / partner_name

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
        # Get model name - check both platform-level and tool-level LLM usage
        # per BRD Section 2.3 (track LLM usage for Restricted data compliance)
        # and PRD-TRD Section 3.2 (complete evidence bundles)
        model_name = None
        
        # Check platform-level LLM (langchain platform)
        if args.platform == "langchain" and hasattr(agent, 'llm'):
            # Extract model name from LLM instance
            if hasattr(agent.llm, 'model_name'):
                model_name = agent.llm.model_name
            elif hasattr(agent.llm, 'model'):
                model_name = agent.llm.model
        
        # Check tool-level LLM usage (e.g., GeneratePartnerEmailTool uses LLM even with minimal platform)
        # Tools that use LLMs should report model in their ToolResult.data per BRD Section 2.3
        if not model_name and results:
            for tool_name, tool_result in results.items():
                if tool_result and tool_result.data:
                    tool_model = tool_result.data.get('model_used')
                    if tool_model:
                        model_name = tool_model
                        break
        
        # Fallback to environment variable if still not found
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
