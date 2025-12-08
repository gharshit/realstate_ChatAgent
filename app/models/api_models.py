from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from typing import Optional, List



class ChatRequest(BaseModel):
     """
     Request model for chat with the real estate agent.
     """
     message         : str = Field(..., description="User Query/Message for the real estate agent.")
     conversation_id : str = Field(..., description="Conversation ID for the chat session.")
     
     
     @field_validator('conversation_id')
     @classmethod
     def validate_conversation_id(cls, value: str) -> str:
          try:
               return str(UUID(value))
          except (ValueError, TypeError) as e:
               raise ValueError(f"Invalid conversation ID format. Please provide a valid UUID string. Error: {e}")
     
     


class ChatResponse(BaseModel):
     """
     Response model for chat with the real estate agent.
     """
     message            : str = Field(..., description="Response message from the real estate agent.")
     conversation_id    : str = Field(..., description="Conversation ID for the chat session.")


class ConversationListItem(BaseModel):
     """
     Model for a single conversation in the list.
     """
     conversation_id: str = Field(..., description="Unique conversation identifier.")
     created_at    : Optional[str] = Field(None, description="Timestamp when conversation was created.")


class ConversationListResponse(BaseModel):
     """
     Response model for listing all conversations.
     """
     conversations: List[ConversationListItem] = Field(..., description="List of all conversations.")


class ChatMessage(BaseModel):
     """
     Model for a single chat message.
     """
     message_id: int = Field(..., description="Unique message identifier (starts from 1).")
     role      : str = Field(..., description="Message role: 'user' or 'assistant'.")
     content   : str = Field(..., description="Message content.")


class ConversationHistoryResponse(BaseModel):
     """
     Response model for conversation history.
     """
     conversation_id: str = Field(..., description="Conversation identifier.")
     messages      : List[ChatMessage] = Field(..., description="List of chat messages (user and AI only).")
     
    