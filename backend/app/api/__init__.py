from fastapi import APIRouter
from app.api.endpoints import datasets, queries, visualizations, analysis, python_analysis, deep_research

api_router = APIRouter()

api_router.include_router(datasets.router)
api_router.include_router(queries.router)
api_router.include_router(visualizations.router)
api_router.include_router(analysis.router)
api_router.include_router(python_analysis.router)
api_router.include_router(deep_research.router, prefix="/deep-research", tags=["deep-research"])
