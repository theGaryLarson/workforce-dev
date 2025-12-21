"""Pytest configuration and shared fixtures."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def sample_csv_file():
    """Create a temporary CSV file for testing."""
    content = """First Name,Last Name,Date of Birth (MM/DD/YYYY),Zip Code,State
John,Doe,01/15/1990,98101,WA
Jane,Smith,02/20/1985,98006,WA
Bob,Johnson,03/25/1995,60601,IL"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)
    
    yield str(temp_path)
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'first_name': ['John', 'Jane', 'Bob'],
        'last_name': ['Doe', 'Smith', 'Johnson'],
        'date_of_birth': ['01/15/1990', '02/20/1985', '03/25/1995'],
        'zip_code': ['98101', '98006', '60601'],
        'state': ['WA', 'WA', 'IL']
    })


@pytest.fixture
def sample_dataframe_with_errors():
    """Create a sample DataFrame with validation errors."""
    return pd.DataFrame({
        'first_name': ['John', '', 'Bob'],  # Missing first_name in row 1
        'last_name': ['Doe', 'Smith', ''],  # Missing last_name in row 2
        'date_of_birth': ['01/15/1990', '02/20/1985', ''],  # Missing DOB in row 2
        'zip_code': ['98101.0', '98006', 'invalid'],  # Invalid zip codes
        'state': ['WA', 'WA', 'IL'],
        'current_program_status': ['Currently active in program', 'Graduated/completed', 'Currently active in program'],
        'training_exit_date____': ['12/31/2024', '12/31/2023', '12/31/2022']  # Active past graduation
    })


