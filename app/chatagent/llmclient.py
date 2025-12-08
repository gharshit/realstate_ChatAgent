"""
LLM Client for the Property Sales Conversational Agent.

This module provides a class-based LLM client following the same pattern
as the database connection for consistency and better initialization control.
"""

## Imports
import os
from typing import Optional, List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from langchain_core.tools import BaseTool
from app.chatagent.tools import secure_sql_tools


##> ============================================================================
##> LLM CLIENT CLASS
##> ============================================================================

class LLMClient:
     """
     LLM client for the property sales agent.
     
     Manages OpenAI LLM initialization, tool binding, and tool node creation.
     Follows the same pattern as DatabaseConnection for consistency.
     """
     
     def __init__(
          self,
          model: Optional[str] = None,
          temperature: float = 0.7,
          api_key: Optional[str] = None
     ):
          """
          Initialize LLM client.
          
          Args:
               model: OpenAI model name (defaults to gpt-4o-mini).
               temperature: Temperature for LLM responses (default 0.7).
               api_key: OpenAI API key (defaults to OPENAI_API_KEY env var).
          """
          # Load environment variables
          load_dotenv()
          
          ##> Get API key
          self.api_key = api_key or os.getenv("OPENAI_API_KEY")
          if not self.api_key:
               raise ValueError("OPENAI_API_KEY environment variable is required")
          
          # Get model name
          self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
          
          # Validate model name
          valid_models = ["gpt-4o-mini", "gpt-4o", "gpt-4.1","text-embedding-3-small","gpt-5-mini","gpt-4.1-mini"]
          if self.model not in valid_models:
               print(f"⚠️  Warning: '{self.model}' may not be a valid OpenAI model. Valid models: {valid_models}")
          
          self.temperature = temperature
          
          # Initialize LLM
          self.llm = ChatOpenAI(
               model       =self.model,
               temperature =self.temperature,
               api_key     =self.api_key
          )
          
          # Initialize tools
          self.tools = secure_sql_tools
          
          # Bind tools to LLM
          self.llm_with_tools = self.llm.bind_tools(self.tools)
          
     
     def get_llm(self) -> ChatOpenAI:
          """Get the base LLM instance."""
          return self.llm
     
     def get_llm_with_tools(self):
          """Get LLM instance with tools bound."""
          return self.llm_with_tools
     
     
     def get_tools(self) -> List[BaseTool]:
          """Get list of available tools."""
          return self.tools


##> ============================================================================
##> GLOBAL INSTANCE
##> ============================================================================

# Global LLM client instance (will be initialized in main.py)
llm_client: Optional[LLMClient] = None


##> ============================================================================
##> INITIALIZATION FUNCTIONS
##> ============================================================================

def init_llm(
    model: Optional[str] = None,
    temperature: float = 0.7,
    api_key: Optional[str] = None
) -> LLMClient:
     """
     Initialize the global LLM client.
     Should be called once at application startup.
     
     Args:
          model: OpenAI model name (defaults to env var or gpt-4o-mini).
          temperature: Temperature for LLM responses (default 0.7).
          api_key: OpenAI API key (defaults to OPENAI_API_KEY env var).
     
     Returns:
          LLMClient instance.
     """
     global llm_client
     
     llm_client = LLMClient(model=model, temperature=temperature, api_key=api_key)
     
     return llm_client


def get_llm_client() -> LLMClient:
     """
     Get the global LLM client instance.
     
     Returns:
          LLMClient instance.
     
     Raises:
          RuntimeError: If LLM client not initialized.
     """
     if llm_client is None:
          raise RuntimeError("LLM client not initialized. Call init_llm() first. This should have initialized in lifespan context manager.")
     return llm_client


def cleanup_llm() -> None:
     """Cleanup LLM client."""
     global llm_client
     llm_client = None