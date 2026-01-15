from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.config import settings
import redis
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Set specific loggers to INFO level
logging.getLogger("api.agents").setLevel(logging.INFO)
logging.getLogger("orchestrator").setLevel(logging.INFO)
logging.getLogger("orchestrator.plan").setLevel(logging.INFO)
logging.getLogger("orchestrator.execute").setLevel(logging.INFO)
logging.getLogger("agent.factory").setLevel(logging.INFO)

# Suppress noisy loggers
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

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
    AgentExecution,
    SkillModel,
    SkillVersion,
    SkillUsageEvent
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

        # Initialize skills system
        from app.skills import setup_skills
        import os
        # Get absolute path relative to this file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        skills_dir = os.path.join(base_dir, "backend", "skills")
        setup_skills(skills_dir=skills_dir)

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


@app.get("/test-logging")
async def test_logging():
    """Test logging configuration"""
    logger = logging.getLogger("api.agents")
    logger.info("🧪 TEST: This is an INFO log from api.agents")
    logger.warning("⚠️  TEST: This is a WARNING log")
    logger.error("❌ TEST: This is an ERROR log")

    orchestrator_logger = logging.getLogger("orchestrator")
    orchestrator_logger.info("🧪 TEST: This is from orchestrator logger")

    return {
        "message": "Logging test complete - check server console",
        "loggers_configured": [
            "api.agents",
            "orchestrator",
            "orchestrator.plan",
            "orchestrator.execute",
            "agent.factory"
        ]
    }
