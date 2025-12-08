# Property Management API

## Tech Stack

- **Python 3.12** - Programming language
- **FastAPI** - Modern web framework for building APIs
- **LangGraph** - Framework for building stateful, multi-actor applications with LLMs
- **LangChain** - Framework for developing applications powered by language models
- **PostgreSQL (Managed)** - Relational database for data persistence
- **SQLAlchemy 2.0** - Python SQL toolkit and ORM with async support
- **asyncpg** - Fast PostgreSQL database driver
- **Docker** - Containerization for deployment
- **pytest** - Testing framework
- **Pydantic** - Data validation using Python type annotations
- **JWT (python-jose)** - Token-based authentication

## Project Overview

Proplens is a property management API with an intelligent conversational agent that helps users find properties, answer questions about real estate projects, and book property visits. The system uses a LangGraph-based agent that can interact with the database, search for information, and perform actions based on user requests.

## Overall Arch

![Architecture](https://github.com/gharshit/realstate_ChatAgent/blob/main/summary.png)

## Modules

### app/

Main FastAPI application providing REST API endpoints and conversational AI agent functionality.

**Purpose:** Handles HTTP requests, authentication, chat interactions, and conversation management.

### db_service/

Database service module for PostgreSQL schema creation, data seeding, and connection management.

**Purpose:** Manages database setup, table creation, initial data population, and provides reusable database connection utilities.

### tests/

Comprehensive test suite covering API endpoints, agent components, tools, and unit tests.

**Purpose:** Ensures code quality and reliability through automated testing.

## Components

### 1. PostgreSQL Database

**Location:** `db_service/client/dbmodels.py`

**Purpose:** Defines the database schema using SQLAlchemy ORM models.

**Tables:**

- **projects** - Real estate project listings with details (name, location, price, bedrooms, features, etc.)
- **leads** - Customer leads with contact information and property preferences
- **bookings** - Property bookings linking leads to projects
- **history** - Conversation/chat history tracking

**Features:**

- Relationships between tables (foreign keys)
- Indexes for query optimization
- JSON columns for complex data (features, facilities, metadata)
- Automatic timestamps (created_at, updated_at)

### 2. Authentication

**Location:** `app/router/auth_router.py`, `app/utils/auth.py`

**Purpose:** Secure API access using API key and JWT token authentication.

**Components:**

- **API Key Authentication** - Validates admin API key to generate access tokens
- **JWT Token Generation** - Creates bearer tokens with configurable expiration
- **Token Verification** - Validates bearer tokens for protected endpoints

**Flow:**

1. Client sends API key in `x-api-key` header to `/auth/token`
2. Server validates API key and generates JWT token
3. Client uses JWT token in `Authorization: Bearer <token>` header for subsequent requests

### 3. LangGraph Agent (React-Style)

![ReAct Agent](https://github.com/gharshit/realstate_ChatAgent/blob/main/property_sales_agent_graph.png)

**Location:** `app/chatagent/`

**Purpose:** Conversational AI agent that processes user queries, decides actions, and generates responses.

**Architecture:**

- **State Management** (`state.py`) - Maintains conversation context and messages
- **Graph Builder** (`builder.py`) - Creates LangGraph workflow with PostgreSQL checkpointing
- **Chat Node** (`nodes.py`) - Processes messages, decides tool usage or direct response
- **Tools** (`tools.py`) - Secure database query tools and web search capabilities
- **LLM Client** (`llmclient.py`) - Manages OpenAI LLM instances with tool binding
- **Prompts** (`prompts.py`) - System prompts defining agent behavior

**React-Style Flow:**

1. User message received → Agent analyzes context
2. Agent decides: Use tools (search DB, book property) OR generate response
3. If tools needed → Execute tools → Update state → Re-analyze
4. If enough info → Generate final response
5. State persisted in PostgreSQL checkpoint for conversation continuity

**Security:**

- SQL query validation (only SELECT, INSERT, UPDATE allowed)
- Table-level access controls
- Prevents dangerous operations (DELETE, DROP, etc.)

### 4. APIs

**Location:** `app/router/`

**Purpose:** REST API endpoints for interacting with the system.

**Endpoints:**

**Authentication:**

- `POST /auth/token` - Generate JWT access token using API key

**Chat:**

- `POST /agents/chat` - Chat with the property sales agent
  - Requires: Bearer token, message, conversation_id
  - Returns: Agent response and conversation_id

**Conversations:**

- `GET /conversations/` - List all conversations (requires auth)
- `GET /conversations/{conversation_id}` - Get chat history for a conversation (requires auth)

**Features:**

- Automatic conversation creation if conversation_id doesn't exist
- Conversation state persistence using LangGraph checkpoints
- Message history retrieval from PostgreSQL checkpoint database

### 5. DB Service (Table Creation & Seeding)

**Location:** `db_service/service/`

**Purpose:** Database schema creation and initial data population.

**Components:**

**Table Creation** (`create_tables.py`):

- Creates all database tables from SQLAlchemy models
- Sets up indexes, foreign keys, and constraints
- Can drop and recreate tables (with `RECREATE_DB=true`)

**Data Seeding** (`insert_data_projects.py`):

- Reads project data from CSV file (`ProplensData.csv`)
- Validates and transforms data
- Inserts records into projects table
- Handles duplicates and invalid records

**Scripts:**

- `run_make_db.py` - Creates database schema
- `run_seed_db.py` - Populates database with sample data

**Connection Management** (`db_service/client/postgres_connection.py`):

- Async PostgreSQL connection pooling
- FastAPI dependency injection support
- Connection lifecycle management

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL database (managed or local)
- OpenAI API key

### Setup

1. **Install Dependencies**

```bash
pip install -r requirements.txt
```

2. **Configure Environment**
Create `.env` file:

```env
DATABASE_URL=postgresql://user:password@host:port/database
ADMIN_KEY=your-secret-admin-key
JWT_SECRET_KEY=your-secret-jwt-key
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o
MAX_ITERATIONS=5
JWT_TOKEN_EXPIRY_HOURS=1
RECREATE_DB=FALSE // TO CREATE FRESH DB
```

3. **Setup Database**

```bash
cd db_service
python run_make_db.py
python run_seed_db.py
```

4. **Run Application**

```bash
python run.py
```

Or with Docker:

```bash
docker build -t proplens .
docker run -p 8000:8000 --env-file .env proplens
```

5. **Access API**

- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/`

## Testing

Run tests with pytest:

```bash
pytest
```

Test structure:

- `tests/tests_api/` - API endpoint tests
- `tests/tests_agent/` - Agent component tests
- `tests/tests_tool/` - Tool functionality tests
- `tests/tests_unit/` - Unit tests

## Project Structure

```
proplens/
├── app/                    # Main FastAPI application
│   ├── chatagent/         # LangGraph agent components
│   ├── router/            # API endpoints
│   ├── models/            # Pydantic models
│   ├── utils/             # Helper utilities
│   ├── main.py           # FastAPI app entry point
│   └── config.py         # Application configuration
├── db_service/            # Database service module
│   ├── client/           # Database models and connection
│   ├── service/          # Table creation and seeding
│   └── run_*.py          # Setup scripts
├── tests/                 # Test suite
│   ├── tests_api/        # API tests
│   ├── tests_agent/      # Agent tests
│   ├── tests_tool/       # Tool tests
│   └── tests_unit/       # Unit tests
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── pytest.ini          # Pytest configuration
└── run.py              # Application startup script
```

## Documentation

- `app/README.md` - Detailed application service documentation
- `db_service/README.md` - Database service documentation




## Next Steps

- Solve minor bugs. Ex: to have llm use correct lead_id.
- Implement Logging for better error handling and debugging.


