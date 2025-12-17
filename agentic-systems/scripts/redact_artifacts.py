"""Utilities for scrubbing PII from evidence bundles."""

from pathlib import Path


def redact_bundle(run_path: Path) -> None:
    """Placeholder redaction hook.

    Implement PII redaction for artifacts stored within ``run_path``
    when approved egress or minimization is required.
    """

    # TODO: implement redaction logic
    _ = run_path
