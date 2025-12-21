"""SimpleIntakeAgent per PRD-TRD Section 5.1.

Deterministic baseline agent demonstrating BaseAgent contract with hardcoded orchestration.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .base_agent import BaseAgent
from ..core.canonical.canonicalize_tool import CanonicalizeStagedDataTool
from ..core.ingestion.ingest_tool import IngestPartnerFileTool
from ..core.validation.validate_tool import ValidateStagedDataTool


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
        self.run_id = run_id
        self.evidence_dir = evidence_dir
        self.tool_calls_log = []
        
        # Initialize tools per PRD-TRD Section 5.4
        self.ingest_tool = IngestPartnerFileTool()
        self.validate_tool = ValidateStagedDataTool()
        self.canonicalize_tool = CanonicalizeStagedDataTool()
        
        # Tool registry for execute()
        self.tools = {
            'IngestPartnerFileTool': self.ingest_tool,
            'ValidateStagedDataTool': self.validate_tool,
            'CanonicalizeStagedDataTool': self.canonicalize_tool,
        }
    
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
    
    def _emit(self, event_type: str, message: str, data: Dict[str, Any]) -> None:
        """Emit trace event to tool_calls.jsonl per PRD-TRD Section 7.4.
        
        BaseAgent.execute() wraps tool calls and appends JSONL events directly to
        tool_calls.jsonl as tools run (BaseAgent owns tool_calls.jsonl writing).
        
        Args:
            event_type: Type of event (STEP_START, STEP_END)
            message: Human-readable message
            data: Sanitized metadata only (counts, hashes, status) - no DataFrames or raw data
        """
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "run_id": self.run_id,
            "message": message,
            "data": data
        }
        
        # Store in memory for now, will write to file at end
        self.tool_calls_log.append(event)
        
        # Append to tool_calls.jsonl per BRD FR-011
        if self.evidence_dir:
            tool_calls_path = self.evidence_dir / "tool_calls.jsonl"
            with open(tool_calls_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event) + '\n')
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate tools to fulfill the plan per PRD-TRD Section 5.1.
        
        Wraps each tool call with evidence logging per PRD-TRD Section 7.4.
        Emits STEP_START and STEP_END events to tool_calls.jsonl with sanitized
        metadata only (counts, hashes, status) - no DataFrames or raw data.
        
        Args:
            inputs: Dictionary containing file_path and run_id
            
        Returns:
            Dictionary with step outcomes and canonical data (in-memory objects in data)
        """
        plan_steps = self.plan(inputs)
        results = {}
        staged_dataframe = None
        
        for step in plan_steps:
            tool_name = step['tool']
            tool_args = step['args'].copy()
            
            # Emit STEP_START event to tool_calls.jsonl per BRD FR-011
            self._emit("STEP_START", f"Executing {tool_name}", {
                "tool": tool_name,
                "args": tool_args
            })
            
            # Get tool instance
            tool = self.tools[tool_name]
            
            # Pass dataframe from previous step if needed
            if tool_name == 'ValidateStagedDataTool' and staged_dataframe is not None:
                # ValidateStagedDataTool expects DataFrame as parameter
                result = tool(staged_dataframe)
            elif tool_name == 'CanonicalizeStagedDataTool' and staged_dataframe is not None:
                # CanonicalizeStagedDataTool expects DataFrame as parameter
                result = tool(staged_dataframe)
            else:
                # Invoke tool with args - returns ToolResult with in-memory data for chaining per PRD-TRD Section 5.4
                result = tool(**tool_args)
            
            # Pass dataframe from previous step if needed
            if tool_name == 'ValidateStagedDataTool' and staged_dataframe is not None:
                # ValidateStagedDataTool expects DataFrame as parameter
                result = tool(staged_dataframe)
            elif tool_name == 'CanonicalizeStagedDataTool' and staged_dataframe is not None:
                # CanonicalizeStagedDataTool expects DataFrame as parameter
                result = tool(staged_dataframe)
            else:
                # Invoke tool with args - returns ToolResult with in-memory data for chaining per PRD-TRD Section 5.4
                result = tool(**tool_args)
            
            # Store dataframe for next step
            if tool_name == 'IngestPartnerFileTool' and result.ok:
                staged_dataframe = result.data.get('dataframe')
            elif tool_name == 'ValidateStagedDataTool' and result.ok:
                # Validation doesn't modify the dataframe, pass it through
                staged_dataframe = staged_dataframe  # Keep same dataframe
            elif tool_name == 'CanonicalizeStagedDataTool' and result.ok:
                staged_dataframe = result.data.get('canonical_dataframe')
            
            # Emit STEP_END with sanitized metadata only (no DataFrames) per PRD-TRD Section 3.2
            sanitized_data = {
                "tool": tool_name,
                "ok": result.ok,
                "summary": result.summary
            }
            
            # Add sanitized metadata only (counts, hashes, status) - no raw data
            if 'row_count' in result.data:
                sanitized_data['row_count'] = result.data['row_count']
            if 'file_hash' in result.data:
                sanitized_data['file_hash'] = result.data['file_hash']
            if 'error_count' in result.data:
                sanitized_data['error_count'] = result.data['error_count']
            if 'warning_count' in result.data:
                sanitized_data['warning_count'] = result.data['warning_count']
            if 'record_count' in result.data:
                sanitized_data['record_count'] = result.data['record_count']
            
            self._emit("STEP_END", f"Completed {tool_name}", sanitized_data)
            
            # Store result
            results[tool_name] = result
            
            # Stop on blockers per PRD-TRD Section 5.1
            if not result.ok or result.blockers:
                break
        
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

