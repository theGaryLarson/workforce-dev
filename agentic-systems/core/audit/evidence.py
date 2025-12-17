"""Evidence validation helpers for agent runs.

This module defines helper routines for validating evidence bundles
written to ``core/audit/runs``. Implementations should ensure required
artifacts exist and enforce data classification declarations.
"""

from pathlib import Path
from typing import Iterable


def validate_required_artifacts(run_path: Path, required_files: Iterable[str]) -> list[str]:
    """Validate that all required artifacts are present for a run.

    Args:
        run_path: Base directory for the agent run evidence bundle.
        required_files: Relative file names expected inside ``run_path``.

    Returns:
        A list of missing artifact paths relative to ``run_path``.
    """

    missing: list[str] = []
    for artifact in required_files:
        candidate = run_path / artifact
        if not candidate.exists():
            missing.append(artifact)
    return missing
