## Main Application
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.chatagent.llmclient import init_llm, cleanup_llm
from app.router.chat_router import chat_router
from app.router.convo_router import convo_router
from app.router.auth_router import auth_router
from app.chatagent.builder import create_property_sales_agent_graph, close_checkpoint
from db_service.client.postgres_connection import init_psql_db_from_url, close_psql_db
from app.utils.db_connection import init_db, cleanup_db
from app.config import settings




@asynccontextmanager
async def lifespan(app: FastAPI):
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

    # Initialize property sales agent graph
    await create_property_sales_agent_graph()
    print("✅ Property sales agent graph initialized...")

    yield

    print("🔴 Shutting down...")
    await close_checkpoint()
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



