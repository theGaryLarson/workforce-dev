"""Anthropic platform intake adapter implementing the BaseAgent contract."""

from typing import Any, Dict

from ...base_agent import BaseAgent


class AnthropicIntakeAgent(BaseAgent):
    """Adapter for executing intake flows on Anthropic tooling."""

    platform_name = "anthropic"

    def plan(self, inputs: Dict[str, Any]) -> str:
        return "Anthropic-specific intake plan aligned with audit needs."

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        return {"platform": self.platform_name, "status": "pending", "inputs": inputs}

    def summarize(self, run_results: Dict[str, Any]) -> str:
        return "Executed Anthropic intake flow with governance guardrails."
