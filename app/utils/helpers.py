from typing import Dict, Any, List, Tuple
from fastapi import HTTPException, status, Depends
from app.utils.db_connection import get_db, DatabaseConnection
from app.models.api_models import ChatRequest, ChatMessage
from app.utils.auth import verify_bearer_token
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime


def get_current_timestamp() -> datetime:
     """
     Get the current time as a datetime object for database operations.
     PostgreSQL expects datetime objects, not strings.
     """
     return datetime.now()


async def get_or_create_conversation(
    chat_request: ChatRequest,
    token_data: dict = Depends(verify_bearer_token),
    db: DatabaseConnection = Depends(get_db)
) -> Tuple[Dict[str, Any], bool]:
     """
     FastAPI dependency: Get or create a conversation.
     This runs before the request handler and ensures the conversation exists.
     
     Args:
          chat_request: ChatRequest model containing conversation_id (injected by FastAPI).
     
     Returns:
          Dictionary containing the conversation data.
     
     Raises:
          HTTPException: 500 if database error occurs or conversation cannot be created.
     """
     conversation_id = chat_request.conversation_id
     new_conversation = False
     
     try:
          conversation = None
          
          print(f"Getting conversation from the database. Conversation ID: {conversation_id}")
          ##> Get conversation from the database.
          conversation = await db.execute_query(
               query="SELECT * FROM history WHERE conversation_id = ?",
               params=(conversation_id,),
               fetch_one=True
          )
          print("Fetched conversation from the database: ", conversation)
          
          ##> If conversation not found, create a new one.
          if not conversation:
               new_conversation = True
               time =  get_current_timestamp()
               print(f"Creating new conversation in the database. Conversation ID: {conversation_id}")
               new_id = await db.execute_query(
                    query="INSERT INTO history (conversation_id, created_at, updated_at) VALUES (?, ?, ?)",
                    params=(conversation_id, time, time)
               )
               
               # Check if insert was successful
               if not new_id or new_id == 0:
                    raise HTTPException(
                         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                         detail="Failed to create conversation in database"
                    )
               
               # Fetch the newly created conversation
               conversation = await db.execute_query(
                    query="SELECT * FROM history WHERE conversation_id = ?",
                    params=(conversation_id,),
                    fetch_one=True
               )
          
          return conversation, new_conversation
     
     except HTTPException:
          # Re-raise HTTPException so it propagates to FastAPI
          raise
     
     except Exception as e:
          print(f"Error while getting or creating conversation: {str(e)}")
          raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail=f"Failed to retreive or create conversation: {str(e)}"
          )
          
          


async def extract_messages_from_checkpoint_state(state: Any) -> List[ChatMessage]:
     """
     Extract and filter messages from LangGraph checkpoint state.
     
     Filters only HumanMessage (user) and AIMessage (assistant) messages,
     skipping SystemMessage, ToolMessage, etc.
     Assigns message_id starting from 1.
     
     Args:
          state: LangGraph state object from checkpoint.
     
     Returns:
          List of ChatMessage objects with message_id, role, and content.
     """
     if not state or not state.values.get("messages"):
          return []
     
     messages_list = state.values.get("messages", [])
     chat_messages: List[ChatMessage] = []
     message_id = 1
     
     for msg in messages_list:
          # Filter only HumanMessage (user) and AIMessage (assistant)
          content = str(msg.content).strip()
          if isinstance(msg, HumanMessage):
               if content:
                    chat_messages.append(ChatMessage(
                         message_id=message_id,
                         role="user",
                         content=content
                    ))
                    message_id += 1
          elif isinstance(msg, AIMessage):
               if content:
                    chat_messages.append(ChatMessage(
                         message_id=message_id,
                         role="assistant",
                         content=str(content)
                    ))
                    message_id += 1
               # Skip SystemMessage, ToolMessage, etc.
     
     return chat_messages






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
    
    # Reconstruct URL with cleaned parameters
    new_query = urlencode(query_params, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    clean_url = urlunparse(new_parsed)
    
    print(f"Cleaned connection string: {clean_url}")
    
    return clean_url