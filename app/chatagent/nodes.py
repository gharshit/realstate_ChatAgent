from app.chatagent.llmclient import get_llm_client
from app.chatagent.state import AgentChatState
from langchain_core.messages import BaseMessage, SystemMessage
from typing import Dict, Any
from app.config import settings

##> ============================================================================
##> CHAT NODE
##> ============================================================================

async def chat_node(state: AgentChatState) -> Dict[str, Any]:
     """Chat node for the property sales conversational agent.
     
     This node:
     1. Receives user messages or tool results
     2. Analyzes conversation context and state
     3. Decides whether to call tools OR generate response
     4. Always produces the final response to the user
     
     Flow:
         - If needs data → calls tools (routes to tool_node)
         - If has enough info → generates response (routes to END)
     """

     client = get_llm_client()
     
     ## Increment iteration counter
     current_iteration = state.get("iteration_count", 0) + 1
     ## Check iteration limit
     force_response = current_iteration >= settings.max_iterations
     
     ## Get all messages
     messages = list(state["messages"])
     
     
     ## Get LLM response (with or without tools)
     if force_response:
          response = await client.get_llm().ainvoke(messages)
     else:
          response = await client.get_llm_with_tools().ainvoke(messages)
     
     # Update state
     updates = {
          "messages"       : [response],
          "iteration_count": current_iteration,
     }
     
     return updates
