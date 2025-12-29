"""CFA-specific validation rules per PRD-TRD Section 5.4 and BRD Section 8.2."""

# Approved completion types
COMPLETION_TYPES = [
    'completed on-time (continuous training)',
    'completed not on-time (non-continous training)'
]

# Approved noncompletion reasons
NONCOMPLETION_REASONS = [
    'could not meet the technical requirements for graduation',
    'withdrew due to family obligations',
    'withdrew due to physical health reasons',
    'withdrew due to mental health reasons',
    'withdrew due to lack of adequate transportation',
    'withdrew due to lack of childcare',
    'withdrew due to financial obligations e.g., had to get a full-time job',
    'dismissed due to behavior',
    'did not meet attendance requirements',
    'withdrew because they started a new job during training',
    'other'
]

# Approved employment statuses
EMPLOYMENT_STATUSES = [
    "employed in-field by an employer who doesn't partner with your training program",
    "employed in-field by an employer who partners with your training program",
    "still seeking employment in-field",
    "not seeking employment in-field",
    "could not contact"
]

# Approved employment types
EMPLOYMENT_TYPES = [
    'full-time employment',
    'part-time employment',
    'seasonal employment',
    'earn and learn employment',
    'other'
]

# Approved occupation codes
OCCUPATION_CODES = [
    'computer systems analysts (15-1211)',
    'information security analysts (15-1212)',
    'computer and information research scientists (15-1221)',
    'computer network support specialists (15-1231)',
    'computer user support specialists (15-1232)',
    'computer network architects (15-1241)',
    'database administrators (15-1242)',
    'database architects (15-1243)',
    'network and computer systems administrators (15-1244)',
    'computer programmers (15-1251)',
    'software developers (15-1252)',
    'software quality assurance analysts and testers (15-1253)',
    'web developers (15-1254)',
    'web and digital interface designers (15-1255)',
    'operations research analysts (15-2031)',
    'data scientists (15-2051)',
    'computer hardware engineers (17-2061)',
    'other computer occupations (15-1299)'
]

# Required headers (exact match, case-insensitive)
REQUIRED_HEADERS = [
    "First Name",
    "Last Name",
    "Date of Birth (MM/DD/YYYY)",
    "Address 1"
]

# File structure configuration
FILE_STRUCTURE = {
    "min_columns": 42,  # A-AP columns
    "header_row": 1,    # Row 1 contains headers
    "data_start_row": 2  # Data starts at row 2
}

