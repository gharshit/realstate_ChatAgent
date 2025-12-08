## Main Application
from fastapi import FastAPI
from contextlib import asynccontextmanager

from psycopg_pool import AsyncConnectionPool
from app.chatagent.llmclient import init_llm, cleanup_llm
from app.router.chat_router import chat_router
from app.router.convo_router import convo_router
from app.router.auth_router import auth_router
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from db_service.client.postgres_connection import init_psql_db_from_url
from app.utils.db_connection import init_db, cleanup_db
from app.utils.helpers import clean_conn_string_for_psycopg
from app.config import settings
from psycopg.rows import dict_row
from typing import AsyncGenerator




@asynccontextmanager
async def lifespan(app: FastAPI)->AsyncGenerator:
    """
    Lifespan event handler for FastAPI application.
    """
    # Initialize PostgreSQL database
    await init_psql_db_from_url(settings.database_url)
    print("✅ PostgreSQL database initialized...")

    # Initialize app database connection wrapper
    await init_db()
    print("✅ App database connection initialized...")

    # Initialize LLM client
    init_llm()
    print("✅ LLM client initialized...")

    # Connection pool for langchain checkpoint
    # Create pool without context manager to keep it alive for entire lifespan
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
        "row_factory": dict_row
    }
    checkpoint_pool = AsyncConnectionPool(
        clean_conn_string_for_psycopg(settings.database_url),
        kwargs=connection_kwargs,
        open=False  # Don't open in constructor (recommended)
    )
    
    # Explicitly open the pool
    await checkpoint_pool.open()
    await checkpoint_pool.wait()
    
    # Create checkpoint saver using the pool
    checkpoint = AsyncPostgresSaver(checkpoint_pool)
    await checkpoint.setup()
    print("✅ Checkpoint connection pool created and initialized")

    # Store checkpoint in app state for request access
    app.state.checkpoint = checkpoint
    
    yield

    print("🔴 Shutting down...")
    
    # Close checkpoint pool
    if checkpoint_pool:
        try:
            await checkpoint_pool.close()
            print("✅ Checkpoint connection pool closed")
        except Exception as e:
            print(f"⚠️  Error closing checkpoint pool: {e}")
    
    await cleanup_db()
    cleanup_llm()



##> Initialize FastAPI app
app = FastAPI(
    title="Proplens API",
    description="Property management API with conversational agent",
    version="1.0.0",
    lifespan=lifespan
)


##> Include routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(convo_router)


@app.get("/")
async def root():
    """
    Root endpoint for the API.
    """
    return {"message": "Proplens API is running..."}



