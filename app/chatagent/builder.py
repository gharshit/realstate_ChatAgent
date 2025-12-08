import traceback
from langgraph.graph import StateGraph, END
from app.chatagent.state import AgentChatState
from app.chatagent.nodes import chat_node
from app.chatagent.llmclient import get_llm_client
from langgraph.prebuilt import ToolNode, tools_condition
from app.chatagent.state import create_initial_state
from fastapi import Request




##> ============================================================================
##> GRAPH BUILDER
##> ============================================================================


async def create_property_sales_agent_graph(request: Request):
     """
     Build the property sales agent graph.
     
     Creates a LangGraph workflow with chat and tool nodes, configured with
     the checkpoint from app state for conversation persistence.
     
     Args:
         request: FastAPI Request object to access app.state.checkpoint
     
     Returns:
         Compiled LangGraph StateGraph instance with checkpoint configured.
     """     
     ##> Make tool node
     tool_node = ToolNode(tools=get_llm_client().get_tools())
     
     ## INFO THIS IS CORE REACT AGENT WORKFLOW FOR THE PROPERTY SALES AGENT.
     ##> Initialize workflow
     workflow = StateGraph(AgentChatState)
     
     ##> Add nodes
     workflow.add_node("chat_node", chat_node)
     workflow.add_node("tool_node", tool_node)
     
     ##> Set entry point
     workflow.set_entry_point("chat_node")
     
     ##> Add edges
     workflow.add_conditional_edges("chat_node", tools_condition, {
          "tools"   : "tool_node",
          "__end__" : END
     })
     workflow.add_edge("tool_node", "chat_node")
     
     ##> Compile workflow with checkpoint from app state
     compiled_graph = workflow.compile(checkpointer=request.app.state.checkpoint)
     
     return compiled_graph



##> ============================================================================
##> INVOCATION HELPER
##> ============================================================================


async def invoke_agent(message: str, conversation_id: str, is_new_conversation: bool, request: Request) -> dict:
     """
     Invoke the chatagent with a user message.
     
     Creates the agent graph and invokes it with the user message, using the
     conversation_id as the thread_id for checkpoint persistence.
     
     Args:
          message: User's message
          conversation_id: Conversation ID (used as thread_id for checkpoint)
          is_new_conversation: Whether the conversation is new or not
          request: FastAPI Request object to access app.state.checkpoint
     
     Returns:
          Dictionary with 'response' (agent's message) and 'conversation_id'
     """
     print(f"Invoking agent with message: {message}, conversation_id: {conversation_id}, is_new_conversation: {is_new_conversation}")
     
     # Create graph with checkpoint from app state
     graph = await create_property_sales_agent_graph(request)
     config = {"configurable": {"thread_id": conversation_id}}
          
     # Prepare initial state
     input_state = create_initial_state(
          conversation_id     = conversation_id,
          user_message        = message,
          is_new_conversation = is_new_conversation
     )
     
     print(f"Invoking agent with input state having new conversation: {is_new_conversation}")
     
     # Invoke agent
     try:
          result = await graph.ainvoke(input_state, config)
     except Exception:
          traceback.print_exc()
          return {
               "response": "I encountered a system error. Please try again.",
               "conversation_id": conversation_id
          }
   
     # Extract response from last message
     messages_list = result.get("messages", [])
     response_message = (
          messages_list[-1].content 
          if messages_list and len(messages_list) > 0 
          else "I apologize, but I encountered an issue. Could you please rephrase your message?"
     )
     print(f"Response message: {response_message}")
     
     return {
          "response": response_message,
          "conversation_id": conversation_id
     }