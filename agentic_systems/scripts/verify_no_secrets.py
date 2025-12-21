"""Local preflight checks to ensure secrets are not committed."""

from pathlib import Path


def has_disallowed_files(base_path: Path) -> bool:
    """Detect obvious secret files in the working tree."""

    forbidden = {".env", "secrets.json", "service.key"}
    return any((base_path / item).exists() for item in forbidden)
