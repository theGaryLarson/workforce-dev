"""CFA external system mappings for future export tools per PRD-TRD Section 5.4."""

# WSAC Export Mappings: canonical field -> WSAC camelCase field mappings
# Maps canonical snake_case fields to WSAC camelCase headers per wsac-participants.csv format
WSAC_EXPORT_MAPPINGS = {
    # Basic participant information
    "participant_id": "id",
    "first_name": "firstName",
    "last_name": "lastName",
    "middle_name": "middleName",
    "date_of_birth": "birthDate",
    
    # Address information
    "address_1": "addressLine1",
    "address_2": "addressLine2",
    "city": "addressCity",
    "state": "addressState",
    "zip_code": "addressZip",
    
    # Contact information
    "email": "email",
    "phone": "phoneNumber",
    
    # Training information (mapped to trainingProvider1/trainingProgram1)
    # Note: trainingProvider1 and trainingProgram1 may need to be derived from
    # partner data or set to default values (e.g., "Computing for All" for provider)
    "tech_role/pathway_targeted": "trainingProgram1",
    "training_start_date_(mm/dd/yyyy)": "trainingStartDate1",
    "training_exit_date_(mm/dd/yyyy)": "actualTrainingEndDate1",
    # Note: current_program_status doesn't have a direct WSAC mapping - program status
    # is inferred from training dates and completion reasons in WSAC format
    "if_a_noncompletion_(withdrawal/termination),_provide_reason": "reasonForProgramNoncompletion1",
    "if_the_reason_for_noncompletion_is_\"other\",_please_specify": "otherProgramNoncompletionDetails1",
    
    # Employment information
    "employment_status": "employmentStatus",
    "if_employed,_employer_name": "employer",
    "if_employed,_employment_type": "employmentType",
    "if_employed,_job_start_date_(mm/dd/yyyy)": "employmentStartDate",
    "if_employed,_job_occupation_(naics_code)": "jobTitle",
    "if_employed,_hourly_earnings_(ex._$25.00)": "hourlyWage",
    
    # Note: WSAC fields not directly mapped (may need defaults or derivation in export tool):
    # - trainingProvider1: derived from --partner CLI argument (e.g., "demo" -> "Demo" or partner name)
    # - expectedTrainingEndDate1: may need to be calculated from training duration or left blank
    # - wasProgramEnrollmentInterrupted1: boolean field, may need to be derived from partner data
    # - trainingProvider2, trainingProgram2, etc.: for multiple training programs (not in current canonical format)
    # - current_program_status: no direct WSAC mapping; program status inferred from dates/completion reasons
    #
    # Fields in canonical but not in WSAC format (partner-specific data):
    # - gender, ethnicity, race, disability, veteran, education_level
    # - other_priority_populations_list, wraparound_services, etc.
}

# Dynamics Import Mappings: canonical field -> Dynamics field mappings
DYNAMICS_IMPORT_MAPPINGS = {
    "first_name": "FirstName",
    "last_name": "LastName",
    "date_of_birth": "BirthDate",
    "address_1": "AddressLine1",
    "address_2": "AddressLine2",
    "city": "City",
    "state": "State",
    "zip_code": "PostalCode",
    "training_start_date": "TrainingStartDate",
    "training_exit_date": "TrainingExitDate",
    "current_program_status": "ProgramStatus",
    "completion_type": "CompletionType",
    "noncompletion_reason": "NoncompletionReason",
    "employment_status": "EmploymentStatus",
    "employer_name": "EmployerName",
    "employment_type": "EmploymentType",
    "job_start_date": "JobStartDate",
    "job_occupation": "JobOccupation",
    "hourly_earnings": "HourlyEarnings"
}

# WSAC Transformations: date formats, status mappings
WSAC_TRANSFORMATIONS = {
    "date_format": "%Y-%m-%d",  # ISO format
    "status_mappings": {
        "graduated/completed": "Completed",
        "withdrawn/terminated": "Withdrawn",
        "active": "Active"
    }
}

# Dynamics Transformations: date formats, lookup values
DYNAMICS_TRANSFORMATIONS = {
    "date_format": "%m/%d/%Y",  # MM/DD/YYYY format
    "lookup_values": {
        "program_status": {
            "graduated/completed": "Graduated",
            "withdrawn/terminated": "Withdrawn",
            "active": "Active"
        }
    }
}

# Export all mappings as a single MAPPINGS dict
MAPPINGS = {
    "wsac_export": WSAC_EXPORT_MAPPINGS,
    "dynamics_import": DYNAMICS_IMPORT_MAPPINGS,
    "wsac_transformations": WSAC_TRANSFORMATIONS,
    "dynamics_transformations": DYNAMICS_TRANSFORMATIONS
}
