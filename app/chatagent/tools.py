"""
Secure SQL Tools for Property Sales Conversational Agent.

This module provides secure SQL tools with strict table-level access controls:
1. run_secure_read_query    - For SELECT/WITH queries on allowed tables
2. run_secure_write_query   - For INSERT/UPDATE queries on bookings and leads tables
3. search_project_info      - For searching project information via DuckDuckGo

Security Features:
- Table-level access controls (whitelist approach)
- Query validation and sanitization
- Prevention of destructive operations
- No access to history table
- Detailed error messages for debugging
"""

## Imports
import re
from typing import Tuple, List, Dict, Any
from pydantic import Field
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchResults
from app.utils.db_connection import get_db
from app.utils.helpers import get_current_timestamp


##> ============================================================================
##> SQL SECURITY UTILITIES
##> ============================================================================

class SQLSecurityValidator:
     """
     Validates SQL queries against security policies and access controls.
     """
     
     # Define forbidden keywords for destructive operations
     FORBIDDEN_KEYWORDS = [
          "DELETE", "DROP", "TRUNCATE", "ALTER", "EXEC", "EXECUTE",
          "GRANT", "REVOKE", "CREATE", "REPLACE", "ATTACH", "DETACH",
          "PRAGMA"
     ]
     
     # Define allowed tables for READ operations (SELECT, WITH)
     READ_ALLOWED_TABLES = ["leads", "bookings", "projects"]
     
     # Define allowed tables for WRITE operations (INSERT, UPDATE)
     WRITE_ALLOWED_TABLES = ["bookings", "leads"]
     
     # Define read-only operations
     READ_OPERATIONS = ["SELECT", "WITH"]
     
     # Define write operations
     WRITE_OPERATIONS = ["INSERT", "UPDATE"]
     
     @staticmethod
     def _clean_query(query: str) -> str:
          """
          Clean and normalize SQL query by removing comments and extra whitespace.
          
          Args:
               query: Raw SQL query string
               
          Returns:
               Cleaned query string in uppercase
          """
          # Remove single-line comments (-- comment)
          query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
          
          # Remove multi-line comments (/* comment */)
          query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
          
          # Normalize whitespace and convert to uppercase
          query = ' '.join(query.split()).upper()
          
          return query
     
     @staticmethod
     def _extract_tables_from_query(query: str) -> List[str]:
          """
          Extract table names from SQL query.
          
          Args:
               query: SQL query string (should be cleaned/uppercase)
               
          Returns:
               List of table names found in query
          """
          tables = []
          
          # Pattern to match table names after FROM, JOIN, INTO, UPDATE
          # Matches: FROM table, JOIN table, INTO table, UPDATE table
          patterns = [
               r'\bFROM\s+(\w+)',
               r'\bJOIN\s+(\w+)',
               r'\bINTO\s+(\w+)',
               r'\bUPDATE\s+(\w+)'
          ]
          
          for pattern in patterns:
               matches = re.findall(pattern, query)
               tables.extend(matches)
          
          # Convert to lowercase and remove duplicates
          tables = list(set([table.lower() for table in tables]))
          
          return tables
     
     @staticmethod
     def _get_query_operation(query: str) -> str:
          """
          Extract the main SQL operation from query.
          
          Args:
               query: SQL query string (should be cleaned/uppercase)
               
          Returns:
               Query operation (SELECT, INSERT, UPDATE, WITH, etc.)
          """
          # Get first word from query
          operation = query.strip().split()[0] if query.strip() else ""
          return operation
     
     ##> TOOL DEFINITION FOR SECURE READ QUERY
     @classmethod
     def validate_read_query(cls, query: str) -> Tuple[bool, str, List[str]]:
          """
          Validate query for READ operations (SELECT, WITH).
          
          Args:
               query: SQL query to validate
               
          Returns:
               Tuple of (is_valid, error_message, tables_accessed)
          """
          # Clean query
          cleaned_query = cls._clean_query(query)
          
          # Check if query is empty
          if not cleaned_query:
               return False, "Error: Empty query provided", []
          
          # Check for forbidden keywords
          for keyword in cls.FORBIDDEN_KEYWORDS:
               pattern = r'\b' + keyword + r'\b'
               if re.search(pattern, cleaned_query):
                    return False, f"Error: Forbidden operation '{keyword}' detected. Only SELECT and WITH operations are allowed for reading.", []
          
          # Check if query operation is allowed
          operation = cls._get_query_operation(cleaned_query)
          if operation not in cls.READ_OPERATIONS:
               return False, f"Error: Operation '{operation}' not allowed for read queries. Only SELECT and WITH are permitted.", []
          
          # Extract tables from query
          tables = cls._extract_tables_from_query(cleaned_query)
          
          # Check if any table is accessed
          if not tables:
               return False, "Error: No valid table found in query. Please specify a table to query.", []
          
          # Check if all tables are in the allowed list
          unauthorized_tables = [t for t in tables if t not in cls.READ_ALLOWED_TABLES]
          if unauthorized_tables:
               return False, f"Error: Unauthorized table access detected: {', '.join(unauthorized_tables)}. Allowed tables for reading: {', '.join(cls.READ_ALLOWED_TABLES)}. Note: 'history' table is not accessible.", []
          
          # Check if history table is being accessed (explicit block)
          if "history" in [t.lower() for t in tables]:
               return False, "Error: Access to 'history' table is forbidden. Allowed tables: leads, bookings, projects.", []
          
          return True, "Query validated successfully", tables
     
     
     ##> TOOL DEFINITION FOR SECURE WRITE QUERY
     @classmethod
     def validate_write_query(cls, query: str) -> Tuple[bool, str, List[str]]:
          """
          Validate query for WRITE operations (INSERT, UPDATE).
          
          Args:
               query: SQL query to validate
               
          Returns:
               Tuple of (is_valid, error_message, tables_accessed)
          """
          # Clean query
          cleaned_query = cls._clean_query(query)
          
          # Check if query is empty
          if not cleaned_query:
               return False, "Error: Empty query provided", []
          
          # Check for forbidden keywords (including SELECT for write queries)
          forbidden_for_write = cls.FORBIDDEN_KEYWORDS + ["SELECT", "WITH"]
          for keyword in forbidden_for_write:
               pattern = r'\b' + keyword + r'\b'
               if re.search(pattern, cleaned_query):
                    return False, f"Error: Forbidden operation '{keyword}' detected. Only INSERT and UPDATE operations are allowed for writing.", []
          
          # Check if query operation is allowed
          operation = cls._get_query_operation(cleaned_query)
          if operation not in cls.WRITE_OPERATIONS:
               return False, f"Error: Operation '{operation}' not allowed for write queries. Only INSERT and UPDATE are permitted.", []
          
          # Extract tables from query
          tables = cls._extract_tables_from_query(cleaned_query)
          
          # Check if any table is accessed
          if not tables:
               return False, "Error: No valid table found in query. Please specify a table to write to.", []
          
          # Check if all tables are in the allowed write list
          unauthorized_tables = [t for t in tables if t not in cls.WRITE_ALLOWED_TABLES]
          if unauthorized_tables:
               return False, f"Error: Unauthorized table write access detected: {', '.join(unauthorized_tables)}. Only 'bookings' and 'leads' tables are allowed for write operations.", []
          
          # Explicit check for history table (should never be written to)
          if "history" in [t.lower() for t in tables]:
               return False, "Error: Write access to 'history' table is absolutely forbidden.", []
          
          # Explicit check for projects table
          if "projects" in tables:
               return False, "Error: Write access to 'projects' table is forbidden. Only 'bookings' and 'leads' tables can be modified.", []
          
          return True, "Query validated successfully", tables


