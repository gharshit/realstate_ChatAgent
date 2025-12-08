import os, asyncio, traceback
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from langgraph.graph import StateGraph, END
from app.chatagent.state import AgentChatState
from app.chatagent.nodes import chat_node
from app.chatagent.llmclient import get_llm_client
from langgraph.prebuilt import ToolNode, tools_condition
from app.chatagent.state import create_initial_state
from app.config import settings




try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    POSTGRES_AVAILABLE = True
except ImportError:
    from langgraph.checkpoint.memory import MemorySaver
    POSTGRES_AVAILABLE = False

saver = None
_saver_context = None
_checkpoint_lock = asyncio.Lock()


def clean_conn_string_for_psycopg(database_url: str) -> str:
    """
    Clean PostgreSQL connection string for psycopg3 compatibility.
    
    Removes unsupported query parameters that psycopg3 doesn't recognize.
    psycopg3 uses 'sslmode' instead of 'ssl', and doesn't support some other parameters.
    For Neon database, ensures proper SSL configuration.
    
    Args:
        database_url: PostgreSQL connection URL
        
    Returns:
        str: Cleaned connection string compatible with psycopg3
    """
    if not database_url.startswith("postgresql://"):
        return database_url
    
    # Parse URL to remove unsupported query parameters
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)
    
    # Remove ALL SSL-related parameters that psycopg3 doesn't support
    # psycopg3 only supports 'sslmode', not 'ssl', 'sslcert', 'sslkey', 'sslrootcert', 'channel_binding', etc.
    # Neon URLs often have 'ssl=require&channel_binding=require' which must be removed
    unsupported_ssl_params = ['ssl', 'sslcert', 'sslkey', 'sslrootcert', 'sslcrl', 'channel_binding']
    removed_params = []
    for param in unsupported_ssl_params:
        if param in query_params:
            removed_params.append(f"{param}={query_params[param][0]}")
            del query_params[param]
    
    if removed_params:
        print(f"Removed unsupported SSL parameters: {', '.join(removed_params)}")
    
    # Ensure sslmode is set for Neon database (requires SSL)
    # Use 'require' for Neon to ensure SSL is used
    if 'sslmode' not in query_params:
        query_params['sslmode'] = ['require']
    else:
        # Get current sslmode value
        current_sslmode = query_params.get('sslmode', [''])[0].lower()
        # If sslmode is empty, 'disable', or 'allow', change to 'require' for Neon
        if current_sslmode in ['', 'disable', 'allow']:
            query_params['sslmode'] = ['require']
        # Keep 'prefer', 'require', 'verify-ca', 'verify-full' as-is
    
    # Add connection timeout to prevent hanging connections
    if 'connect_timeout' not in query_params:
        query_params['connect_timeout'] = ['10']
    
    # Reconstruct URL with cleaned parameters
    new_query = urlencode(query_params, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    clean_url = urlunparse(new_parsed)
    
    return clean_url


async def get_checkpoint():
    """
    Get the checkpointer instance. For AsyncPostgresSaver, properly enters the async context.
    
    Returns:
        Checkpointer instance (AsyncPostgresSaver or MemorySaver)
    """
    global saver, _saver_context

    async with _checkpoint_lock:
        if saver is not None:
            return saver

        if POSTGRES_AVAILABLE:
            try:
                # Clean connection string for psycopg3 compatibility
                # Remove unsupported SSL parameters (ssl=require, channel_binding=require) 
                # and ensure sslmode=require for Neon
                original_url = settings.database_url
                clean_url = clean_conn_string_for_psycopg(original_url)
               
                
                # AsyncPostgresSaver.from_conn_string() returns an async context manager
                # We need to enter it to get the actual checkpointer instance
                _saver_context = AsyncPostgresSaver.from_conn_string(clean_url)
                saver = await _saver_context.__aenter__()
                # Setup the saver (creates tables if needed)
                await saver.setup()
                print("✅ Checkpoint initialized successfully")
            except Exception as e:
                print(f"❌ Error initializing checkpoint: {e}")
                print(f"Error type: {type(e).__name__}")
                traceback.print_exc()
                # Reset saver context on error
                _saver_context = None
                saver = None
                # Fallback to MemorySaver if PostgreSQL connection fails
                print("⚠️  Falling back to MemorySaver (conversations won't persist)")
                saver = MemorySaver()
        else:
            saver = MemorySaver()

        return saver


async def close_checkpoint():
     """
     Close the checkpoint for the property sales agent graph.
     Properly exits the async context manager for AsyncPostgresSaver.
     """
     global saver, _saver_context
     
     if POSTGRES_AVAILABLE and _saver_context is not None and saver is not None:
          # Properly exit the async context manager
          await _saver_context.__aexit__(None, None, None)
          _saver_context = None
     
     saver = None



##> ============================================================================
##> GRAPH BUILDER
##> ============================================================================

## Global graph instance
_compiled_graph = None


async def create_property_sales_agent_graph():
     """
     To build the property sales agent graph. 
     
     This function creates the property sales agent graph.
     It includes the chat node, tool node, and edges.
     It also sets the entry point and returns the compiled graph.
     
     Returns a singleton instance to avoid recreating the graph on every request.
     """
     global _compiled_graph
     
     if _compiled_graph is not None:
          return _compiled_graph
     
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
     
     ##> Compile workflow with memory checkpointing
     memory =  await get_checkpoint()
     
     _compiled_graph = workflow.compile(checkpointer=memory)
     # _compiled_graph.get_graph().draw_png("property_sales_agent_graph.png")
     
     return _compiled_graph



##> ============================================================================
##> INVOCATION HELPER
##> ============================================================================


async def invoke_agent(message: str, conversation_id: str, is_new_conversation: bool)->dict:
     """
     Invoke the chatagent with a user message.
     Automatically adds system prompt for new conversations.
     
     Args:
          message: User's message
          conversation_id: Conversation ID (used as thread_id)
          is_new_conversation: Whether the conversation is new or not
     
     Returns:
          Dictionary with response and conversation_id
     """
     print(f"Invoking agent with message: {message}, conversation_id: {conversation_id}, is_new_conversation: {is_new_conversation}")
     graph = await create_property_sales_agent_graph()
     config = {"configurable": {"thread_id": conversation_id}}
          
     ## prepare initial state to invoke
     input_state = create_initial_state(
          conversation_id = conversation_id,
          user_message = message,
          is_new_conversation = is_new_conversation
     )
     
     print(f"Invoking agent with input state having new conversation: {is_new_conversation}")
     ## invoke agent
     
     try:
        result = await graph.ainvoke(input_state, config)   # ✅ ASYNC SAFE
     except Exception:
          traceback.print_exc()
          return {
               "response": "I encountered a system error. Please try again.",
               "conversation_id": conversation_id
          }
   
   
     ## Extract response for last message
     messages_list = result.get("messages", [])
     response_message = messages_list[-1].content if messages_list and len(messages_list) > 0 else "I apologize, but I encountered an issue. Could you pleasae rephrase your message?"
     print(f"Response message: {response_message}")
     ## return response
     return {
          "response"       : response_message,
          "conversation_id": conversation_id
     }