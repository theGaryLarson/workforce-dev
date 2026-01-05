"""Partner-specific parsing configuration loader per multi-partner support."""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml


def load_partner_parsing_config(client_id: str, partner_name: str) -> Optional[Dict[str, Any]]:
    """Load partner-specific parsing configuration.
    
    Args:
        client_id: Client identifier (e.g., "cfa")
        partner_name: Partner identifier (e.g., "test-partner-1")
        
    Returns:
        Dictionary with parsing configuration, or None if not found
    """
    # Path to partner parsing config
    base_dir = Path(__file__).resolve().parents[2]  # Go up to agentic_systems
    config_path = base_dir / "clients" / client_id / "partners" / partner_name / "parsing_config.yaml"
    
    if not config_path.exists():
        return None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_partner_name_from_path(file_path: Path, partner_uploads_dir: Path) -> Optional[str]:
    """Extract partner name from file path.
    
    Args:
        file_path: Path to the file
        partner_uploads_dir: Base directory for partner uploads
        
    Returns:
        Partner name if found, None otherwise
    """
    try:
        # Get relative path from partner_uploads_dir
        relative_path = file_path.relative_to(partner_uploads_dir)
        # First component should be partner name
        parts = relative_path.parts
        if len(parts) > 1:
            return parts[0]
    except (ValueError, AttributeError):
        pass
    return None
