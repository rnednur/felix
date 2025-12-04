from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.config import settings

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
    CanvasItem
)
from app.models.column_metadata import ColumnMetadata, QueryRule

app = FastAPI(
    title="AI Analytics Platform",
    description="AI-assisted analytics for spreadsheets",
    version="1.0.0"
)

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
