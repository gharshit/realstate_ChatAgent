

## import
from typing import List, TypedDict
from typing_extensions import Annotated
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage,HumanMessage,SystemMessage
from typing import Dict, Any
from app.config import settings
from app.chatagent.prompts import get_AGENT_CORE_PROMPT



##> ============================================================================
##> STATE DEFINITION
##> ============================================================================
class AgentChatState(TypedDict):
     """
     State for the property sales conversational agent.
     
     This state flows through all nodes in the LangGraph workflow and maintains
     the complete context of the conversation.
     """
     user_message   : str
     messages       : Annotated[List[BaseMessage], add_messages]
     conversation_id: str
     iteration_count: int


##> ============================================================================
##> STATE CREATION FOR INVOCATION
##> ============================================================================

def create_initial_state(conversation_id: str, user_message: str, is_new_conversation: bool)->Dict[str, Any]:
     """
     Create an initial state for a new invocation of the agent.
     
     Args:
          conversation_id: The unique identifier for the conversation.
          message: The user's message to the agent.
          is_new_conversation: Whether this is a new conversation or not.
          
     Returns:
          A dictionary containing the initial state of the agent.
     """
     
     
     ## get core prompt
     messages_list: List[BaseMessage] = []
     print("Fetching core agent prompt...")
     core_prompt = get_AGENT_CORE_PROMPT()
     
     if is_new_conversation:
          system_message = SystemMessage(content=core_prompt)
          messages_list.append(system_message)
     
     print("Updating messages...")
     ## This is the received user message from the user.
     messages_list.append(HumanMessage(content=user_message))
     
     return {
          "user_message"   : user_message,
          "messages"       : messages_list,
          "conversation_id": conversation_id,
          "iteration_count": 0,
     }