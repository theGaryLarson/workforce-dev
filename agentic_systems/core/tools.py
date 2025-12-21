"""Tool protocol and ToolResult dataclass per PRD-TRD Section 5.4."""

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol


class Tool(Protocol):
    """Protocol defining the interface for all tools per PRD-TRD Section 5.4.
    
    Tools are deterministic, versioned, parameterized components that perform
    specific tasks. They do not contain orchestration logic.
    """
    
    name: str
    
    def __call__(self, **kwargs: Any) -> "ToolResult":
        """Execute the tool with provided arguments and return a ToolResult."""
        ...


@dataclass
class ToolResult:
    """Standardized result structure for all tool executions per PRD-TRD Section 5.4.
    
    ToolResult.data can contain in-memory objects (DataFrames, lists) for tool chaining.
    Only sanitized metadata (counts, hashes, status) is logged to tool_calls.jsonl
    per PRD-TRD Section 3.2 - no DataFrames or raw data in evidence logs.
    """
    
    ok: bool
    """Success/failure indicator."""
    
    summary: str
    """Human-readable summary of the tool execution."""
    
    data: Dict[str, Any]
    """Structured data - may contain in-memory objects (DataFrames, lists) for tool chaining.
    
    Note: Evidence logging uses sanitized metadata only. The evidence writer
    (write_evidence.py) serializes in-memory tool results to outputs/ directory once.
    """
    
    warnings: List[str]
    """Non-blocking issues that don't prevent execution."""
    
    blockers: List[str]
    """Blocking errors that prevent further execution."""