##> ============================================================================
##> SECURE SQL TOOLS
##> ============================================================================

@tool(description="Execute a secure READ-ONLY SQL query on allowed tables (leads, bookings, projects).")
async def run_secure_read_query(
     query: str = Field(
          ..., 
          description="SELECT or WITH query to read data from database. Allowed tables: leads, bookings, projects. History table is NOT accessible.",
          min_length=2
     )
) -> Tuple[str, List[Dict[str, Any]]]:
     """
     Execute a secure READ-ONLY SQL query (SELECT / WITH) on allowed tables.
     
     The tool received on single string query, and no other format is allowed.
     
     This tool provides read access to the following tables:
     - leads    : Customer lead information
     - bookings : Property booking records
     - projects : Property project information
     
     RESTRICTIONS:
     - Only SELECT and WITH queries are allowed
     - No access to 'history' table
     - No destructive operations (DELETE, DROP, TRUNCATE, etc.)
     - No write operations (INSERT, UPDATE)
     
     Args:
          query: SQL SELECT or WITH query to execute
          
     Returns:
          Tuple[str, List[Dict[str, Any]]]: 
               - First element: Success/error message
               - Second element: List of result rows as dictionaries (empty list on error)
               
     Examples:
          - "SELECT DISTINCT city FROM projects;"
          - "SELECT project_name, project_description, project_location FROM projects WHERE price_usd > 500000"
          - "SELECT * FROM projects WHERE city = 'Dubai' LIMIT 10"
          - "SELECT * FROM leads WHERE preferred_budget > 500000"
          - "SELECT b.*, l.email FROM bookings b JOIN leads l ON b.lead_id = l.id"
          - "WITH recent_bookings AS (SELECT * FROM bookings WHERE booking_date > '2024-01-01') SELECT * FROM recent_bookings"
          
     Invalid Examples:
          - {"query": "SELECT DISTINCT city FROM projects"} 
          - "SELECT DISTINCT city FROM projects; SELECT * FROM projects WHERE city = 'Dubai' LIMIT 10;" 
     """
     try:
          print(f"Query: {query}")
          # Validate query
          is_valid, message, tables = SQLSecurityValidator.validate_read_query(query)
          
          if not is_valid:
               return message, []
          
          # Execute query using database connection
          db     = get_db()
          result = await db.execute_query(
               query      =query,
               fetch_all  =True
          )
          
          # Handle None result
          if result is None:
               return "Success: Query executed but returned no results", []
          
          # Return success with results
          return f"Success: Retrieved {len(result)} row(s) from tables: {', '.join(tables)}", result
          
     except Exception as e:
          error_msg = f"Unexpected error during query execution (try with a different query): {str(e)}"
          print(f"Error: {error_msg}")
          # Return more detailed error message for debugging
          return f"Error: {error_msg}", []


