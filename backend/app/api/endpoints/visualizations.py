from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid

from app.core.database import get_db
from app.models.query import Query, QueryStatus
from app.models.visualization import Visualization
from app.schemas.visualization import (
    VizSuggestionRequest,
    VizSuggestionsResponse,
    CreateVizRequest,
    VizResponse
)
from app.services.visualization_service import VizService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/visualizations", tags=["visualizations"])


@router.post("/suggest", response_model=VizSuggestionsResponse)
async def suggest_visualizations(
    request: VizSuggestionRequest,
    db: Session = Depends(get_db)
):
    """Suggest chart types for query result"""
    query = db.query(Query).filter(Query.id == request.query_id).first()

    if not query:
        raise HTTPException(404, "Query not found")

    if query.status != QueryStatus.SUCCESS:
        raise HTTPException(400, "Query did not execute successfully")

    # Load query result
    storage = StorageService()
    try:
        df = storage.load_query_result(request.query_id)
    except Exception as e:
        raise HTTPException(500, f"Failed to load query result: {str(e)}")

    # Generate suggestions
    viz_service = VizService()
    suggestions = viz_service.suggest_charts(df, query.nl_input)

    return {"suggestions": suggestions}


@router.post("/", response_model=VizResponse)
async def create_visualization(
    request: CreateVizRequest,
    db: Session = Depends(get_db)
):
    """Create and save visualization"""
    # Verify query exists
    query = db.query(Query).filter(Query.id == request.query_id).first()

    if not query:
        raise HTTPException(404, "Query not found")

    viz_id = str(uuid.uuid4())

    viz = Visualization(
        id=viz_id,
        query_id=request.query_id,
        name=request.name,
        chart_type=request.chart_type,
        vega_spec=request.vega_spec
    )
    db.add(viz)
    db.commit()
    db.refresh(viz)

    return viz


@router.get("/{viz_id}", response_model=VizResponse)
async def get_visualization(viz_id: str, db: Session = Depends(get_db)):
    """Get visualization spec"""
    viz = db.query(Visualization).filter(Visualization.id == viz_id).first()

    if not viz:
        raise HTTPException(404, "Visualization not found")

    return viz


@router.get("/query/{query_id}", response_model=list[VizResponse])
async def list_query_visualizations(query_id: str, db: Session = Depends(get_db)):
    """List all visualizations for a query"""
    visualizations = db.query(Visualization).filter(
        Visualization.query_id == query_id
    ).all()

    return visualizations
