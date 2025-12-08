"""
Startup script for FastAPI application.
Sets Windows event loop policy before uvicorn starts.
"""
import asyncio
import os
import sys

# Fix for Windows: psycopg requires SelectorEventLoop, not ProactorEventLoop
# This MUST be set before uvicorn creates its event loop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Now import and run uvicorn
import uvicorn

if __name__ == "__main__":
    # Disable reload in Docker/production (reload is for development only)
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload
    )