# Field validation rules
# Each field can have: required, conditional_required, valid_values, format_constraints
FIELD_RULES = {
    "first_name": {
        "required": True,
        "conditional_required": None,
        "valid_values": None,
        "format_constraints": None
    },
    "last_name": {
        "required": True,
        "conditional_required": None,
        "valid_values": None,
        "format_constraints": None
    },
    "date_of_birth": {
        "required": True,
        "conditional_required": None,
        "valid_values": None,
        "format_constraints": {
            "format": "MM/DD/YYYY",
            "min_year": 1900,
            "max_date": "today"  # Cannot be in the future
        }
    },
    "address_1": {
        "required": True,
        "conditional_required": None,
        "valid_values": None,
        "format_constraints": {
            "no_po_box": True,
            "no_unit_info": True  # Unit info must be in Address 2
        }
    },
    "city": {
        "required": True,
        "conditional_required": None,
        "valid_values": None,
        "format_constraints": None
    },
    "state": {
        "required": True,
        "conditional_required": None,
        "valid_values": None,
        "format_constraints": None
    },
    "zip_code": {
        "required": True,
        "conditional_required": None,
        "valid_values": None,
        "format_constraints": {
            "format": "5_digits",
            "zip_plus_4_allowed": True  # Truncate to 5 digits if provided
        }
    },
    "training_start_date": {
        "required": True,
        "conditional_required": None,
        "valid_values": None,
        "format_constraints": {
            "format": "MM/DD/YYYY",
            "max_date": "today-1"  # Must be earlier than today
        }
    },
    "training_exit_date": {
        "required": False,
        "conditional_required": {
            "condition": "any_of",
            "fields": ["current_program_status", "noncompletion_reason"],
            "values": {
                "current_program_status": ["graduated/completed"],
                "noncompletion_reason": ["any_non_empty"]
            }
        },
        "valid_values": None,
        "format_constraints": {
            "format": "MM/DD/YYYY",
            "max_date": "today-1",  # Must be earlier than today
            "must_be_after": "training_start_date"
        }
    },
    "current_program_status": {
        "required": True,
        "conditional_required": None,
        "valid_values": None,
        "format_constraints": None
    },
    "completion_type": {
        "required": False,
        "conditional_required": {
            "condition": "field_equals",
            "field": "current_program_status",
            "value": "graduated/completed"
        },
        "valid_values": COMPLETION_TYPES,
        "format_constraints": None
    },
    "noncompletion_reason": {
        "required": False,
        "conditional_required": {
            "condition": "field_equals",
            "field": "current_program_status",
            "value": "withdrawn/terminated"
        },
        "valid_values": NONCOMPLETION_REASONS,
        "format_constraints": None
    },
    "noncompletion_other_specify": {
        "required": False,
        "conditional_required": {
            "condition": "field_equals",
            "field": "noncompletion_reason",
            "value": "other"
        },
        "valid_values": None,
        "format_constraints": None
    },
    "employment_status": {
        "required": False,
        "conditional_required": None,
        "valid_values": EMPLOYMENT_STATUSES,
        "format_constraints": None
    },
    "employer_name": {
        "required": False,
        "conditional_required": {
            "condition": "field_starts_with",
            "field": "employment_status",
            "value": "employed in-field"
        },
        "valid_values": None,
        "format_constraints": None
    },
    "employment_type": {
        "required": False,
        "conditional_required": {
            "condition": "field_starts_with",
            "field": "employment_status",
            "value": "employed in-field"
        },
        "valid_values": EMPLOYMENT_TYPES,
        "format_constraints": None
    },
    "earn_and_learn_specify": {
        "required": False,
        "conditional_required": {
            "condition": "field_equals",
            "field": "employment_type",
            "value": "earn and learn employment"
        },
        "valid_values": None,
        "format_constraints": None
    },
    "job_start_date": {
        "required": False,
        "conditional_required": {
            "condition": "field_starts_with",
            "field": "employment_status",
            "value": "employed in-field"
        },
        "valid_values": None,
        "format_constraints": {
            "format": "MM/DD/YYYY"
        }
    },
    "job_occupation": {
        "required": False,
        "conditional_required": {
            "condition": "field_starts_with",
            "field": "employment_status",
            "value": "employed in-field"
        },
        "valid_values": OCCUPATION_CODES,
        "format_constraints": None
    },
    "hourly_earnings": {
        "required": False,
        "conditional_required": {
            "condition": "field_starts_with",
            "field": "employment_status",
            "value": "employed in-field"
        },
        "valid_values": None,
        "format_constraints": None
    }
}

# Wraparound services code mappings
# Letter codes used in partner data "Wraparound services provided this quarter" column
# Per BRD Section 2.3 and PRD-TRD Section 5.4: business rules belong in rules.py
WRAPAROUND_SERVICE_CODES = {
    "a": "transportation",
    "b": "childcare",
    "c": "career_services_and_learning_materials",
    "d": "mental_health_services",
    "e": "life_skills",
    "f": "navigation",
    "g": "other"
}

# Reverse mapping for display names
WRAPAROUND_SERVICE_NAMES = {
    "transportation": "Transportation",
    "childcare": "Childcare",
    "career_services_and_learning_materials": "Career services and learning materials",
    "mental_health_services": "Mental health services",
    "life_skills": "Life skills",
    "navigation": "Navigation",
    "other": "Other"
}

# List of all service types (for iteration)
WRAPAROUND_SERVICE_TYPES = list(WRAPAROUND_SERVICE_NAMES.keys())

# Enhanced rules configuration (implementation details only - enablement in client_spec.yaml)
# Per BRD Section 2.3 and best practices: configuration (enablement) in YAML, implementation (logic) in rules.py
ENHANCED_RULES = {
    "active_past_graduation": {
        "severity": "Error",
        "description": "Check if participant marked active past graduation date"
    },
    "name_misspelling": {
        "severity": "Warning",
        "description": "Fuzzy matching for name misspelling detection"
    },
    "prevailing_wage": {
        "severity": "Error",
        "description": "Hardcoded prevailing wage validation (occupation code + region lookup)",
        "blocks_wsac_entry": True
    }
}

# Export all rules as a single RULES dict for engine consumption
RULES = {
    "completion_types": COMPLETION_TYPES,
    "noncompletion_reasons": NONCOMPLETION_REASONS,
    "employment_statuses": EMPLOYMENT_STATUSES,
    "employment_types": EMPLOYMENT_TYPES,
    "occupation_codes": OCCUPATION_CODES,
    "required_headers": REQUIRED_HEADERS,
    "file_structure": FILE_STRUCTURE,
    "field_rules": FIELD_RULES,
    "enhanced_rules": ENHANCED_RULES,
    "wraparound_service_codes": WRAPAROUND_SERVICE_CODES,
    "wraparound_service_names": WRAPAROUND_SERVICE_NAMES,
    "wraparound_service_types": WRAPAROUND_SERVICE_TYPES
}