@tool(description="Execute a secure WRITE SQL query on 'bookings' and 'leads' tables (INSERT/UPDATE operations).")
async def run_secure_write_query(
     query: str = Field(
          ...,
          description="INSERT or UPDATE query to write data to 'bookings' or 'leads' tables. IMPORTANT: Use literal values directly in the query, NOT parameterized placeholders (?). Use single quotes for strings and no quotes for numbers. No other tables are allowed for write operations.",
          min_length=2
     )
) -> Tuple[str, int]:
     """
     Execute a secure WRITE SQL query (INSERT / UPDATE) on allowed tables.
     
     This tool provides write access to:
     - bookings : Property booking records
     - leads    : Customer lead information
     
     RESTRICTIONS:
     - Only INSERT and UPDATE queries are allowed
     - Write access ONLY to 'bookings' and 'leads' tables
     - No access to 'projects' or 'history' tables for writing
     - No destructive operations (DELETE, DROP, TRUNCATE, etc.)
     - No read operations (SELECT, WITH)
     - DO NOT use parameterized queries with ? placeholders - use literal values directly
     
     Args:
          query: SQL INSERT or UPDATE query to execute on allowed tables.
                 Must use literal values (e.g., 'John', 500000) NOT placeholders (?).
          
     Returns:
          Tuple[str, int]:
               - First element: Success/error message
               - Second element: 
                    - For INSERT: ID of newly inserted row
                    - For UPDATE: Number of rows affected
                    - For error: 0
               
     Examples (CORRECT - using literal values):
          BOOKINGS:
          - "INSERT INTO bookings (lead_id, project_id, booking_date, booking_status) VALUES (1, 5, '2024-12-05', 'confirmed')"
          - "UPDATE bookings SET booking_status = 'confirmed' WHERE id = 10"
          
          LEADS:
          - "INSERT INTO leads (first_name, last_name, email, preferred_city, preferred_budget) VALUES ('John', 'Doe', 'john@example.com', 'Dubai', 500000)"
          - "UPDATE leads SET preferred_budget = 600000 WHERE id = 3"
          
     Examples (INCORRECT - DO NOT USE):
          - "INSERT INTO leads (first_name, preferred_city) VALUES (?, ?)"  ❌ WRONG - uses placeholders
          - "INSERT INTO leads (first_name, preferred_city) VALUES (?, ?, ?, ?, ?)"  ❌ WRONG - uses placeholders
     """
     try:
          
          print(f"Query: {query}")
          # Validate query
          is_valid, message, tables = SQLSecurityValidator.validate_write_query(query)
          
          if not is_valid:
               return message, 0
          
          # Execute query using database connection
          db     = get_db()
          result = await db.execute_query(query=query)
          
          # Handle result based on operation type
          if result is None or result == 0:
               return "Warning: Query executed but no rows were affected", 0
          
          # Determine operation type for message
          operation = SQLSecurityValidator._get_query_operation(
               SQLSecurityValidator._clean_query(query)
          )
          
          # Get table name for better message
          table_name = tables[0] if tables else "table"
          
          if operation == "INSERT":
               return f"Success: New {table_name} record created with ID: {result}", result
          elif operation == "UPDATE":
               return f"Success: Updated {result} {table_name} record(s)", result
          else:
               return f"Success: Operation completed on {table_name}, affected ID/count: {result}", result
          
     except Exception as e:
          error_msg = f"Unexpected error during query execution (try with a different query): {str(e)}"
          print(f"Error: {error_msg}")
          return "Some error occured. Try updating and trying with a different query.", 0


