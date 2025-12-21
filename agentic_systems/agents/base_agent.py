"""Shared BaseAgent contract for all agent implementations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseAgent(ABC):
    """Defines the orchestration contract for all agents.

    Agents must plan, coordinate tool usage, and produce evidence
    bundles without directly performing deterministic business logic.
    """

    @abstractmethod
    def plan(self, inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return structured execution steps for the provided inputs.
        
        Returns a list of step dictionaries, each containing:
        - 'tool': name of the tool to execute
        - 'args': dictionary of arguments to pass to the tool
        
        Human-readable plan.md is generated from structured steps by write_evidence.py.
        """

    @abstractmethod
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate tools to fulfill the plan and return outputs."""

    @abstractmethod
    def summarize(self, run_results: Dict[str, Any]) -> str:
        """Produce a staff-facing summary describing decisions and outcomes."""
