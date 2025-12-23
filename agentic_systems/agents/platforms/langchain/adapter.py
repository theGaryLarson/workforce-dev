"""LangChain platform adapter per PRD-TRD Section 6.4.

Converts BaseAgent tools to LangChain tool format for LLM orchestration.
"""

import os
from typing import Any, Dict, List

try:
    # LangChain 1.2.0+ uses langchain.tools for @tool decorator
    from langchain.tools import tool
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
except ImportError:
    # LangChain not installed - will raise error when adapter is used
    tool = None
    ChatOpenAI = None
    ChatAnthropic = None

from ....core.tools import Tool, ToolResult


class LangChainAdapter:
    """Adapter to convert BaseAgent tools to LangChain format per PRD-TRD Section 6.4.
    
    Wraps Part 1 deterministic tools for LLM orchestration. LLM receives tool summaries
    (metadata) only - no raw data per BRD Section 2.3.
    """
    
    def __init__(self, tools: Dict[str, Tool]):
        """Initialize adapter with BaseAgent tools.
        
        Args:
            tools: Dictionary mapping tool names to Tool instances
        """
        if tool is None:
            raise ImportError(
                "LangChain dependencies not installed. "
                "Install with: pip install langchain langchain-openai openai"
            )
        self.tools = tools
        self.langchain_tools = {}
    
    def _baseagent_tool_to_langchain(self, name: str, tool_impl: Tool) -> Any:
        """Convert BaseAgent tool to LangChain tool format per PRD-TRD Section 6.4.
        
        Args:
            name: Tool name
            tool_impl: BaseAgent Tool instance
            
        Returns:
            LangChain tool wrapper
        """
        if tool is None:
            raise ImportError("LangChain not installed")
        
        # Generate description from tool name and summary
        description = f"{name}: {tool_impl.name if hasattr(tool_impl, 'name') else name}"
        
        # LangChain 1.2.0+ @tool decorator doesn't accept 'name' parameter
        # Tool name is derived from function name, so we set it after decoration
        @tool(description=description)
        def tool_wrapper(**kwargs) -> str:
            """LangChain wrapper for BaseAgent tool.
            
            Calls Part 1 deterministic tool (same tools, no changes needed).
            Tool returns ToolResult with in-memory data (DataFrame) for tool chaining.
            LLM receives summary only (metadata) - no raw data per BRD Section 2.3.
            """
            # Calls Part 1 deterministic tool - same tools, no changes needed
            result = tool_impl(**kwargs)  # Per PRD-TRD Section 5.4 Tool protocol
            
            if result.ok:
                # LLM receives summary only (metadata) - no raw data per BRD Section 2.3
                # This ensures "redacted" PII handling when LLM processes tool results
                return result.summary
            else:
                return f"Error: {result.summary}. Blockers: {', '.join(result.blockers) if result.blockers else 'None'}"
        
        # Set function name to match tool name for LangChain (tool name comes from function name)
        tool_wrapper.__name__ = name
        return tool_wrapper
    
    def get_langchain_tools(self) -> List[Any]:
        """Convert all BaseAgent tools to LangChain tools.
        
        Returns:
            List of LangChain tool instances
        """
        if not self.langchain_tools:
            for name, tool_impl in self.tools.items():
                self.langchain_tools[name] = self._baseagent_tool_to_langchain(name, tool_impl)
        
        return list(self.langchain_tools.values())
    
    def get_llm(self, model_name: str = None) -> Any:
        """Get LLM instance based on environment variables.
        
        Checks for OPENAI_API_KEY or ANTHROPIC_API_KEY and returns appropriate LLM.
        
        Args:
            model_name: Optional model name override (e.g., 'gpt-4', 'claude-3-opus-20240229')
            
        Returns:
            LangChain LLM instance (ChatOpenAI or ChatAnthropic)
            
        Raises:
            ValueError: If no API key is found or unsupported provider
        """
        if ChatOpenAI is None or ChatAnthropic is None:
            raise ImportError(
                "LangChain LLM dependencies not installed. "
                "Install with: pip install langchain-openai openai "
                "OR pip install langchain-anthropic anthropic"
            )
        
        # Check for OpenAI API key
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            model = model_name or os.getenv("OPENAI_MODEL", "gpt-4")
            return ChatOpenAI(model=model, temperature=0)
        
        # Check for Anthropic API key
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            model = model_name or os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
            return ChatAnthropic(model=model, temperature=0)
        
        raise ValueError(
            "No LLM API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable."
        )

