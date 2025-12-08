"""
Conversation Router for retrieving conversation history.

This module provides REST API endpoints for retrieving conversation
history and listing all conversations.
"""

## Imports
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.api_models import (
    ConversationListResponse,
    ConversationListItem,
    ConversationHistoryResponse,
    ChatMessage
)
from app.utils.db_connection import get_db, DatabaseConnection
from app.utils.helpers import extract_messages_from_checkpoint_state
from app.utils.auth import verify_bearer_token
from app.chatagent.builder import create_property_sales_agent_graph
from fastapi import Request


##> Initialize router
convo_router = APIRouter(prefix="/conversations", tags=["Conversations"])


##> ============================================================================
##> CONVERSATION ENDPOINTS
##> ============================================================================

@convo_router.get(
    "/",
    response_model=ConversationListResponse,
    description="Get all conversation IDs from the history table."
)
async def get_all_conversations(
    token_data: dict = Depends(verify_bearer_token),
    db: DatabaseConnection = Depends(get_db)
) -> ConversationListResponse:
    """
    Retrieve all conversation IDs from the history table.
    
    Returns:
        ConversationListResponse with list of all conversations.
    
    Raises:
        HTTPException: If database error occurs.
    """
    try:
        conversations = await db.execute_query(
            query="SELECT conversation_id, created_at FROM history ORDER BY created_at DESC",
            fetch_all=True
        )
        
        conversation_list = []
        for conv in conversations:
            # Convert datetime to ISO format string if it's a datetime object
            created_at = conv.get("created_at")
            if isinstance(created_at, datetime):
                created_at = created_at.isoformat()
            elif created_at is not None:
                created_at = str(created_at)
            
            conversation_list.append(
                ConversationListItem(
                    conversation_id=conv["conversation_id"],
                    created_at=created_at
                )
            )
        
        return ConversationListResponse(conversations=conversation_list)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving conversations: {str(e)}"
        )


@convo_router.get(
    "/{conversation_id}",
    response_model=ConversationHistoryResponse,
    description="Get chat history for a specific conversation ID."
)
async def get_conversation_history(
     conversation_id: str,
     request: Request,
     token_data: dict = Depends(verify_bearer_token),
     db: DatabaseConnection = Depends(get_db),
    
) -> ConversationHistoryResponse:
     """
     Retrieve chat history for a specific conversation.
     
     First checks if conversation exists in history table, then retrieves
     messages from PostgreSQL checkpoint database, filtering only user and AI messages.
     
     Args:
          conversation_id: UUID string identifying the conversation.
          db: Database connection dependency.
     
     Returns:
          ConversationHistoryResponse with filtered chat messages.
     
     Raises:
          HTTPException: 
               - 404 if conversation not found in history table
               - 500 if database or checkpoint error occurs
     """
     try:
          # Check if conversation exists in history table
          conversation = await db.execute_query(
               query="SELECT * FROM history WHERE conversation_id = ?",
               params=(conversation_id,),
               fetch_one=True
          )
          
          if not conversation:
               raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation with ID '{conversation_id}' not found."
               )
               
          print(f"Conversation found in history table. Conversation ID: {conversation_id}")
          
          # Get messages from PostgreSQL checkpoint database
          graph = await create_property_sales_agent_graph(request)
          config = {"configurable": {"thread_id": conversation_id}}
          
          try:
               state = await graph.aget_state(config)
               
               # Extract messages using helper function
               chat_messages = await extract_messages_from_checkpoint_state(state)
               
               return ConversationHistoryResponse(
                    conversation_id=conversation_id,
                    messages=chat_messages
               )
          
          except Exception as checkpoint_error:
               # If checkpoint retrieval fails, return empty messages
               print(f"Error retrieving checkpoint messages: {checkpoint_error}")
               return ConversationHistoryResponse(
                    conversation_id=conversation_id,
                    messages=[]
               )
     
     except HTTPException:
          # Re-raise HTTP exceptions
          raise
     except Exception as e:
          raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail=f"Error retrieving conversation history: {str(e)}"
          )
