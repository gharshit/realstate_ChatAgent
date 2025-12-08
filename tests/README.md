# Tests Overview

This directory contains comprehensive test suites organized by component type.

## Test Structure

### `tests_agent/`
**Why:** Ensures the conversational agent core functions correctly before API integration.  
**How:** Mocks LLM clients and checkpoints to test graph building, state transitions, and node execution logic.  
**Covers:**
- Singleton pattern validation: Verifies only one graph instance exists across multiple calls
- State management (new/existing conversations): Tests proper initialization and message handling for different conversation types
- Iteration limits: Ensures agent stops after maximum iterations to prevent infinite loops
- Tool decision logic: Validates when agent chooses to call tools versus generating direct responses
- Message flow: Confirms messages are correctly passed between nodes and stored in state

### `tests_api/`
**Why:** Validates end-to-end API behavior and security before deployment.  
**How:** Uses FastAPI TestClient to simulate HTTP requests with real authentication flows.  
**Covers:**
- Token generation: Tests API key to JWT token conversion works correctly
- API key validation: Ensures unauthorized requests are rejected with proper error codes
- Chat endpoint responses: Validates correct response format and content for chat requests
- Conversation persistence: Confirms conversations are saved and retrieved correctly from database
- Error handling (400/401/500): Tests appropriate HTTP status codes for different failure scenarios
- Request validation: Ensures invalid request bodies are rejected with clear error messages

### `tests_tool/`
**Why:** Confirms database tools work with actual schema and data structures.  
**How:** Executes real queries against test database using async tool invocations.  
**Covers:**
- Read queries (projects, leads, bookings): Tests SELECT operations return correct data from each table
- Write operations (INSERT/UPDATE): Validates data is correctly saved and modified in database
- Query result formatting: Ensures results are properly structured and returned to agent
- Error handling: Tests tool behavior when queries fail or return unexpected results
- Database connection management: Verifies connections are established and closed properly

### `tests_unit/`
**Why:** Fast feedback loop for tool logic without database overhead.  
**How:** Mocks database connections to test query validation, error handling, and return formats in isolation.  
**Covers:**
- SQL injection prevention: Ensures malicious SQL cannot be executed through user input
- Query sanitization: Tests that queries are validated before being sent to database
- Response structure validation: Confirms tools return data in expected tuple format (message, results)
- Edge case handling: Tests behavior with empty results, invalid queries, and connection failures
