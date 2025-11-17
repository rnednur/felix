from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from app.core.database import get_db
from app.services.deep_research_service import DeepResearchService
from app.models.dataset import Dataset
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


class DeepResearchRequest(BaseModel):
    """Request for deep research analysis"""
    dataset_id: str = Field(..., description="Dataset ID to analyze")
    question: str = Field(..., description="Main research question")
    max_sub_questions: int = Field(default=10, ge=1, le=20, description="Maximum sub-questions to generate")
    enable_python: bool = Field(default=True, description="Enable Python analysis")
    enable_world_knowledge: bool = Field(default=True, description="Enable world knowledge enrichment")


class DeepResearchResponse(BaseModel):
    """Response from deep research analysis"""
    success: bool
    main_question: str
    direct_answer: str
    key_findings: List[str]
    supporting_details: Dict[str, Any]
    data_coverage: Dict[str, Any]
    follow_up_questions: List[str]
    visualizations: List[Dict[str, Any]]
    stages_completed: List[str]
    execution_time_seconds: float
    error: Optional[str] = None


@router.post("/analyze", response_model=DeepResearchResponse)
async def deep_research_analyze(
    request: DeepResearchRequest,
    db: Session = Depends(get_db)
):
    """
    Perform deep research analysis on a dataset using multi-stage pipeline:

    1. Question Understanding & Decomposition
    2. Question Classification & Schema Mapping
    3. Query Execution (SQL + Python orchestration)
    4. World Knowledge Enrichment
    5. Synthesis & Insight Generation
    6. Follow-up Question Suggestions
    """

    try:
        # Verify dataset exists
        dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail=f"Dataset {request.dataset_id} not found")

        logger.info(f"Starting deep research for dataset {request.dataset_id}: {request.question}")

        # Initialize service
        service = DeepResearchService()

        # Execute deep research
        result = await service.research(
            main_question=request.question,
            dataset_id=request.dataset_id,
            max_sub_questions=request.max_sub_questions,
            enable_python=request.enable_python,
            enable_world_knowledge=request.enable_world_knowledge
        )

        logger.info(f"Deep research completed in {result.get('execution_time_seconds', 0):.2f}s")

        return DeepResearchResponse(
            success=True,
            main_question=result['main_question'],
            direct_answer=result['direct_answer'],
            key_findings=result['key_findings'],
            supporting_details=result['supporting_details'],
            data_coverage=result['data_coverage'],
            follow_up_questions=result['follow_up_questions'],
            visualizations=result.get('visualizations', []),
            stages_completed=result['stages_completed'],
            execution_time_seconds=result['execution_time_seconds']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deep research failed: {str(e)}", exc_info=True)
        return DeepResearchResponse(
            success=False,
            main_question=request.question,
            direct_answer="",
            key_findings=[],
            supporting_details={},
            data_coverage={},
            follow_up_questions=[],
            visualizations=[],
            stages_completed=[],
            execution_time_seconds=0,
            error=str(e)
        )


@router.get("/analyze-stream")
async def deep_research_analyze_stream(
    dataset_id: str,
    question: str,
    max_sub_questions: int = 10,
    enable_python: bool = True,
    enable_world_knowledge: bool = True,
    db: Session = Depends(get_db)
):
    """
    Stream deep research progress using Server-Sent Events
    """

    # Verify dataset exists
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")

    async def event_generator():
        """Generate SSE events for progress updates"""
        progress_queue = asyncio.Queue()

        async def progress_callback(stage: int, message: str):
            """Callback to send progress updates"""
            await progress_queue.put({
                'stage': stage,
                'message': message,
                'total_stages': 6
            })

        # Start research in background task
        async def run_research():
            try:
                service = DeepResearchService()
                result = await service.research(
                    main_question=question,
                    dataset_id=dataset_id,
                    max_sub_questions=max_sub_questions,
                    enable_python=enable_python,
                    enable_world_knowledge=enable_world_knowledge,
                    progress_callback=progress_callback
                )
                # Send final result
                await progress_queue.put({'type': 'complete', 'result': result})
            except Exception as e:
                logger.error(f"Deep research error: {str(e)}", exc_info=True)
                await progress_queue.put({'type': 'error', 'error': str(e)})
            finally:
                await progress_queue.put(None)  # Signal completion

        # Start research task
        research_task = asyncio.create_task(run_research())

        # Stream progress updates
        try:
            while True:
                update = await progress_queue.get()
                if update is None:
                    break

                yield f"data: {json.dumps(update)}\n\n"
        finally:
            # Ensure task is cancelled if client disconnects
            if not research_task.done():
                research_task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "deep_research"}
