"""Shared BaseAgent contract for all agent implementations."""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.tools import ToolResult


class BaseAgent(ABC):
    """Defines the orchestration contract for all agents.

    Agents must plan, coordinate tool usage, and produce evidence
    bundles without directly performing deterministic business logic.
    
    This base class enforces evidence logging pattern per PRD-TRD Section 7.4
    using the Template Method pattern. Subclasses customize behavior via hook methods.
    """

    def __init__(self, run_id: Optional[str] = None, evidence_dir: Optional[Path] = None):
        """Initialize BaseAgent with evidence logging support.
        
        Args:
            run_id: Run identifier for evidence bundle
            evidence_dir: Directory for evidence bundle (where tool_calls.jsonl is written)
        """
        self.run_id = run_id
        self.evidence_dir = evidence_dir
        self.tool_calls_log = []
        self.tools: Dict[str, Any] = {}  # Subclasses populate this in __init__

    @abstractmethod
    def plan(self, inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return structured execution steps for the provided inputs.
        
        Returns a list of step dictionaries, each containing:
        - 'tool': name of the tool to execute
        - 'args': dictionary of arguments to pass to the tool
        
        Human-readable plan.md is generated from structured steps by write_evidence.py.
        """
        pass

    def _emit(self, event_type: str, message: str, data: Dict[str, Any]) -> None:
        """Emit trace event to tool_calls.jsonl per PRD-TRD Section 7.4.
        
        Subclasses can override for custom logging, but should call super().
        
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
        
        self.tool_calls_log.append(event)
        
        # Append to tool_calls.jsonl per BRD FR-011
        if self.evidence_dir:
            tool_calls_path = self.evidence_dir / "tool_calls.jsonl"
            with open(tool_calls_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event) + '\n')

    def _sanitize_tool_result(self, result: ToolResult) -> Dict[str, Any]:
        """Extract sanitized metadata from ToolResult (no DataFrames or raw data).
        
        Subclasses can override to add custom sanitization.
        
        Args:
            result: ToolResult from tool execution
        
        Returns:
            Dictionary with sanitized metadata only
        """
        sanitized = {
            "ok": result.ok,
            "summary": result.summary
        }
        
        # Add sanitized metadata only (counts, hashes, status) - no raw data
        for key in ['row_count', 'file_hash', 'error_count', 'warning_count', 
                    'record_count', 'total_participants', 'error_row_count', 
                    'total_row_count']:
            if key in result.data:
                sanitized[key] = result.data[key]
        
        return sanitized

    def _invoke_tool(self, tool_name: str, tool: Any, tool_args: Dict[str, Any], 
                    context: Dict[str, Any]) -> ToolResult:
        """Invoke tool with prepared arguments.
        
        Subclasses can override to handle special tool invocation patterns
        (e.g., tools that take DataFrames as positional arguments).
        
        Args:
            tool_name: Name of the tool
            tool: Tool instance
            tool_args: Prepared arguments dictionary
            context: Execution context
        
        Returns:
            ToolResult from tool execution
        """
        # Default: invoke with keyword arguments
        return tool(**tool_args)

    def _prepare_tool_args(self, step: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare tool arguments, allowing subclasses to inject context (e.g., DataFrames).
        
        Args:
            step: Step dictionary with 'tool' and 'args' keys
            context: Execution context (e.g., staged_dataframe from previous steps)
        
        Returns:
            Prepared arguments dictionary
        """
        return step['args'].copy()

    def _handle_tool_result(self, step: Dict[str, Any], result: ToolResult, 
                           context: Dict[str, Any]) -> None:
        """Handle tool result, allowing subclasses to update context or trigger side effects.
        
        Args:
            step: Step dictionary
            result: ToolResult from tool execution
            context: Execution context (can be modified by subclass)
        """
        pass  # Default: no-op

    def _handle_custom_orchestration(self, step: Dict[str, Any], result: ToolResult,
                                    context: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Handle custom orchestration logic after a step (e.g., HITL workflows).
        
        Args:
            step: Completed step dictionary
            result: ToolResult from step
            context: Execution context
            inputs: Original inputs
        
        Returns:
            Dictionary of additional results from custom orchestration (merged into main results)
        """
        return {}  # Default: no custom orchestration

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate tools to fulfill the plan with enforced evidence logging.
        
        This method enforces the evidence logging pattern per PRD-TRD Section 7.4.
        Subclasses can customize behavior via hook methods rather than overriding execute().
        
        Args:
            inputs: Input dictionary
        
        Returns:
            Dictionary with step outcomes
        """
        plan_steps = self.plan(inputs)
        results = {}
        context = {}  # Execution context (e.g., staged_dataframe)
        
        for step in plan_steps:
            tool_name = step['tool']
            
            # Emit STEP_START event to tool_calls.jsonl per BRD FR-011
            self._emit("STEP_START", f"Executing {tool_name}", {
                "tool": tool_name,
                "args": step['args']
            })
            
            # Prepare tool arguments (allows subclasses to inject context)
            tool_args = self._prepare_tool_args(step, context)
            
            # Get tool instance
            tool = self.tools.get(tool_name)
            if not tool:
                raise ValueError(f"Tool '{tool_name}' not found in tools registry")
            
            # Invoke tool - returns ToolResult with in-memory data for chaining
            result = self._invoke_tool(tool_name, tool, tool_args, context)
            
            # Handle tool result (allows subclasses to update context)
            self._handle_tool_result(step, result, context)
            
            # Emit STEP_END with sanitized metadata only (no DataFrames) per PRD-TRD Section 3.2
            sanitized_data = {
                "tool": tool_name,
                **self._sanitize_tool_result(result)
            }
            self._emit("STEP_END", f"Completed {tool_name}", sanitized_data)
            
            # Store result
            results[tool_name] = result
            
            # Handle custom orchestration (e.g., HITL workflows)
            custom_results = self._handle_custom_orchestration(step, result, context, inputs)
            results.update(custom_results)
            
            # Check if custom orchestration halted execution
            if custom_results.get('_halted', False):
                return results
            
            # Stop on blockers per PRD-TRD Section 5.1
            if not result.ok or result.blockers:
                break
        
        return results

    @abstractmethod
    def summarize(self, run_results: Dict[str, Any]) -> str:
        """Produce a staff-facing summary describing decisions and outcomes."""
        pass
