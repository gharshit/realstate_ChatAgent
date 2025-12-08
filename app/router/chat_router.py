"""
Chat Router for the Property Sales Conversational Agent.

This module provides the REST API endpoint for interacting with
the Silver Land Properties conversational agent.
"""

## Imports
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.api_models import ChatRequest, ChatResponse
from app.utils.helpers import get_or_create_conversation
from app.chatagent.builder import invoke_agent
from fastapi import Request
from typing import Dict, Any, Tuple


##> Initialize router
chat_router = APIRouter(prefix="/agents", tags=["Chat"])


##> ============================================================================
##> CHAT ENDPOINT
##> ============================================================================

@chat_router.post(
    "/chat",
    response_model=ChatResponse,
    description="Chat with the Silver Land Properties AI assistant."
)
async def chat_with_agent(
    chat_request: ChatRequest,
    request: Request,
    context_data: Tuple[Dict[str, Any], bool] = Depends(get_or_create_conversation)
) -> ChatResponse:
    """
    Chat with the property sales agent.
    
    This endpoint processes user messages through an iterative agent that:
    - Understands property preferences
    - Searches the database for matching properties
    - Answers questions about projects
    - Books property visits
    
    Args:
        chat_request: ChatRequest with user message and conversation_id.
        conversation: Conversation data from database dependency.
    
    Returns:
        ChatResponse with agent's response message.
    
    Raises:
        HTTPException: If processing error occurs.
    """
    conversation, new_conversation = context_data
    try:
        print(f"Chat request received: {chat_request}")
        # Invoke the agent
        result = await invoke_agent(
            message        =chat_request.message,
            conversation_id=conversation['conversation_id'],
            is_new_conversation=new_conversation,
            request=request
        )
        
        # Build response
        return ChatResponse(
            message            =result["response"],
            conversation_id    =result["conversation_id"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {str(e)}"
        )

