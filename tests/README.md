# Tests Overview

This directory contains comprehensive test suites organized by component type.

## Test Structure

### `tests_agent/`
**Why:** Ensures the conversational agent core functions correctly before API integration.  
**How:** Mocks LLM clients, Request objects with app.state.checkpoint, and graph compilation to test graph building, state transitions, and node execution logic.  
**Covers:**
- Graph creation with checkpoint: Verifies graph is compiled with checkpoint from request.app.state.checkpoint
- State management (new/existing conversations): Tests proper initialization and message handling for different conversation types
- Iteration limits: Ensures agent stops after maximum iterations to prevent infinite loops
- Tool decision logic: Validates when agent chooses to call tools versus generating direct responses
- Message flow: Confirms messages are correctly passed between nodes and stored in state
- Request parameter handling: Tests that Request object is properly passed to graph creation functions

### `tests_api/`
**Why:** Validates end-to-end API behavior and security before deployment.  
**How:** Uses FastAPI TestClient to simulate HTTP requests with real authentication flows. Includes fixture to mock app.state.checkpoint for request handlers.  
**Covers:**
- Token generation: Tests API key to JWT token conversion works correctly
- API key validation: Ensures unauthorized requests are rejected with proper error codes
- Chat endpoint responses: Validates correct response format and content for chat requests
- Conversation persistence: Confirms conversations are saved and retrieved correctly from checkpoint database
- Error handling (400/401/500): Tests appropriate HTTP status codes for different failure scenarios
- Request validation: Ensures invalid request bodies are rejected with clear error messages
- Checkpoint access: Verifies endpoints correctly access checkpoint from request.app.state.checkpoint

### `tests_tool/`
**Why:** Confirms database tools work with actual schema and data structures.  
**How:** Executes real queries against test database using async tool invocations with module-scoped connection pool.  
**Covers:**
- Read queries (projects, leads, bookings): Tests SELECT operations return correct data from each table
- Write operations (INSERT/UPDATE): Validates data is correctly saved and modified in database
- Query result formatting: Ensures results are properly structured and returned to agent
- Error handling: Tests tool behavior when queries fail or return unexpected results
- Database connection pool management: Verifies module-scoped connection pool is established and reused across tests

### `tests_unit/`
**Why:** Fast feedback loop for tool logic without database overhead.  
**How:** Mocks database connections to test query validation, error handling, and return formats in isolation.  
**Covers:**
- SQL injection prevention: Ensures malicious SQL cannot be executed through user input
- Query sanitization: Tests that queries are validated before being sent to database
- Response structure validation: Confirms tools return data in expected tuple format (message, results)
- Edge case handling: Tests behavior with empty results, invalid queries, and connection failures
