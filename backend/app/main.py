from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.config import settings
import redis

# Import models to ensure they're registered with SQLAlchemy
from app.models import (
    Dataset,
    DatasetVersion,
    Query,
    Visualization,
    SemanticMetric,
    AuditLog,
    CodeExecution,
    MLModel,
    Workspace,
    CanvasItem,
    AgentSession,
    AgentMessage,
    AgentExecution
)
from app.models.column_metadata import ColumnMetadata, QueryRule

app = FastAPI(
    title="AI Analytics Platform",
    description="AI-assisted analytics for spreadsheets",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Initialize Redis client
        redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=False  # Keep as bytes for compatibility
        )

        # Test Redis connection
        redis_client.ping()
        print("✅ Redis connection successful")

        # Initialize agent system
        from app.services.agents import setup_agent_system
        setup_agent_system(redis_client, config_path="agents_config.json")

    except Exception as e:
        print(f"⚠️  Warning: Could not initialize agent system: {e}")
        print("   Agent endpoints will not be available")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Analytics Platform API",
        "docs": "/docs"
    }
