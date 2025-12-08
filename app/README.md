# Application Service

## What This Service Does

This is the main FastAPI application for Proplens. It provides a REST API with a conversational AI agent that helps users find properties, answer questions about real estate projects, and book property visits. The agent uses LangGraph to manage conversation flow and can search the database and perform actions based on user requests.

## Structure

The application is divided into four main modules:

1. **router/** - API endpoints
2. **chatagent/** - Conversational AI agent logic
3. **models/** - Pydantic models for API requests/responses
4. **utils/** - Helper functions and utilities

## Components

### router/

**chat_router.py**
- Provides `/agents/chat` endpoint
- Handles chat requests from users
- Processes messages through the conversational agent
- Returns agent responses

**auth_router.py**
- Provides `/auth/token` endpoint
- Generates JWT access tokens using API key authentication
- Validates API keys and returns bearer tokens

**convo_router.py**
- Provides `/conversations/` endpoints
- Lists all conversations
- Retrieves chat history for specific conversations
- Requires bearer token authentication

### chatagent/

**builder.py**
- Creates and manages the LangGraph agent workflow
- Sets up PostgreSQL checkpoint for conversation persistence
- Handles agent initialization and cleanup
- Provides `invoke_agent()` function to process messages

**nodes.py**
- Defines the chat node that processes user messages
- Decides whether to call tools or generate responses
- Manages iteration limits to prevent infinite loops

**state.py**
- Defines `AgentChatState` - the state structure for the agent
- Manages conversation messages and context
- Creates initial state for new conversations

**tools.py**
- Provides secure SQL tools for database queries
- `run_secure_read_query` - For reading from projects, leads, bookings tables
- `run_secure_write_query` - For inserting/updating leads and bookings
- `search_project_info` - For searching project information online
- Includes security validation to prevent dangerous operations

**prompts.py**
- Contains system prompts for the AI agent
- Defines agent behavior and instructions

**llmclient.py**
- Manages LLM client initialization
- Provides LLM instances with and without tools
- Handles LLM cleanup

### models/

**api_models.py**
- Defines Pydantic models for API requests and responses
- `ChatRequest` - Input model for chat endpoint
- `ChatResponse` - Output model for chat endpoint
- `ConversationListResponse` - Model for listing conversations
- `ConversationHistoryResponse` - Model for conversation history

**db_models.py**
- Database-related Pydantic models (if any)

### utils/

**auth.py**
- JWT token creation and validation
- `create_access_token()` - Generates JWT tokens
- `verify_bearer_token()` - FastAPI dependency for token verification

**db_connection.py**
- Database connection wrapper for the app
- Provides `DatabaseConnection` class with query execution
- Validates queries to prevent dangerous operations
- Supports SELECT, INSERT, UPDATE operations

**helpers.py**
- Utility functions for conversation management
- `get_or_create_conversation()` - FastAPI dependency to get/create conversations
- `extract_messages_from_checkpoint_state()` - Extracts messages from LangGraph state
- Helper functions for timestamps and data processing

### Root Files

**main.py**
- FastAPI application entry point
- Sets up lifespan events (startup/shutdown)
- Initializes database, LLM client, and agent graph
- Includes all routers
- Provides root endpoint

**config.py**
- Loads configuration from environment variables
- Manages settings like `DATABASE_URL`, `ADMIN_KEY`, `JWT_SECRET_KEY`
- Sets max iterations for agent loops

## How to Run

### 1. Install Dependencies

```bash
pip install fastapi uvicorn sqlalchemy asyncpg langchain langgraph langchain-openai langchain-community python-dotenv pydantic python-jose
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://username:password@host:port/database
ADMIN_KEY=your-secret-admin-key
JWT_SECRET_KEY=your-secret-jwt-key
OPENAI_API_KEY=your-openai-api-key
MAX_ITERATIONS=5
JWT_TOKEN_EXPIRY_HOURS=1
```

### 3. Ensure Database is Set Up

Make sure you've run the database setup scripts from `db_service`:

```bash
cd db_service
python run_make_db.py
python run_seed_db.py
```

### 4. Start the Application

```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or from project root:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access the API

- API Documentation: `http://localhost:8000/docs`
- Root endpoint: `http://localhost:8000/`
- Chat endpoint: `POST http://localhost:8000/agents/chat`
- Auth endpoint: `POST http://localhost:8000/auth/token`

### 6. Using the API

**Get Access Token:**
```bash
curl -X POST "http://localhost:8000/auth/token" \
  -H "x-api-key: your-admin-key"
```

**Chat with Agent:**
```bash
curl -X POST "http://localhost:8000/agents/chat" \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me apartments in Dubai",
    "conversation_id": "your-uuid-here"
  }'
```

**Get Conversation History:**
```bash
curl -X GET "http://localhost:8000/conversations/your-uuid-here" \
  -H "Authorization: Bearer your-token"
```

## Important Notes

- The agent uses LangGraph with PostgreSQL checkpointing to persist conversations
- All database queries are validated for security - only SELECT, INSERT, UPDATE are allowed
- The agent has a maximum iteration limit to prevent infinite loops
- Bearer token authentication is required for most endpoints except `/auth/token`
- Conversation IDs must be valid UUIDs
- The agent can search the database and perform actions like booking properties site visit.
