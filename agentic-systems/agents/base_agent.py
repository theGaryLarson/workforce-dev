"""Shared BaseAgent contract for all agent implementations."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """Defines the orchestration contract for all agents.

    Agents must plan, coordinate tool usage, and produce evidence
    bundles without directly performing deterministic business logic.
    """

    @abstractmethod
    def plan(self, inputs: Dict[str, Any]) -> str:
        """Return a human-readable execution plan for the provided inputs."""

    @abstractmethod
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate tools to fulfill the plan and return outputs."""

    @abstractmethod
    def summarize(self, run_results: Dict[str, Any]) -> str:
        """Produce a staff-facing summary describing decisions and outcomes."""
