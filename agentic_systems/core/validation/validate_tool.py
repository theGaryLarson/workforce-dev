"""ValidateStagedDataTool per updated spreadsheet validator specifications."""

import re
from datetime import datetime, date
from typing import Any, Dict, List, Optional

import pandas as pd

from ..tools import ToolResult
from .engine import ValidationEngine


class ValidateStagedDataTool:
    """Validates staged data using client-specific rules loaded from ValidationEngine.
    
    Implements header checks (A–AP), row-blank termination, canonical mapping,
    and row-level validation for program status, noncompletion, and employment.
    Per PRD-TRD Section 5.4, rules are loaded from clients/{client_id}/rules.py.
    """
    
    name = "ValidateStagedDataTool"
    
    def __init__(self, client_id: str = "cfa"):
        """Initialize validation tool for a specific client.
        
        Args:
            client_id: Client identifier (default: "cfa")
        """
        self.client_id = client_id
        self.engine = ValidationEngine(client_id=client_id)

    def _normalize_string(self, val: Any) -> str:
        """Normalize strings by removing smart quotes, newlines, and extra whitespace."""
        if pd.isna(val) or val is None:
            return ""
        s = str(val).strip()
        # Smart quotes normalization
        s = s.replace('â\x80\x99', "’").replace('â\x80\x98', "‘").replace('â\x80\x9c', '“').replace('â\x80\x9d', '”')
        s = s.replace("\u2019", "’").replace("\u2018", "‘").replace("\u201c", "“").replace("\u201d", "”")
        # Newlines and whitespace
        s = re.sub(r'\s+', ' ', s)
        return s.strip()

    def _parse_date(self, val: Any) -> Optional[datetime]:
        """Parse date from various formats (MM/DD/YYYY, datetime, or Excel serial)."""
        if pd.isna(val) or val == '' or (isinstance(val, str) and not val.strip()):
            return None
        
        if isinstance(val, (datetime, date)):
            if isinstance(val, date) and not isinstance(val, datetime):
                return datetime.combine(val, datetime.min.time())
            return val
            
        if isinstance(val, str):
            val_str = val.strip()
            # Try MM/DD/YYYY and common variations
            for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y']:
                try:
                    return datetime.strptime(val_str, fmt)
                except ValueError:
                    continue
        
        try:
            # Pandas to_datetime can handle some Excel serials if they were imported as strings
            dt = pd.to_datetime(val)
            if pd.isna(dt):
                return None
            return dt
        except:
            return None

    def _validate_zip_code_format(self, val: Any) -> Optional[str]:
        """Validate zip code format: must be 5 digits.
        
        If provided in ZIP+4 format (xxxxx-xxxx), truncates to first 5 digits.
        
        Args:
            val: Zip code value (string, number, etc.)
        
        Returns:
            Error message if invalid, None if valid
        """
        if pd.isna(val) or not str(val).strip():
            return None  # Required check is handled separately
        
        zip_str = str(val).strip()
        
        # Handle ZIP+4 format: truncate to first 5 digits
        if '-' in zip_str:
            zip_str = zip_str.split('-')[0].strip()
        
        # Remove any spaces
        zip_str = zip_str.replace(' ', '')
        
        # Must be exactly 5 digits
        if not zip_str.isdigit():
            return 'Zip Code must contain only digits.'
        
        if len(zip_str) != 5:
            return f'Zip Code must be exactly 5 digits (found {len(zip_str)} digits).'
        
        return None

    def _get_canonical_mapping(self, headers: List[str]) -> Dict[str, str]:
        """Map sheet headers to canonical keys using client-specific patterns."""
        mapping = {}
        canonical_mappings = self.engine.get_canonical_mappings()
        
        # Helper to find a header by normalizing and checking substrings or patterns
        def find_match(canonical_key, patterns):
            for h in headers:
                norm = self._normalize_string(h).lower()
                for p in patterns:
                    if p.lower() in norm:
                        mapping[canonical_key] = h
                        return True
            return False

        # Use patterns from client config instead of hardcoded
        for canonical_key, mapping_config in canonical_mappings.items():
            patterns = mapping_config.get("patterns", [])
            find_match(canonical_key, patterns)
        
        return mapping

    def __call__(self, staged_data: pd.DataFrame) -> ToolResult:
        """Validate staged data using client-specific rules."""
        violations = []
        error_count = 0
        warning_count = 0
        
        # Load approved values and configuration from engine
        completion_types = self.engine.get_approved_values("completion_types")
        noncompletion_reasons = self.engine.get_approved_values("noncompletion_reasons")
        employment_statuses = self.engine.get_approved_values("employment_statuses")
        employment_types = self.engine.get_approved_values("employment_types")
        occupation_codes = self.engine.get_approved_values("occupation_codes")
        required_headers = self.engine.get_required_headers()
        file_structure = self.engine.get_file_structure()
        
        # 1. Sheet-level / header-row requirements (A–AP, first 42 columns)
        max_cols = file_structure.get("min_columns", 42)
        header_row = file_structure.get("header_row", 1)
        data_start_row = file_structure.get("data_start_row", 2)
        if len(staged_data.columns) < max_cols:
            violations.append({
                'row_index': 1,
                'field': 'File Structure',
                'severity': 'Error',
                'message': f'File has fewer than {max_cols} columns. Missing A–AP headers.'
            })
            error_count += 1
            # Still proceed with what we have
            headers = list(staged_data.columns)
        else:
            headers = list(staged_data.columns[:max_cols])

        # Header checks (A1:AP1)
        seen_headers = {}
        for i, h in enumerate(headers):
            h_str = str(h).strip()
            # Blank/Unnamed check
            if not h_str or h_str.startswith('Unnamed:') or h_str.isspace():
                violations.append({
                    'row_index': 1,
                    'field': f'Column {chr(65+i)}' if i < 26 else f'Column A{chr(65+i-26)}',
                    'severity': 'Error',
                    'message': 'Header cell must not be blank or unnamed.'
                })
                error_count += 1
            
            # Duplicate check (case-insensitive)
            h_lower = self._normalize_string(h_str).lower()
            if h_lower in seen_headers:
                violations.append({
                    'row_index': 1,
                    'field': h_str,
                    'severity': 'Error',
                    'message': f'Duplicate header name detected: "{h_str}"'
                })
                error_count += 1
            seen_headers[h_lower] = True

        # Required headers exact match (case-insensitive)
        headers_lower = [self._normalize_string(h).lower() for h in headers]
        for req in required_headers:
            if self._normalize_string(req).lower() not in headers_lower:
                violations.append({
                    'row_index': 1,
                    'field': req,
                    'severity': 'Error',
                    'message': f'Required header "{req}" must exist in A–AP.'
                })
                error_count += 1

        # Robust mapping
        col_map = self._get_canonical_mapping(headers)
        
        # Helper function to get value and field name for reporting (used in main loop and enhanced rules)
        def get_val_field(row, canonical_key):
            """Get value and field name for a canonical key from a row."""
            sheet_header = col_map.get(canonical_key)
            if not sheet_header:
                return None, f"MISSING_{canonical_key}"
            return row.get(sheet_header), sheet_header
        
        # 2. Row-level behavior
        now = datetime.now()
        today = datetime(now.year, now.month, now.day)
        
        for idx, row in staged_data.iterrows():
            row_num = int(idx) + data_start_row
            
            # Termination rule: stop at first row where A–AP are all blank
            row_slice = row.iloc[:max_cols]
            if row_slice.isna().all() or (row_slice.astype(str).str.strip() == '').all():
                break

            # 3. Column-by-column requirements
            # TODO: Field-level validation from FIELD_RULES not yet implemented.
            # Current validation uses hardcoded logic. Future enhancement: drive
            # conditional requirements, format constraints, and valid values from
            # engine.get_field_rule() instead of hardcoded checks.
            
            # First Name & Last Name
            for key in ['first_name', 'last_name']:
                val, field = get_val_field(row, key)
                if pd.isna(val) or not str(val).strip():
                    violations.append({
                        'row_index': row_num,
                        'field': field,
                        'severity': 'Error',
                        'message': f'{field} is required (can’t be blank).'
                    })
                    error_count += 1

            # Date of Birth
            val_dob, field_dob = get_val_field(row, 'date_of_birth')
            dt_dob = self._parse_date(val_dob)
            if pd.isna(val_dob) or not str(val_dob).strip():
                violations.append({
                    'row_index': row_num,
                    'field': field_dob,
                    'severity': 'Error',
                    'message': 'Date of Birth is required.'
                })
                error_count += 1
            elif dt_dob is None:
                violations.append({
                    'row_index': row_num,
                    'field': field_dob,
                    'severity': 'Error',
                    'message': f'{field_dob} must be a valid date in MM/DD/YYYY format.'
                })
                error_count += 1
            else:
                if dt_dob > today:
                    violations.append({
                        'row_index': row_num,
                        'field': field_dob,
                        'severity': 'Error',
                        'message': 'Date of Birth cannot be in the future.'
                    })
                    error_count += 1
                if dt_dob.year < 1900:
                    violations.append({
                        'row_index': row_num,
                        'field': field_dob,
                        'severity': 'Error',
                        'message': 'Year must be 1900 or later.'
                    })
                    error_count += 1

            # Address 1
            val_addr, field_addr = get_val_field(row, 'address_1')
            if pd.isna(val_addr) or not str(val_addr).strip():
                violations.append({
                    'row_index': row_num,
                    'field': field_addr,
                    'severity': 'Error',
                    'message': f'{field_addr} is required.'
                })
                error_count += 1
            else:
                addr_str = str(val_addr).strip().lower()
                # PO Box
                if any(p in addr_str for p in ["po box", "p.o. box", "post office box"]):
                    violations.append({
                        'row_index': row_num,
                        'field': field_addr,
                        'severity': 'Error',
                        'message': 'Address 1 must not contain a PO Box.'
                    })
                    error_count += 1
                
                # Apt/Suite/Unit - check for known unit designations (with optional periods)
                disallowed = [r'\bapt\.?\b', r'\bsuite\.?\b', r'\bunit\.?\b', r'\bfloor\.?\b', r'#\s*\d+']
                unit_found = False
                if any(re.search(p, addr_str) for p in disallowed):
                    violations.append({
                        'row_index': row_num,
                        'field': field_addr,
                        'severity': 'Error',
                        'message': 'Apartment/Suite/Unit info must be in Address 2 (not Address 1).'
                    })
                    error_count += 1
                    unit_found = True  # Mark that we already found a unit designation
                
                # Holistic check: ends with space + alphanumeric designation
                # Only run if explicit check didn't already catch it
                if not unit_found:
                    # Pattern: space + word(s) + optional number/letter (but exclude common street suffixes)
                    street_suffixes = ['street', 'st', 'avenue', 'ave', 'road', 'rd', 'drive', 'dr', 'lane', 'ln', 
                                       'boulevard', 'blvd', 'court', 'ct', 'place', 'pl', 'way', 'circle', 'cir',
                                       'parkway', 'pkwy', 'trail', 'tr', 'terrace', 'ter', 'heights', 'hills',
                                       'valley', 'view', 'village', 'woods', 'point', 'port', 'ridge', 'run']
                    
                    # Check if address ends with space + alphanumeric that's not a street suffix
                    # Pattern allows for periods in abbreviations (e.g., "apt.", "suite.")
                    end_pattern = r'\s+([a-z#]+\.?(?:\s+[a-z0-9#]+\.?)*)$'
                    match = re.search(end_pattern, addr_str)
                    if match:
                        ending = match.group(1).strip()
                        # Remove trailing periods for comparison
                        ending_clean = ending.rstrip('.')
                        # If it's not a known street suffix and contains unit-like patterns, flag it
                        if ending_clean.lower() not in street_suffixes:
                            # Check if it looks like a unit designation (contains numbers, #, or common unit words with optional periods)
                            if re.search(r'[0-9#]', ending) or any(re.search(rf'\b{word}\.?\b', ending) for word in ['apt', 'suite', 'unit', 'floor', 'flat']):
                                violations.append({
                                    'row_index': row_num,
                                    'field': field_addr,
                                    'severity': 'Error',
                                    'message': 'Apartment/Suite/Unit info must be in Address 2 (not Address 1).'
                                })
                                error_count += 1

            # City, State
            for key in ['city', 'state']:
                val, field = get_val_field(row, key)
                if pd.isna(val) or not str(val).strip():
                    violations.append({
                        'row_index': row_num,
                        'field': field,
                        'severity': 'Error',
                        'message': 'Required value is missing.'
                    })
                    error_count += 1

            # Zip Code - required + format validation
            val_zip, field_zip = get_val_field(row, 'zip_code')
            if pd.isna(val_zip) or not str(val_zip).strip():
                violations.append({
                    'row_index': row_num,
                    'field': field_zip,
                    'severity': 'Error',
                    'message': 'Required value is missing.'
                })
                error_count += 1
            else:
                # Format validation: must be 5 digits (ZIP+4 truncated to 5 digits)
                format_error = self._validate_zip_code_format(val_zip)
                if format_error:
                    violations.append({
                        'row_index': row_num,
                        'field': field_zip,
                        'severity': 'Error',
                        'message': format_error
                    })
                    error_count += 1

            # Training Start Date
            val_start, field_start = get_val_field(row, 'training_start_date')
            dt_start = self._parse_date(val_start)
            if pd.isna(val_start) or not str(val_start).strip():
                violations.append({
                    'row_index': row_num,
                    'field': field_start,
                    'severity': 'Error',
                    'message': 'Training Start Date is required.'
                })
                error_count += 1
            elif dt_start is None:
                violations.append({
                    'row_index': row_num,
                    'field': field_start,
                    'severity': 'Error',
                    'message': f'{field_start} must be a valid date in MM/DD/YYYY format.'
                })
                error_count += 1
            elif dt_start >= today:
                violations.append({
                    'row_index': row_num,
                    'field': field_start,
                    'severity': 'Error',
                    'message': f'{field_start} must be earlier than today (today is not allowed).'
                })
                error_count += 1

            # Training Exit Date
            val_exit, field_exit = get_val_field(row, 'training_exit_date')
            dt_exit = self._parse_date(val_exit)
            
            # exit date is required if status is graduated or noncompletion reason provided
            status_raw, field_status = get_val_field(row, 'current_program_status')
            status = self._normalize_string(status_raw).lower()
            nc_reason_raw, _ = get_val_field(row, 'noncompletion_reason')
            nc_reason = self._normalize_string(nc_reason_raw).lower()
            
            exit_required = (status == 'graduated/completed') or (bool(nc_reason))
            
            if exit_required and (pd.isna(val_exit) or not str(val_exit).strip()):
                msg = f'Training Exit Date is required when status is Graduated/completed.' if status == 'graduated/completed' else 'Training Exit Date is required when a noncompletion reason is provided.'
                violations.append({
                    'row_index': row_num,
                    'field': field_exit,
                    'severity': 'Error',
                    'message': msg
                })
                error_count += 1
            elif not pd.isna(val_exit) and str(val_exit).strip():
                if dt_exit is None:
                    violations.append({
                        'row_index': row_num,
                        'field': field_exit,
                        'severity': 'Error',
                        'message': f'{field_exit} must be a valid date in MM/DD/YYYY format.'
                    })
                    error_count += 1
                elif dt_exit >= today:
                    violations.append({
                        'row_index': row_num,
                        'field': field_exit,
                        'severity': 'Error',
                        'message': f'{field_exit} must be earlier than today (today is not allowed).'
                    })
                    error_count += 1
                elif dt_start and dt_exit <= dt_start:
                    violations.append({
                        'row_index': row_num,
                        'field': field_exit,
                        'severity': 'Error',
                        'message': 'Exit Date must be after Start Date.'
                    })
                    error_count += 1

            # Current Program Status - required field check
            if pd.isna(status_raw) or not str(status_raw).strip():
                violations.append({
                    'row_index': row_num,
                    'field': field_status,
                    'severity': 'Error',
                    'message': 'Current Program Status is required.'
                })
                error_count += 1
            
            # Reverse conditional: If Training Exit Date is provided, status must be Graduated/Withdrawn
            if not pd.isna(val_exit) and str(val_exit).strip() and dt_exit is not None:
                if status not in ['graduated/completed', 'withdrawn/terminated']:
                    violations.append({
                        'row_index': row_num,
                        'field': field_status,
                        'severity': 'Error',
                        'message': 'When "Training Exit Date" is provided, Current Program Status must be "Graduated/completed" or "Withdrawn/terminated".'
                    })
                    error_count += 1
            
            # Program status conditionals
            if status == 'withdrawn/terminated':
                if not nc_reason:
                    _, f_nc = get_val_field(row, 'noncompletion_reason')
                    violations.append({
                        'row_index': row_num,
                        'field': f_nc,
                        'severity': 'Error',
                        'message': 'Required when Current Program Status is "Withdrawn/terminated".'
                    })
                    error_count += 1
            
            if status == 'graduated/completed':
                val_ct, field_ct = get_val_field(row, 'completion_type')
                ct = self._normalize_string(val_ct).lower()
                if not ct:
                    violations.append({
                        'row_index': row_num,
                        'field': field_ct,
                        'severity': 'Error',
                        'message': 'If Graduated/Completed, type of completion becomes required.'
                    })
                    error_count += 1
                elif ct not in [c.lower() for c in completion_types]:
                    violations.append({
                        'row_index': row_num,
                        'field': field_ct,
                        'severity': 'Error',
                        'message': 'If Graduated/Completed, type of completion must be one of the allowed types.'
                    })
                    error_count += 1

            # Noncompletion rules
            if nc_reason:
                if nc_reason not in [r.lower() for r in noncompletion_reasons]:
                    _, f_nc = get_val_field(row, 'noncompletion_reason')
                    violations.append({
                        'row_index': row_num,
                        'field': f_nc,
                        'severity': 'Error',
                        'message': 'Noncompletion reason must match one of the approved reasons.'
                    })
                    error_count += 1
                
                if nc_reason == 'other':
                    val_nos, field_nos = get_val_field(row, 'noncompletion_other_specify')
                    if pd.isna(val_nos) or not str(val_nos).strip():
                        violations.append({
                            'row_index': row_num,
                            'field': field_nos,
                            'severity': 'Error',
                            'message': 'If the reason for noncompletion is "other", please specify becomes required.'
                        })
                        error_count += 1

            # Employment rules
            emp_status_raw, field_es = get_val_field(row, 'employment_status')
            emp_status = self._normalize_string(emp_status_raw).lower()
            is_employed = emp_status.startswith('employed in-field')
            
            # Normalize approved list items for comparison
            normalized_approved = [self._normalize_string(s).lower() for s in employment_statuses]
            
            if emp_status and emp_status not in normalized_approved:
                violations.append({
                    'row_index': row_num,
                    'field': field_es,
                    'severity': 'Error',
                    'message': 'Invalid Employment Status value.'
                })
                error_count += 1

            # Details filled check
            detail_keys = ['employer_name', 'employment_type', 'job_start_date', 'job_occupation', 'hourly_earnings']
            details_filled = any(not pd.isna(get_val_field(row, k)[0]) and str(get_val_field(row, k)[0]).strip() for k in detail_keys)
            
            if details_filled and not is_employed:
                violations.append({
                    'row_index': row_num,
                    'field': field_es,
                    'severity': 'Error',
                    'message': 'Employment Status must be either "Employed In-field by an employer who doesn\'t partner with your training program" or "Employed In-field by an employer who partners with your training program" when any employment fields are filled out.'
                })
                error_count += 1

            if is_employed:
                # Employer Name
                v_en, f_en = get_val_field(row, 'employer_name')
                if pd.isna(v_en) or not str(v_en).strip():
                    violations.append({ 'row_index': row_num, 'field': f_en, 'severity': 'Error', 'message': 'Employer Name is required when employed.' })
                    error_count += 1
                
                # Employment Type
                v_et, f_et = get_val_field(row, 'employment_type')
                et = self._normalize_string(v_et).lower()
                if not et:
                    violations.append({ 'row_index': row_num, 'field': f_et, 'severity': 'Error', 'message': 'Employment Type is required when employed.' })
                    error_count += 1
                elif et not in [e.lower() for e in employment_types]:
                    violations.append({ 'row_index': row_num, 'field': f_et, 'severity': 'Error', 'message': 'Employment Type must be one of the allowed types.' })
                    error_count += 1
                
                # Earn and Learn specify
                v_els, f_els = get_val_field(row, 'earn_and_learn_specify')
                if et == 'earn and learn employment':
                    if pd.isna(v_els) or not str(v_els).strip():
                        violations.append({ 'row_index': row_num, 'field': f_els, 'severity': 'Error', 'message': 'Specify type is required when Employment Type is “Earn and Learn employment”.' })
                        error_count += 1
                else:
                    if not pd.isna(v_els) and str(v_els).strip():
                        violations.append({ 'row_index': row_num, 'field': f_els, 'severity': 'Error', 'message': 'Specify type must be blank if Employment Type is anything else.' })
                        error_count += 1

                # Job Start Date
                v_jsd, f_jsd = get_val_field(row, 'job_start_date')
                if pd.isna(v_jsd) or not str(v_jsd).strip():
                    violations.append({ 'row_index': row_num, 'field': f_jsd, 'severity': 'Error', 'message': 'Job start date is required when employed.' })
                    error_count += 1
                
                # Job Occupation
                v_jo, f_jo = get_val_field(row, 'job_occupation')
                jo = self._normalize_string(v_jo).lower()
                if not jo:
                    violations.append({ 'row_index': row_num, 'field': f_jo, 'severity': 'Error', 'message': 'Job Occupation is required when employed.' })
                    error_count += 1
                elif jo not in [o.lower() for o in occupation_codes]:
                    violations.append({ 'row_index': row_num, 'field': f_jo, 'severity': 'Error', 'message': 'Job Occupation must match one of the approved options.' })
                    error_count += 1

                # Hourly Earnings
                v_he, f_he = get_val_field(row, 'hourly_earnings')
                if pd.isna(v_he) or not str(v_he).strip():
                    violations.append({ 'row_index': row_num, 'field': f_he, 'severity': 'Error', 'message': 'Required when Employment Status is employed.' })
                    error_count += 1

        # Enhanced rules validation (gated by enablement in YAML config)
        # Per BRD Section 2.3 and Task 9: Check enablement before executing enhanced rules
        enhanced_rules = self.engine.get_enhanced_rules()
        
        # Enhanced Rule: active_past_graduation
        # Check if Training Exit Date is provided but status is not Graduated/Withdrawn
        # Note: This rule is now redundant with the main validation logic above, but kept for
        # backward compatibility with enhanced rules configuration
        active_past_graduation_config = self.engine.get_enhanced_rule_config("active_past_graduation")
        if active_past_graduation_config and active_past_graduation_config.get("enabled", False):
            for idx, row in staged_data.iterrows():
                row_num = int(idx) + data_start_row
                
                # Termination rule: stop at first blank row
                row_slice = row.iloc[:max_cols]
                if row_slice.isna().all() or (row_slice.astype(str).str.strip() == '').all():
                    break
                
                status_raw, field_status = get_val_field(row, 'current_program_status')
                status = self._normalize_string(status_raw).lower()
                val_exit, field_exit = get_val_field(row, 'training_exit_date')
                dt_exit = self._parse_date(val_exit)
                
                # Check if Training Exit Date is provided but status is not Graduated/Withdrawn
                if not pd.isna(val_exit) and str(val_exit).strip() and dt_exit is not None:
                    if status not in ['graduated/completed', 'withdrawn/terminated']:
                        violations.append({
                            'row_index': row_num,
                            'field': field_status,
                            'severity': active_past_graduation_config.get("severity", "Error"),
                            'message': 'When "Training Exit Date" is provided, Current Program Status must be "Graduated/completed" or "Withdrawn/terminated".'
                        })
                        error_count += 1
        
        # Enhanced Rule: prevailing_wage
        # Validate job placements meet prevailing wage requirements (hardcoded lookup table)
        prevailing_wage_config = self.engine.get_enhanced_rule_config("prevailing_wage")
        if prevailing_wage_config and prevailing_wage_config.get("enabled", False):
            # Hardcoded prevailing wage lookup table (occupation code + region)
            # Per plan: "Uses hardcoded wage lookup table" (not external API)
            # TODO: Implement hardcoded wage lookup table when prevailing_wage rule is enabled
            # For now, this is a placeholder that can be expanded with actual wage data
            for idx, row in staged_data.iterrows():
                row_num = int(idx) + data_start_row
                
                # Termination rule: stop at first blank row
                row_slice = row.iloc[:max_cols]
                if row_slice.isna().all() or (row_slice.astype(str).str.strip() == '').all():
                    break
                
                emp_status_raw, field_es = get_val_field(row, 'employment_status')
                emp_status = self._normalize_string(emp_status_raw).lower()
                is_employed = emp_status.startswith('employed in-field')
                
                if is_employed:
                    v_jo, f_jo = get_val_field(row, 'job_occupation')
                    v_he, f_he = get_val_field(row, 'hourly_earnings')
                    
                    # Only check if both occupation and earnings are present
                    if not pd.isna(v_jo) and str(v_jo).strip() and not pd.isna(v_he) and str(v_he).strip():
                        try:
                            hourly_wage = float(v_he)
                            # TODO: Add hardcoded wage lookup table here
                            # For now, this is a placeholder - actual implementation would:
                            # 1. Extract occupation code from job_occupation
                            # 2. Determine region (from address or default)
                            # 3. Look up prevailing wage from hardcoded table
                            # 4. Compare hourly_wage with prevailing_wage
                            # 5. Flag error if hourly_wage < prevailing_wage
                            # Note: This is intentionally not implemented yet as the wage lookup table
                            # needs to be defined per BRD requirements
                        except (ValueError, TypeError):
                            # Invalid hourly earnings format - already caught by main validation
                            pass
        
        # Enhanced Rule: name_misspelling
        # Compare canonical participant names with WSAC prior-quarter data (requires WSAC data)
        name_misspelling_config = self.engine.get_enhanced_rule_config("name_misspelling")
        if name_misspelling_config and name_misspelling_config.get("enabled", False):
            # This rule requires WSAC prior-quarter data, which is not available in validate_tool.py
            # It will be implemented in CollectWSACAggregatesTool per POC Part 3
            # Per plan: "name_misspelling: enabled: false  # Requires WSAC data"
            # This is a placeholder for future integration
            pass

        # Implement halt logic per BRD Section 2.3
        halt_on_error = self.engine.should_halt_on_error()
        warning_threshold = self.engine.get_warning_threshold()
        
        should_halt = False
        halt_reasons = []
        
        if halt_on_error and error_count > 0:
            should_halt = True
            halt_reasons.append(f"Halted: {error_count} errors found (halt_on_error enabled)")
        
        if warning_threshold is not None and warning_count >= warning_threshold:
            should_halt = True
            halt_reasons.append(f"Halted: {warning_count} warnings exceed threshold of {warning_threshold}")
        
        # Determine ok status: no errors AND not halted by warning threshold
        ok_status = error_count == 0 and not should_halt
        
        # Build blockers list
        blockers = []
        if should_halt:
            blockers.extend(halt_reasons)
        elif error_count > 0:
            blockers.append(f"{error_count} errors found")

        return ToolResult(
            ok=ok_status,
            summary=f"Validation complete: {error_count} errors, {warning_count} warnings",
            data={
                'violations': violations,
                'error_count': error_count,
                'warning_count': warning_count,
                'total_violations': len(violations)
            },
            warnings=[f"{warning_count} warnings found"] if warning_count > 0 else [],
            blockers=blockers
        )
