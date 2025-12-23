"""LangChainIntakeAgent per PRD-TRD Section 6.4.

LLM-based orchestration agent demonstrating BaseAgent contract with AI-powered planning and summarization.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

try:
    # LangChain 1.2.0+ uses create_agent and langchain.messages
    from langchain.agents import create_agent
    from langchain.messages import HumanMessage, SystemMessage
except ImportError:
    # LangChain not installed - will raise error when agent is used
    create_agent = None
    HumanMessage = None
    SystemMessage = None

from agentic_systems.agents.base_agent import BaseAgent
from agentic_systems.core.canonical.canonicalize_tool import CanonicalizeStagedDataTool
from agentic_systems.core.ingestion.ingest_tool import IngestPartnerFileTool
from agentic_systems.core.validation.validate_tool import ValidateStagedDataTool
from .adapter import LangChainAdapter


class LangChainIntakeAgent(BaseAgent):
    """LLM-based intake agent extending BaseAgent contract per PRD-TRD Section 6.4.
    
    Uses LangChain internally for LLM orchestration. Implements plan(), execute(), and
    summarize() using LLM while maintaining BaseAgent contract compliance.
    """
    
    def __init__(self, run_id: str = None, evidence_dir: Path = None, model_name: str = None):
        """Initialize LangChainIntakeAgent.
        
        Args:
            run_id: Run identifier for evidence bundle
            evidence_dir: Directory for evidence bundle (where tool_calls.jsonl is written)
            model_name: Optional LLM model name override
        """
        if create_agent is None:
            raise ImportError(
                "LangChain dependencies not installed. "
                "Install with: pip install langchain langchain-openai openai"
            )
        
        self.run_id = run_id
        self.evidence_dir = evidence_dir
        self.tool_calls_log = []
        self.model_name = model_name
        
        # Initialize tools per PRD-TRD Section 5.4 (same as Part 1)
        self.ingest_tool = IngestPartnerFileTool()
        self.validate_tool = ValidateStagedDataTool()
        self.canonicalize_tool = CanonicalizeStagedDataTool()
        
        # Tool registry for execute()
        self.tools = {
            'IngestPartnerFileTool': self.ingest_tool,
            'ValidateStagedDataTool': self.validate_tool,
            'CanonicalizeStagedDataTool': self.canonicalize_tool,
        }
        
        # Initialize adapter
        self.adapter = LangChainAdapter(self.tools)
        self.llm = self.adapter.get_llm(model_name)
    
    def _extract_preflight_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract file metadata without full ingestion per PRD-TRD Section 6.4.
        
        Reads file size, extension, and header row (column names) without loading
        all data. This metadata is sent to LLM for planning (no raw data per BRD Section 2.3).
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file metadata (name, size, extension, column_names)
        """
        path = Path(file_path)
        
        metadata = {
            'file_name': path.name,
            'file_size': path.stat().st_size,
            'extension': path.suffix.lower(),
        }
        
        # Read header row only (no row data per BRD Section 2.3)
        try:
            import pandas as pd
            
            if metadata['extension'] == '.csv':
                # Read first row only to get column names
                df_header = pd.read_csv(file_path, nrows=0)
                metadata['column_names'] = list(df_header.columns)
            elif metadata['extension'] in ['.xlsx', '.xls']:
                # Read first row only
                df_header = pd.read_excel(file_path, nrows=0)
                metadata['column_names'] = list(df_header.columns)
            else:
                metadata['column_names'] = []
        except Exception as e:
            metadata['column_names'] = []
            metadata['header_error'] = str(e)
        
        return metadata
    
    def plan(self, inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate dynamic execution plan using LLM per PRD-TRD Section 6.4.
        
        Uses LLM to analyze preflight metadata and generate structured execution steps.
        LLM receives preflight metadata only (file name, size, extension, column names)
        - no row data per BRD Section 2.3.
        
        Args:
            inputs: Dictionary containing file_path and run_id
            
        Returns:
            List of step dictionaries, each with 'tool' and 'args' keys
        """
        file_path = inputs.get('file_path')
        
        # Extract preflight metadata (no raw data per BRD Section 2.3)
        preflight = self._extract_preflight_metadata(file_path)
        
        # Build prompt with tool descriptions and preflight metadata
        tool_descriptions = [
            "IngestPartnerFileTool: Parses CSV/Excel files, normalizes column names, computes file hash",
            "ValidateStagedDataTool: Validates required fields, checks business rules (active past graduation, zip codes)",
            "CanonicalizeStagedDataTool: Maps data to canonical format and generates participant IDs"
        ]
        
        prompt = f"""You are an ETL orchestration agent. Analyze the file metadata and generate an execution plan.

File Metadata (preflight only - no row data):
- File name: {preflight['file_name']}
- File size: {preflight['file_size']} bytes
- Extension: {preflight['extension']}
- Column names: {', '.join(preflight['column_names'][:20])}{'...' if len(preflight['column_names']) > 20 else ''}

Available Tools:
{chr(10).join(f'- {desc}' for desc in tool_descriptions)}

Generate a JSON array of execution steps. Each step should have:
- "tool": tool name (one of: IngestPartnerFileTool, ValidateStagedDataTool, CanonicalizeStagedDataTool)
- "args": dictionary of arguments (IngestPartnerFileTool needs "file_path", others receive data from previous steps)

Example format:
[
  {{"tool": "IngestPartnerFileTool", "args": {{"file_path": "{file_path}"}}}},
  {{"tool": "ValidateStagedDataTool", "args": {{}}}},
  {{"tool": "CanonicalizeStagedDataTool", "args": {{}}}}
]

Return ONLY the JSON array, no other text."""

        try:
            # Call LLM to generate plan
            messages = [
                SystemMessage(content="You are a helpful ETL orchestration assistant. Return only valid JSON."),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            
            # Extract JSON from response
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Try to extract JSON array from response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                plan_steps = json.loads(json_match.group())
            else:
                # Fallback: try parsing entire response as JSON
                plan_steps = json.loads(response_text)
            
            # Validate and normalize plan steps
            validated_steps = []
            for step in plan_steps:
                if isinstance(step, dict) and 'tool' in step:
                    step_args = step.get('args', {}).copy()
                    # Ensure file_path is preserved for IngestPartnerFileTool
                    if step['tool'] == 'IngestPartnerFileTool':
                        step_args['file_path'] = file_path
                    validated_steps.append({
                        'tool': step['tool'],
                        'args': step_args
                    })
            
            # Ensure we have the basic three steps
            if not validated_steps:
                # Fallback to default plan
                validated_steps = [
                    {'tool': 'IngestPartnerFileTool', 'args': {'file_path': file_path}},
                    {'tool': 'ValidateStagedDataTool', 'args': {}},
                    {'tool': 'CanonicalizeStagedDataTool', 'args': {}}
                ]
            
            return validated_steps
            
        except Exception as e:
            # Fallback to default plan on error
            return [
                {'tool': 'IngestPartnerFileTool', 'args': {'file_path': file_path}},
                {'tool': 'ValidateStagedDataTool', 'args': {}},
                {'tool': 'CanonicalizeStagedDataTool', 'args': {}}
            ]
    
    def _emit(self, event_type: str, message: str, data: Dict[str, Any]) -> None:
        """Emit trace event to tool_calls.jsonl per PRD-TRD Section 7.4."""
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "run_id": self.run_id,
            "message": message,
            "data": data
        }
        
        self.tool_calls_log.append(event)
        
        if self.evidence_dir:
            tool_calls_path = self.evidence_dir / "tool_calls.jsonl"
            with open(tool_calls_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event) + '\n')
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate tools using LangChain agent per PRD-TRD Section 6.4.
        
        Uses LangChain to dynamically select and execute tools. LLM receives tool
        summaries (metadata) only - no raw data per BRD Section 2.3.
        
        Args:
            inputs: Dictionary containing file_path and run_id
            
        Returns:
            Dictionary with step outcomes and canonical data
        """
        # For POC, we'll use a simplified execution that follows the plan
        # but uses LangChain tools. In full implementation, the agent would
        # handle dynamic tool selection.
        
        plan_steps = self.plan(inputs)
        results = {}
        staged_dataframe = None
        
        # Get LangChain tools
        langchain_tools = self.adapter.get_langchain_tools()
        
        # Create agent using LangChain 1.2.0+ create_agent pattern
        # For POC, we execute plan steps sequentially
        # In full implementation, the agent would handle dynamic tool selection
        langchain_agent = None
        try:
            langchain_agent = create_agent(
                model=self.llm,
                tools=langchain_tools,
                system_prompt="You are an ETL orchestration agent. Use the available tools to process the file."
            )
        except Exception:
            # Fallback to sequential execution if agent creation fails
            langchain_agent = None
        
        # Execute plan steps sequentially (simplified for POC)
        # In full implementation, the agent would handle this dynamically
        for step in plan_steps:
            tool_name = step['tool']
            tool_args = step['args'].copy()
            
            self._emit("STEP_START", f"Executing {tool_name}", {
                "tool": tool_name,
                "args": tool_args
            })
            
            # Get BaseAgent tool (not LangChain wrapper) for actual execution
            tool = self.tools[tool_name]
            
            # Execute tool with proper data flow
            if tool_name == 'ValidateStagedDataTool' and staged_dataframe is not None:
                result = tool(staged_dataframe)
            elif tool_name == 'CanonicalizeStagedDataTool' and staged_dataframe is not None:
                result = tool(staged_dataframe)
            else:
                result = tool(**tool_args)
            
            # Store dataframe for next step
            if tool_name == 'IngestPartnerFileTool' and result.ok:
                staged_dataframe = result.data.get('dataframe')
            elif tool_name == 'ValidateStagedDataTool' and result.ok:
                staged_dataframe = staged_dataframe  # Pass through
            elif tool_name == 'CanonicalizeStagedDataTool' and result.ok:
                staged_dataframe = result.data.get('canonical_dataframe')
            
            # Emit STEP_END with sanitized metadata
            sanitized_data = {
                "tool": tool_name,
                "ok": result.ok,
                "summary": result.summary
            }
            
            if 'row_count' in result.data:
                sanitized_data['row_count'] = result.data['row_count']
            if 'file_hash' in result.data:
                sanitized_data['file_hash'] = result.data['file_hash']
            if 'error_count' in result.data:
                sanitized_data['error_count'] = result.data['error_count']
            if 'warning_count' in result.data:
                sanitized_data['warning_count'] = result.data['warning_count']
            if 'record_count' in result.data:
                sanitized_data['record_count'] = result.data['record_count']
            
            self._emit("STEP_END", f"Completed {tool_name}", sanitized_data)
            
            results[tool_name] = result
            
            if not result.ok or result.blockers:
                break
        
        return results
    
    def summarize(self, run_results: Dict[str, Any]) -> str:
        """Generate contextual summary using LLM per PRD-TRD Section 5.1.
        
        LLM receives metadata only (error counts, types, severity breakdowns) per
        BRD Section 2.3. No raw participant data, no PII, no field values.
        
        Args:
            run_results: Dictionary of tool execution results from execute()
            
        Returns:
            Human-readable summary string
        """
        # Extract metadata only (no raw data per BRD Section 2.3)
        metadata = {}
        
        ingest_result = run_results.get('IngestPartnerFileTool')
        if ingest_result:
            metadata['ingest'] = {
                'ok': ingest_result.ok,
                'summary': ingest_result.summary,
                'row_count': ingest_result.data.get('row_count', 0),
                'file_hash': ingest_result.data.get('file_hash', '')[:16] + '...' if ingest_result.data.get('file_hash') else ''
            }
        
        validate_result = run_results.get('ValidateStagedDataTool')
        if validate_result:
            violations = validate_result.data.get('violations', [])
            error_types = {}
            warning_types = {}
            
            for v in violations:
                field = v.get('field', 'unknown')
                severity = v.get('severity', 'Warning')
                if severity == 'Error':
                    error_types[field] = error_types.get(field, 0) + 1
                else:
                    warning_types[field] = warning_types.get(field, 0) + 1
            
            metadata['validation'] = {
                'ok': validate_result.ok,
                'error_count': validate_result.data.get('error_count', 0),
                'warning_count': validate_result.data.get('warning_count', 0),
                'error_types': error_types,
                'warning_types': warning_types,
                'blockers': validate_result.blockers
            }
        
        canonicalize_result = run_results.get('CanonicalizeStagedDataTool')
        if canonicalize_result:
            metadata['canonicalization'] = {
                'ok': canonicalize_result.ok,
                'record_count': canonicalize_result.data.get('record_count', 0),
                'summary': canonicalize_result.summary
            }
        
        # Build prompt with metadata only
        prompt = f"""Generate a staff-facing summary of the ETL pipeline execution.

Execution Metadata (no raw data):
{json.dumps(metadata, indent=2)}

Provide a clear, contextual summary that:
1. Explains what happened during processing
2. Highlights any validation errors and their implications (without exposing raw data)
3. Provides actionable next steps if blockers exist
4. References specific validation error types and their business impact

Return only the summary text, no JSON or formatting."""

        try:
            messages = [
                SystemMessage(content="You are a helpful assistant that generates clear, professional summaries."),
                HumanMessage(content=prompt)
            ]
            response = self.llm.invoke(messages)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            # Fallback to simple summary
            return self._generate_fallback_summary(run_results)
    
    def _generate_fallback_summary(self, run_results: Dict[str, Any]) -> str:
        """Generate simple fallback summary if LLM fails."""
        ingest_result = run_results.get('IngestPartnerFileTool')
        validate_result = run_results.get('ValidateStagedDataTool')
        canonicalize_result = run_results.get('CanonicalizeStagedDataTool')
        
        summary_parts = []
        
        if ingest_result:
            summary_parts.append(f"File processed: {ingest_result.summary}")
        
        if validate_result:
            error_count = validate_result.data.get('error_count', 0)
            warning_count = validate_result.data.get('warning_count', 0)
            summary_parts.append(f"Validation: {error_count} errors, {warning_count} warnings")
            if validate_result.blockers:
                summary_parts.append(f"Blockers: {', '.join(validate_result.blockers)}")
        
        if canonicalize_result:
            record_count = canonicalize_result.data.get('record_count', 0)
            summary_parts.append(f"Canonicalized: {record_count} records")
        
        return "\n".join(summary_parts) if summary_parts else "No results to summarize"

