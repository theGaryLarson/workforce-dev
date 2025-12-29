"""Validation engine framework for loading client-specific configuration per PRD-TRD Section 5.4."""

import importlib
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ValidationEngine:
    """Loads and provides access to client-specific validation rules and configuration.
    
    Per PRD-TRD Section 5.4 and BRD Section 8.2, validation rules are loaded from
    client-specific files rather than being hardcoded in the validation tool.
    """
    
    def __init__(self, client_id: str = "cfa"):
        """Initialize validation engine for a specific client.
        
        Args:
            client_id: Client identifier (default: "cfa")
            
        Raises:
            FileNotFoundError: If client files don't exist
        """
        self.client_id = client_id
        self.rules = self._load_rules()
        self.config = self._load_config()
        self.mappings = self._load_mappings()
    
    def _load_rules(self) -> Dict[str, Any]:
        """Dynamically import rules from clients/{client_id}/rules.py.
        
        Returns:
            RULES dict from the client's rules module
            
        Raises:
            FileNotFoundError: If rules.py doesn't exist
        """
        try:
            module_path = f"agentic_systems.clients.{self.client_id}.rules"
            module = importlib.import_module(module_path)
            if not hasattr(module, "RULES"):
                raise FileNotFoundError(
                    f"RULES dict not found in {module_path}. "
                    "Ensure rules.py exports RULES dict."
                )
            return module.RULES
        except ImportError as e:
            raise FileNotFoundError(
                f"Could not load rules from clients/{self.client_id}/rules.py: {e}"
            )
    
    def _load_config(self) -> Dict[str, Any]:
        """Load and parse client_spec.yaml configuration.
        
        Returns:
            Parsed YAML configuration dict
            
        Raises:
            FileNotFoundError: If client_spec.yaml doesn't exist
        """
        # Get the path to the client directory
        current_file = Path(__file__)
        clients_dir = current_file.parent.parent.parent / "clients" / self.client_id
        config_path = clients_dir / "client_spec.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"Client configuration not found: {config_path}. "
                f"Ensure clients/{self.client_id}/client_spec.yaml exists."
            )
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_mappings(self) -> Dict[str, Any]:
        """Dynamically import mappings from clients/{client_id}/mappings.py.
        
        Returns:
            MAPPINGS dict from the client's mappings module
            
        Raises:
            FileNotFoundError: If mappings.py doesn't exist
        """
        try:
            module_path = f"agentic_systems.clients.{self.client_id}.mappings"
            module = importlib.import_module(module_path)
            if not hasattr(module, "MAPPINGS"):
                raise FileNotFoundError(
                    f"MAPPINGS dict not found in {module_path}. "
                    "Ensure mappings.py exports MAPPINGS dict."
                )
            return module.MAPPINGS
        except ImportError as e:
            raise FileNotFoundError(
                f"Could not load mappings from clients/{self.client_id}/mappings.py: {e}"
            )
    
    def get_approved_values(self, value_type: str) -> List[str]:
        """Get approved values for a specific value type.
        
        Args:
            value_type: One of "completion_types", "noncompletion_reasons",
                       "employment_statuses", "employment_types", "occupation_codes"
        
        Returns:
            List of approved values
        """
        return self.rules.get(value_type, [])
    
    def get_field_rule(self, field_name: str) -> Optional[Dict[str, Any]]:
        """Get validation rule for a specific field.
        
        Args:
            field_name: Canonical field name (e.g., "first_name", "date_of_birth")
        
        Returns:
            Field rule dict or None if not found
        """
        field_rules = self.rules.get("field_rules", {})
        return field_rules.get(field_name)
    
    def get_required_headers(self) -> List[str]:
        """Get list of required headers.
        
        Returns:
            List of required header names
        """
        return self.rules.get("required_headers", [])
    
    def get_file_structure(self) -> Dict[str, Any]:
        """Get file structure configuration, preferring YAML config over rules.py.
        
        Returns:
            Dict with min_columns, header_row, data_start_row
            YAML config takes precedence; rules.py provides fallback defaults.
        """
        # Prefer YAML config
        validation_config = self.config.get("validation", {})
        yaml_structure = {
            "min_columns": validation_config.get("min_columns"),
            "header_row": validation_config.get("header_row"),
            "data_start_row": validation_config.get("data_start_row")
        }
        
        # Fallback to rules.py defaults
        rules_structure = self.rules.get("file_structure", {})
        
        # Merge with YAML taking precedence
        return {
            "min_columns": yaml_structure.get("min_columns") or rules_structure.get("min_columns", 42),
            "header_row": yaml_structure.get("header_row") or rules_structure.get("header_row", 1),
            "data_start_row": yaml_structure.get("data_start_row") or rules_structure.get("data_start_row", 2)
        }
    
    def get_canonical_mappings(self) -> Dict[str, Dict[str, List[str]]]:
        """Get canonical field mappings from config.
        
        Returns:
            Dict mapping canonical field names to their header patterns
            Format: {canonical_field: {"patterns": [pattern1, pattern2, ...]}}
        """
        return self.config.get("canonical_mappings", {})
    
    def should_halt_on_error(self) -> bool:
        """Check if validation should halt on errors.
        
        Returns:
            True if halt_on_error is enabled (default: True per BRD Section 2.3)
        """
        validation_config = self.config.get("validation", {})
        return validation_config.get("halt_on_error", True)
    
    def get_warning_threshold(self) -> Optional[int]:
        """Get configurable warning threshold per BRD Section 2.3.
        
        Returns:
            Warning threshold value, or None if not configured
        """
        validation_config = self.config.get("validation", {})
        return validation_config.get("halt_on_warning_threshold") or validation_config.get("max_warnings_before_halt")
    
    def get_enhanced_rule_config(self, rule_name: str) -> Optional[Dict[str, Any]]:
        """Get enhanced rule enablement and thresholds from YAML config.
        
        Args:
            rule_name: Name of the enhanced rule (e.g., "active_past_graduation")
        
        Returns:
            Dict with enablement flags and thresholds, or None if rule not found
        """
        validation_config = self.config.get("validation", {})
        enhanced_rules = validation_config.get("enhanced_rules", {})
        return enhanced_rules.get(rule_name)
    
    def get_enhanced_rules(self) -> Dict[str, Any]:
        """Get enhanced rules implementation details from rules.py (no enablement flags).
        
        Returns:
            Dict of enhanced rule implementation details (severity, description, etc.)
        """
        return self.rules.get("enhanced_rules", {})
    
    def get_data_classification(self) -> Dict[str, Any]:
        """Get data classification configuration from YAML.
        
        Returns:
            Dict with default classification and PII handling settings
            Per BRD Section 2.3: "Partner data is Confidential by default"
        """
        return self.config.get("data_classification", {})
