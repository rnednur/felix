"""
Dashboard Generation API Endpoints

Provides endpoints for one-click dashboard generation with SSE streaming.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, Any
import json
import asyncio
import logging
import numpy as np
from datetime import datetime


class NumpyJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles numpy types."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, (np.bool_,)):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'isoformat'):  # pandas Timestamp, etc.
            return obj.isoformat()
        return super().default(obj)


def json_dumps_safe(obj: Any) -> str:
    """Safely serialize to JSON, handling numpy types."""
    return json.dumps(obj, cls=NumpyJSONEncoder)


from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, Dataset
from app.schemas.dashboard import (
    DashboardGenerateRequest,
    DashboardOptions,
    DashboardProgress,
    DashboardPhase,
    DashboardGenerateResult,
)
from app.services.agents.dashboard_planner_agent import DashboardPlannerAgent
from app.schemas.agent import AgentConfig
from app.core.config import settings


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


def get_dashboard_planner_agent() -> DashboardPlannerAgent:
    """Get or create dashboard planner agent instance."""
    config = AgentConfig(
        name="dashboard_planner_agent",
        display_name="Dashboard Planner Agent",
        description="Orchestrates automatic dashboard generation from datasets",
        tier="free",
        enabled=True,
        capabilities=[
            "dashboard_generation",
            "kpi_identification",
            "chart_selection",
            "insight_generation",
            "layout_optimization"
        ],
        libraries=["duckdb", "pandas"],
        llm_config={
            "default_model": settings.AGENT_MODEL,  # Use configured model
            "temperature": 0.3,
            "max_tokens": 2000
        },
        prompts={},
        intent_keywords=[
            "dashboard", "overview", "summary dashboard", "create dashboard",
            "auto dashboard", "visualize all", "complete analysis"
        ]
    )
    return DashboardPlannerAgent(config)


@router.post("/generate")
async def generate_dashboard(
    request: DashboardGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a complete dashboard from a dataset.

    Returns Server-Sent Events (SSE) stream with progress updates.

    Progress events have the format:
    ```
    event: progress
    data: {"phase": "analyzing", "progress": 10, "message": "..."}
    ```

    Final event:
    ```
    event: complete
    data: {"workspace_id": "uuid", "name": "Dashboard Name", ...}
    ```
    """
    # Validate dataset exists and user has access
    dataset = db.query(Dataset).filter(
        Dataset.id == request.dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Check user has access to dataset
    if dataset.owner_id != current_user.id:
        # TODO: Check for shared access
        raise HTTPException(status_code=403, detail="Access denied to this dataset")

    async def generate_sse():
        """Generator for SSE events."""
        agent = get_dashboard_planner_agent()

        try:
            async for progress in agent.generate_dashboard_streaming(
                dataset_id=request.dataset_id,
                options=request.options,
                prompt=request.prompt,
                user_id=current_user.id
            ):
                # Convert progress to SSE event
                if progress.phase == DashboardPhase.COMPLETE:
                    # Extract workspace_id from the data
                    event_data = {
                        "phase": progress.phase.value,
                        "progress": progress.progress,
                        "message": progress.message,
                    }
                    if progress.data:
                        event_data["kpis"] = [k.model_dump() for k in progress.data.kpis] if progress.data.kpis else []
                        event_data["charts"] = progress.data.charts or []
                        event_data["insights"] = progress.data.insights or []
                        # Include workspace_id for frontend navigation
                        if progress.data.workspace_id:
                            event_data["workspace_id"] = progress.data.workspace_id

                    yield f"event: complete\ndata: {json_dumps_safe(event_data)}\n\n"

                elif progress.phase == DashboardPhase.ERROR:
                    error_data = {
                        "error": progress.message,
                        "phase": progress.phase.value
                    }
                    yield f"event: error\ndata: {json_dumps_safe(error_data)}\n\n"

                else:
                    progress_data = {
                        "phase": progress.phase.value,
                        "progress": progress.progress,
                        "message": progress.message,
                    }
                    if progress.data:
                        if progress.data.kpis:
                            progress_data["kpis"] = [k.model_dump() for k in progress.data.kpis]
                        if progress.data.charts:
                            progress_data["charts"] = progress.data.charts
                        if progress.data.insights:
                            progress_data["insights"] = progress.data.insights

                    yield f"event: progress\ndata: {json_dumps_safe(progress_data)}\n\n"

                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error(f"Dashboard generation error: {str(e)}", exc_info=True)
            error_data = {"error": str(e), "phase": "error"}
            yield f"event: error\ndata: {json_dumps_safe(error_data)}\n\n"

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/generate/sync")
async def generate_dashboard_sync(
    request: DashboardGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DashboardGenerateResult:
    """
    Generate a dashboard synchronously (non-streaming).

    Returns the final result after generation is complete.
    Use the streaming endpoint for progress updates.
    """
    # Validate dataset
    dataset = db.query(Dataset).filter(
        Dataset.id == request.dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this dataset")

    agent = get_dashboard_planner_agent()

    import time
    start_time = time.time()

    workspace_id = None
    kpi_count = 0
    chart_count = 0
    insight_count = 0

    async for progress in agent.generate_dashboard_streaming(
        dataset_id=request.dataset_id,
        options=request.options,
        prompt=request.prompt,
        user_id=current_user.id
    ):
        if progress.phase == DashboardPhase.ERROR:
            raise HTTPException(status_code=500, detail=progress.message)

        if progress.phase == DashboardPhase.COMPLETE and progress.data:
            kpi_count = len(progress.data.kpis) if progress.data.kpis else 0
            chart_count = len(progress.data.charts) if progress.data.charts else 0
            insight_count = len(progress.data.insights) if progress.data.insights else 0

    # Get workspace ID from database (most recent for this user/dataset)
    from app.models import Workspace
    workspace = db.query(Workspace).filter(
        Workspace.dataset_id == request.dataset_id,
        Workspace.owner_id == current_user.id
    ).order_by(Workspace.created_at.desc()).first()

    if not workspace:
        raise HTTPException(status_code=500, detail="Workspace creation failed")

    generation_time = time.time() - start_time

    return DashboardGenerateResult(
        workspace_id=workspace.id,
        name=workspace.name,
        dataset_id=request.dataset_id,
        kpi_count=kpi_count,
        chart_count=chart_count,
        insight_count=insight_count,
        summary_table_included=request.options.include_summary_table,
        generation_time_seconds=round(generation_time, 2)
    )


@router.get("/suggestions/{dataset_id}")
async def get_dashboard_suggestions(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get suggestions for dashboard generation without actually creating one.

    Returns potential KPIs, chart types, and insights based on data analysis.
    """
    # Validate dataset
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this dataset")

    agent = get_dashboard_planner_agent()

    # Just run the data understanding phase
    try:
        profile = await agent._phase_data_understanding(dataset_id)

        return {
            "dataset_id": dataset_id,
            "row_count": profile.row_count,
            "column_count": profile.column_count,
            "suggested_kpi_columns": profile.potential_kpi_columns,
            "suggested_group_by_columns": profile.potential_group_by_columns,
            "numeric_columns": profile.numeric_columns,
            "categorical_columns": profile.categorical_columns,
            "temporal_columns": profile.temporal_columns,
            "columns": [
                {
                    "name": c.name,
                    "type": c.dtype,
                    "is_numeric": c.is_numeric,
                    "is_categorical": c.is_categorical,
                    "is_temporal": c.is_temporal,
                    "unique_count": c.unique_count,
                    "null_percentage": round(c.null_percentage, 1)
                }
                for c in profile.columns
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
