"""
Annotation API endpoints for dashboard editing
"""
import logging
from fastapi import APIRouter, HTTPException
from app.schemas.annotation import (
    AnnotationRequest,
    AnnotationResponse,
    DashboardEdit,
    AnnotationBatchRequest,
    AnnotationBatchResponse,
    ContextCreateRequest
)
from app.services.agents.dashboard_editor_agent import DashboardEditorAgent
from app.schemas.agent import AgentConfig

router = APIRouter(prefix="/annotations", tags=["annotations"])
logger = logging.getLogger(__name__)


def get_dashboard_editor_agent() -> DashboardEditorAgent:
    """
    Get or create a DashboardEditorAgent instance
    """
    # Create minimal config for the agent
    config = AgentConfig(
        name="dashboard_editor_agent",
        display_name="Dashboard Editor",
        description="Interprets annotations and generates dashboard modifications",
        tier="free",
        enabled=True,
        capabilities=[
            "interpret_annotations",
            "generate_edits",
            "modify_charts",
            "modify_kpis",
            "modify_insights"
        ],
        libraries=[],
        intent_keywords=[
            "change", "modify", "update", "edit",
            "make", "convert", "transform",
            "color", "style", "font",
            "chart", "bar", "line", "pie",
            "remove", "delete", "hide"
        ]
    )
    return DashboardEditorAgent(config)


@router.post("", response_model=AnnotationResponse)
async def process_annotation(
    annotation: AnnotationRequest
):
    """
    Process a single annotation and return edit instructions

    This endpoint receives annotation data from the frontend (element selector,
    type, config, and user feedback) and uses the DashboardEditorAgent to
    interpret the feedback and generate structured edit instructions.

    Args:
        annotation: AnnotationRequest with element info and user feedback

    Returns:
        AnnotationResponse with success status and DashboardEdit
    """
    try:
        logger.info(f"[Annotations API] Received annotation request")
        logger.info(f"[Annotations API] Element type: {annotation.element_type}")
        logger.info(f"[Annotations API] Element selector: {annotation.element_selector}")
        logger.info(f"[Annotations API] Feedback: {annotation.feedback}")

        # Get the dashboard editor agent
        agent = get_dashboard_editor_agent()

        # Process the annotation
        edit = await agent.process_annotation(annotation)

        return AnnotationResponse(
            success=True,
            edit=edit,
            message=f"Successfully processed annotation for {annotation.element_type}"
        )

    except ValueError as e:
        logger.warning(f"Invalid annotation request: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Failed to process annotation: {e}", exc_info=True)
        return AnnotationResponse(
            success=False,
            edit=None,
            message=f"Failed to process annotation: {str(e)}"
        )


@router.post("/batch", response_model=AnnotationBatchResponse)
async def process_annotation_batch(
    batch_request: AnnotationBatchRequest
):
    """
    Process multiple annotations in batch

    Useful for applying multiple changes at once (batch edit mode).

    Args:
        batch_request: AnnotationBatchRequest with list of annotations

    Returns:
        AnnotationBatchResponse with list of edits and any errors
    """
    try:
        logger.info(f"Processing batch of {len(batch_request.annotations)} annotations")

        agent = get_dashboard_editor_agent()
        edits: list[DashboardEdit] = []
        errors: list[str] = []

        for i, annotation in enumerate(batch_request.annotations):
            try:
                edit = await agent.process_annotation(annotation)
                edits.append(edit)
            except Exception as e:
                error_msg = f"Annotation {i + 1} failed: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)

        return AnnotationBatchResponse(
            success=len(errors) == 0,
            edits=edits,
            errors=errors
        )

    except Exception as e:
        logger.error(f"Batch annotation processing failed: {e}", exc_info=True)
        return AnnotationBatchResponse(
            success=False,
            edits=[],
            errors=[str(e)]
        )


@router.post("/create-from-context", response_model=AnnotationResponse)
async def create_from_context(
    request: ContextCreateRequest
):
    """
    Create a new element using full dashboard context

    This endpoint allows creating elements with access to all KPIs, charts,
    and dataset information. Use this when clicking on empty dashboard space
    to create new elements that reference existing data.

    Example requests:
    - "Create a bar chart comparing all KPIs"
    - "Add a pie chart showing the distribution of values"
    - "Generate an insight summarizing all metrics"

    Args:
        request: ContextCreateRequest with feedback and full dashboard context

    Returns:
        AnnotationResponse with the new element to add
    """
    try:
        logger.info(f"[Context Create] Received request: {request.feedback}")
        logger.info(f"[Context Create] Context - KPIs: {len(request.context.kpis)}, Charts: {len(request.context.charts)}")

        agent = get_dashboard_editor_agent()

        # Process with full context
        edit = await agent.create_from_context(request)

        return AnnotationResponse(
            success=True,
            edit=edit,
            message=f"Successfully created new element based on dashboard context"
        )

    except ValueError as e:
        logger.warning(f"Invalid context create request: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        logger.error(f"Failed to create from context: {e}", exc_info=True)
        return AnnotationResponse(
            success=False,
            edit=None,
            message=f"Failed to create element: {str(e)}"
        )


@router.get("/supported-intents")
async def get_supported_intents():
    """
    Get list of supported annotation intents

    Returns documentation about what types of edits the system can understand.
    """
    return {
        "intents": [
            {
                "type": "change_chart_type",
                "description": "Change visualization type (e.g., bar to line chart)",
                "examples": [
                    "Convert this to a line chart",
                    "Make this a pie chart",
                    "Show as scatter plot"
                ],
                "supported_elements": ["chart"]
            },
            {
                "type": "modify_styling",
                "description": "Change colors, fonts, sizes, or visual appearance",
                "examples": [
                    "Make this blue",
                    "Use larger font",
                    "Change the colors to match our brand"
                ],
                "supported_elements": ["chart", "kpi", "insight", "table", "map"]
            },
            {
                "type": "update_data",
                "description": "Change data displayed (filters, aggregations)",
                "examples": [
                    "Only show top 10",
                    "Filter to show only Q4 data",
                    "Group by month instead of day"
                ],
                "supported_elements": ["chart", "table", "kpi"]
            },
            {
                "type": "reword_insight",
                "description": "Change text content for insights and notes",
                "examples": [
                    "Make this more concise",
                    "Add specific numbers",
                    "Rewrite in bullet points"
                ],
                "supported_elements": ["insight"]
            },
            {
                "type": "remove_element",
                "description": "Remove element from dashboard",
                "examples": [
                    "Remove this",
                    "Delete this chart",
                    "Hide this KPI"
                ],
                "supported_elements": ["chart", "kpi", "insight", "table", "map", "code"]
            },
            {
                "type": "resize_element",
                "description": "Make element larger or smaller",
                "examples": [
                    "Make this bigger",
                    "Reduce size",
                    "Expand to full width"
                ],
                "supported_elements": ["chart", "kpi", "insight", "table", "map"]
            }
        ]
    }