##> ============================================================================
##> WEB SEARCH TOOL
##> ============================================================================

@tool(description="Search for additional information about a specific property project using DuckDuckGo.")
async def search_project_info(
     project_name: str = Field(
          ...,
          description="Name of the property project to search for",
          min_length=2
     ),
     location: str = Field(
          ...,
          description="Location of the property project to search for like city name or country name or specific area name.",
          min_length=2   
     ),
     project_description: str = Field(
          default="",
          description="Brief description of the developer name, location or location oriented information to refine search results.",
          max_length=50
     ),
     project_metadata: str = Field(
          default="",
          description="Specific query what to search for or look for or retrieve from the web to enhance search query under 70 characters.",
          max_length=70
     )
) -> Tuple[str, str]:
     """
     Search for additional information about a property project using DuckDuckGo.
     
     This tool should be used when:
     - The required information about a property is NOT available in the database
     - User asks about external information (nearby amenities, connectivity, reviews, etc.)
     - You need to verify or supplement project details
     
     The tool combines project name, description, and metadata to create an effective
     search query and returns relevant information from the web. Use this carefully and do atmost 2-3 searches at a time.
     
     Args:
          project_name: Name of the property project to search
          location: Location of the property project to search for
          project_description: Brief description of the project (optional) (like developer name, location, city which can help in finding the project.)
          project_metadata: a to the point what to search for in the web to get the information about the project with location name or city name.
          
     Returns:
          Tuple[str, str]:
               - First element: Status message (Success/Error)
               - Second element: Search results as formatted text with titles, snippets
               
     Examples:
          search_project_info(
               project_name="Marina Bay Residences",
               location="Dubai Marina",
               project_description="Developer: Emaar Properties, Location: Dubai Marina"
               project_metadata= "search nearest airport and its distance to the Marina Bay Residences in Dubai"
          )
          
          search_project_info(
               project_name="ELLE Resort & Beach Club",
               location="Bali, Indonesia",
               project_description="Developer: Geonet, Location: Bali, Indonesia",
               project_metadata= "nearby school,nearby malls and nearest hospital near Elle Resort & Beach Club in Bali, Indonesia"
          )
          
     Return Format:
          The second element contains search results with:
          - Title of each result
          - Brief snippet/description
          
          Example return:
          "Success", "Title: Marina Bay Residences - Luxury Living
                         Snippet: Discover luxury waterfront apartments...
                         ---
                         Title: Marina Bay Residences Reviews
                         Snippet: Residents love the amenities and location..."
     """
     try:
          print(f"Searching for project: {project_name}, description: {project_description}, metadata: {project_metadata}")
          # Build comprehensive search query
          search_parts = [project_name, location]
          
          if project_description:
               desc = str(project_description).strip()
               if desc:
                    search_parts.append(desc)
          
          if project_metadata:
               meta = str(project_metadata).strip()
               if meta:
                    search_parts.append(meta)
          
          search_query = " ".join(search_parts)
          
          # Initialize DuckDuckGo search
          search_tool = DuckDuckGoSearchResults(output_format="string")
          
          # Execute search (DuckDuckGoSearchResults is synchronous, uses .run() method)
          results = search_tool.run(search_query)
          
          print(f"Search results: {results}")
          
          # Handle different return types: string or list/empty
          if not results:
               return "Warning: No search results found for the given project", ""
          
          # Convert results to string if it's not already
          return f"Success: Found information about '{project_name}'", results
          
     except Exception as e:
          message = f"Error: {str(e)}. Try updating and trying with a different project name or description or metadata."
          print(f"Error: {message}")
          return message, ""




@tool(description="Get current timestamp as a string in format 'YYYY-MM-DD HH:MM:SS' for use in INSERT or UPDATE queries. Use this value directly in SQL queries as a string literal (e.g., '2025-12-08 01:14:31').")
async def get_current_time() -> str:
     """
     Get the current time as a formatted string for use in SQL queries.
     
     Returns a string in format 'YYYY-MM-DD HH:MM:SS' that can be used directly
     in SQL INSERT or UPDATE queries as a string literal.
     
     Note: This tool is designed for use with literal SQL queries (not parameterized).
     The run_secure_write_query tool uses literal SQL, so this string format works correctly.
     
     Returns:
         str: Current timestamp as string in format 'YYYY-MM-DD HH:MM:SS'
     """
     print(f"Getting current time")
     # Return formatted string for use in literal SQL queries
     return get_current_timestamp().strftime("%Y-%m-%d %H:%M:%S")




##> ============================================================================
##> TOOL LIST FOR AGENT
##> ============================================================================

# Export tools for use in agent
secure_sql_tools = [
    get_current_time,
    run_secure_read_query,
    run_secure_write_query,
    search_project_info
]

