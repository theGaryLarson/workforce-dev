"""Unit tests for core/tools.py ToolResult dataclass per PRD-TRD Section 10.1."""

import pandas as pd
import pytest

from agentic_systems.core.tools import ToolResult


class TestToolResult:
    """Test suite for ToolResult dataclass."""

    def test_tool_result_required_fields(self):
        """Test that ToolResult has all required fields."""
        result = ToolResult(
            ok=True,
            summary="Test summary",
            data={},
            warnings=[],
            blockers=[]
        )
        
        assert hasattr(result, 'ok')
        assert hasattr(result, 'summary')
        assert hasattr(result, 'data')
        assert hasattr(result, 'warnings')
        assert hasattr(result, 'blockers')
        
        assert result.ok is True
        assert result.summary == "Test summary"
        assert isinstance(result.data, dict)
        assert isinstance(result.warnings, list)
        assert isinstance(result.blockers, list)

    def test_tool_result_with_data(self):
        """Test ToolResult with various data types."""
        df = pd.DataFrame({"col1": [1, 2, 3]})
        result = ToolResult(
            ok=True,
            summary="Test",
            data={"dataframe": df, "count": 3, "message": "Success"},
            warnings=[],
            blockers=[]
        )
        
        assert "dataframe" in result.data
        assert isinstance(result.data["dataframe"], pd.DataFrame)
        assert result.data["count"] == 3
        assert result.data["message"] == "Success"

    def test_tool_result_with_warnings(self):
        """Test ToolResult with warnings."""
        result = ToolResult(
            ok=True,
            summary="Test with warnings",
            data={},
            warnings=["Warning 1", "Warning 2"],
            blockers=[]
        )
        
        assert len(result.warnings) == 2
        assert "Warning 1" in result.warnings
        assert "Warning 2" in result.warnings

    def test_tool_result_with_blockers(self):
        """Test ToolResult with blockers."""
        result = ToolResult(
            ok=False,
            summary="Test with blockers",
            data={},
            warnings=[],
            blockers=["Error 1", "Error 2"]
        )
        
        assert result.ok is False
        assert len(result.blockers) == 2
        assert "Error 1" in result.blockers
        assert "Error 2" in result.blockers

    def test_tool_result_empty_warnings_blockers(self):
        """Test ToolResult with empty warnings and blockers."""
        result = ToolResult(
            ok=True,
            summary="Test",
            data={},
            warnings=[],
            blockers=[]
        )
        
        assert len(result.warnings) == 0
        assert len(result.blockers) == 0

    def test_tool_result_model_used_tracking(self):
        """Test ToolResult with model_used for LLM tracking."""
        result = ToolResult(
            ok=True,
            summary="LLM tool executed",
            data={"model_used": "gpt-4o-mini", "tokens": 100},
            warnings=[],
            blockers=[]
        )
        
        assert result.data["model_used"] == "gpt-4o-mini"
        assert result.data["tokens"] == 100



