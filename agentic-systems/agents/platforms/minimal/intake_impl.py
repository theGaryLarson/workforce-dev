"""Minimal platform intake adapter implementing the BaseAgent contract."""

from typing import Any, Dict

from ...base_agent import BaseAgent


class MinimalIntakeAgent(BaseAgent):
    """Adapter showcasing the smallest viable intake implementation."""

    platform_name = "minimal"

    def plan(self, inputs: Dict[str, Any]) -> str:
        return "Minimal intake plan for deterministic local execution."

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return {"platform": self.platform_name, "status": "pending", "inputs": inputs}

    def summarize(self, run_results: Dict[str, Any]) -> str:
        return "Executed minimal intake flow with local evidence bundle."
