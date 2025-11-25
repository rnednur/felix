from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from app.core.database import get_db
from app.services.deep_research_service import DeepResearchService
from app.services.infographic_service import InfographicService
from app.models.dataset import Dataset
import logging
import json
import asyncio
import base64

logger = logging.getLogger(__name__)

router = APIRouter()


class DeepResearchRequest(BaseModel):
    """Request for deep research analysis"""
    dataset_id: str = Field(..., description="Dataset ID to analyze")
    question: str = Field(..., description="Main research question")
    max_sub_questions: int = Field(default=10, ge=1, le=20, description="Maximum sub-questions to generate")
    enable_python: bool = Field(default=True, description="Enable Python analysis")
    enable_world_knowledge: bool = Field(default=True, description="Enable world knowledge enrichment")
    generate_infographic: bool = Field(default=False, description="Auto-generate infographic")
    infographic_format: str = Field(default='pdf', description="Infographic format if auto-generating")
    infographic_color_scheme: str = Field(default='professional', description="Color scheme if auto-generating")


class DeepResearchResponse(BaseModel):
    """Response from deep research analysis"""
    success: bool
    main_question: str
    direct_answer: str
    key_findings: List[str]
    supporting_details: List[Dict[str, Any]]  # Changed from Dict to List
    data_coverage: Dict[str, Any]
    follow_up_questions: List[str]
    visualizations: List[Dict[str, Any]]
    stages_completed: List[str]  # List of stage names
    execution_time_seconds: float
    error: Optional[str] = None
    infographic: Optional[Dict[str, Any]] = None  # Added: optional infographic data


class PlanRequest(BaseModel):
    """Request for research plan generation"""
    dataset_id: str = Field(..., description="Dataset ID to analyze")
    question: str = Field(..., description="Main research question")
    max_sub_questions: int = Field(default=10, ge=1, le=20, description="Maximum sub-questions to generate")


class PlanResponse(BaseModel):
    """Response containing research plan"""
    success: bool
    main_question: str
    sub_questions: List[Dict[str, Any]]
    estimated_time: str
    research_stages: List[str]
    error: Optional[str] = None


class ExecutePlanRequest(BaseModel):
    """Request to execute research with edited plan"""
    dataset_id: str = Field(..., description="Dataset ID to analyze")
    main_question: str = Field(..., description="Main research question")
    sub_questions: List[Dict[str, Any]] = Field(..., description="User-edited sub-questions")
    enable_python: bool = Field(default=True, description="Enable Python analysis")
    enable_world_knowledge: bool = Field(default=True, description="Enable world knowledge enrichment")
    generate_infographic: bool = Field(default=False, description="Auto-generate infographic")
    infographic_format: str = Field(default='pdf', description="Infographic format if auto-generating")
    infographic_color_scheme: str = Field(default='professional', description="Color scheme if auto-generating")


class InfographicRequest(BaseModel):
    """Request for infographic generation"""
    format: str = Field(default='pdf', description="Output format: 'pdf' or 'png'")
    color_scheme: str = Field(default='professional', description="Color scheme: 'professional', 'modern', or 'corporate'")
    include_charts: bool = Field(default=True, description="Include summary charts")
    include_visualizations: bool = Field(default=True, description="Include data visualizations")


class InfographicResponse(BaseModel):
    """Response from infographic generation"""
    success: bool
    data: str = Field(..., description="Base64 encoded infographic")
    format: str
    filename: str
    size_bytes: int
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

        # Optionally generate infographic
        infographic_data = None
        if request.generate_infographic:
            try:
                logger.info("Auto-generating infographic...")
                infographic_service = InfographicService(template=request.infographic_color_scheme)
                infographic_result = infographic_service.generate_infographic(
                    research_result=result,
                    format=request.infographic_format,
                    include_charts=True,
                    include_visualizations=True
                )
                infographic_data = {
                    'data': infographic_result['data'],
                    'format': infographic_result['format'],
                    'filename': infographic_result['filename'],
                    'size_bytes': infographic_result['size_bytes']
                }
                logger.info(f"Infographic generated: {infographic_result['filename']}")
            except Exception as e:
                logger.error(f"Infographic generation failed: {str(e)}", exc_info=True)
                # Continue without infographic - don't fail the whole request

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
            execution_time_seconds=result['execution_time_seconds'],
            infographic=infographic_data
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


@router.post("/generate-infographic")
async def generate_infographic(
    research_result: Dict[str, Any],
    infographic_request: InfographicRequest = InfographicRequest()
):
    """
    Generate professional infographic from deep research results

    This endpoint takes the output from /analyze and generates a visual infographic.
    Supports PDF and PNG formats with multiple professional color schemes.

    Args:
        research_result: The complete output from /analyze endpoint
        infographic_request: Infographic generation options

    Returns:
        Base64 encoded infographic (PDF or PNG)
    """

    try:
        logger.info(f"Generating {infographic_request.format} infographic with {infographic_request.color_scheme} theme")

        # Initialize infographic service
        infographic_service = InfographicService(template=infographic_request.color_scheme)

        # Generate infographic
        result = infographic_service.generate_infographic(
            research_result=research_result,
            format=infographic_request.format,
            include_charts=infographic_request.include_charts,
            include_visualizations=infographic_request.include_visualizations
        )

        logger.info(f"Infographic generated successfully: {result['filename']} ({result['size_bytes']} bytes)")

        return InfographicResponse(
            success=True,
            data=result['data'],
            format=result['format'],
            filename=result['filename'],
            size_bytes=result['size_bytes']
        )

    except Exception as e:
        logger.error(f"Infographic generation failed: {str(e)}", exc_info=True)
        return InfographicResponse(
            success=False,
            data="",
            format=infographic_request.format,
            filename="",
            size_bytes=0,
            error=str(e)
        )


@router.post("/analyze-with-infographic", response_model=Dict[str, Any])
async def analyze_with_infographic(
    request: DeepResearchRequest,
    infographic_request: InfographicRequest = InfographicRequest(),
    db: Session = Depends(get_db)
):
    """
    Convenience endpoint: Run deep research AND generate infographic in one call

    This combines /analyze and /generate-infographic into a single request.

    Returns both the research results and the generated infographic.
    """

    try:
        # Step 1: Run deep research
        logger.info(f"Running deep research for: {request.question}")

        dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail=f"Dataset {request.dataset_id} not found")

        service = DeepResearchService()
        research_result = await service.research(
            main_question=request.question,
            dataset_id=request.dataset_id,
            max_sub_questions=request.max_sub_questions,
            enable_python=request.enable_python,
            enable_world_knowledge=request.enable_world_knowledge
        )

        # Step 2: Generate infographic
        logger.info("Generating infographic from research results")

        infographic_service = InfographicService(template=infographic_request.color_scheme)
        infographic_result = infographic_service.generate_infographic(
            research_result=research_result,
            format=infographic_request.format,
            include_charts=infographic_request.include_charts,
            include_visualizations=infographic_request.include_visualizations
        )

        logger.info(f"Analysis complete with infographic: {infographic_result['filename']}")

        # Return combined response
        return {
            "success": True,
            "research": {
                "main_question": research_result['main_question'],
                "direct_answer": research_result['direct_answer'],
                "key_findings": research_result['key_findings'],
                "supporting_details": research_result['supporting_details'],
                "data_coverage": research_result['data_coverage'],
                "follow_up_questions": research_result['follow_up_questions'],
                "visualizations": research_result.get('visualizations', []),
                "stages_completed": research_result['stages_completed'],
                "execution_time_seconds": research_result['execution_time_seconds']
            },
            "infographic": {
                "data": infographic_result['data'],
                "format": infographic_result['format'],
                "filename": infographic_result['filename'],
                "size_bytes": infographic_result['size_bytes']
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis with infographic failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plan", response_model=PlanResponse)
async def create_research_plan(
    request: PlanRequest,
    db: Session = Depends(get_db)
):
    """
    Generate research plan without executing

    Returns decomposed sub-questions for user review and editing.
    This allows users to see and modify the research plan before execution.
    """

    try:
        # Verify dataset exists
        dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail=f"Dataset {request.dataset_id} not found")

        logger.info(f"Generating research plan for: {request.question}")

        # Initialize service
        service = DeepResearchService()

        # Load schema
        schema = service.storage_service.load_schema(request.dataset_id)

        # Decompose question into sub-questions
        sub_questions = await service._decompose_question(
            request.question,
            schema,
            request.max_sub_questions
        )

        logger.info(f"Generated {len(sub_questions)} sub-questions")

        # Format response
        return PlanResponse(
            success=True,
            main_question=request.question,
            sub_questions=[
                {
                    "id": f"sq_{i}",
                    "question": sq.question,
                    "intent_type": sq.intent_type,
                    "desired_output": sq.desired_output,
                    "priority": sq.priority,
                    "editable": True
                }
                for i, sq in enumerate(sub_questions)
            ],
            estimated_time=f"{len(sub_questions) * 2}s",
            research_stages=[
                "Research Websites",
                "Analyze Results",
                "Create Report"
            ]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Plan generation failed: {str(e)}", exc_info=True)
        return PlanResponse(
            success=False,
            main_question=request.question,
            sub_questions=[],
            estimated_time="0s",
            research_stages=[],
            error=str(e)
        )


@router.post("/execute-plan", response_model=DeepResearchResponse)
async def execute_research_plan(
    request: ExecutePlanRequest,
    db: Session = Depends(get_db)
):
    """
    Execute research with user-edited plan

    Takes the edited plan from the user and executes the research,
    skipping the decomposition stage since we already have the sub-questions.
    """

    try:
        # Verify dataset exists
        dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail=f"Dataset {request.dataset_id} not found")

        logger.info(f"Executing research plan for: {request.main_question}")

        # Initialize service
        service = DeepResearchService()

        # Load schema
        schema = service.storage_service.load_schema(request.dataset_id)

        # Convert sub_questions dict back to SubQuestion objects
        from app.services.deep_research_service import SubQuestion
        sub_questions = [
            SubQuestion(
                question=sq['question'],
                intent_type=sq.get('intent_type', 'descriptive'),
                desired_output=sq.get('desired_output', 'table'),
                priority=sq.get('priority', 2)
            )
            for sq in request.sub_questions
        ]

        logger.info(f"Executing with {len(sub_questions)} sub-questions")

        # Execute research pipeline starting from classification
        # (skip decomposition since we have user-edited sub-questions)

        # Stage 2: Classification & Schema Mapping
        classified = await service._classify_and_map(sub_questions, schema)

        # Stage 3: Query Execution
        results = await service._execute_queries(
            classified,
            request.dataset_id,
            schema,
            request.enable_python
        )

        # Stage 4: World Knowledge Enrichment
        world_knowledge = {}
        if request.enable_world_knowledge:
            world_knowledge = await service._enrich_world_knowledge(classified, results)

        # Stage 5: Synthesis & Insight Generation
        synthesis = await service._synthesize_insights(
            request.main_question,
            sub_questions,
            classified,
            results,
            world_knowledge,
            schema
        )

        # Stage 6: Follow-up Questions
        follow_ups = await service._suggest_follow_ups(
            request.main_question,
            synthesis,
            schema
        )

        # Extract follow-up questions
        follow_up_questions = []
        if isinstance(follow_ups, list):
            for item in follow_ups:
                if isinstance(item, dict):
                    follow_up_questions.append(item.get('question', str(item)))
                else:
                    follow_up_questions.append(str(item))

        # Collect visualizations
        visualizations = []
        for r in results:
            if r.success and r.visualization:
                viz_list = r.visualization if isinstance(r.visualization, list) else [r.visualization]
                for viz in viz_list:
                    visualizations.append({
                        'question': r.question,
                        'type': viz.get('type', 'image'),
                        'format': viz.get('format', 'png'),
                        'data': viz.get('data'),
                        'caption': r.question
                    })

        # Build data coverage
        data_coverage = {
            'questions_answered': sum(1 for r in results if r.success),
            'total_questions': len(sub_questions),
            'gaps': synthesis.get('gaps', []),
            'methods_used': list(set(r.method for r in results))
        }

        # Generate infographic if requested
        infographic_data = None
        if request.generate_infographic:
            try:
                logger.info("Auto-generating infographic...")
                infographic_service = InfographicService(template=request.infographic_color_scheme)

                result_for_infographic = {
                    'research_id': f"plan_exec_{int(datetime.utcnow().timestamp())}",
                    'main_question': request.main_question,
                    'sub_questions_count': len(sub_questions),
                    'direct_answer': synthesis.get('direct_answer', ''),
                    'key_findings': synthesis.get('key_findings', []),
                    'supporting_details': synthesis.get('supporting_details', {}),
                    'data_coverage': data_coverage,
                    'follow_up_questions': follow_up_questions,
                    'visualizations': visualizations,
                    'stages_completed': [
                        'Question decomposition (user-edited)',
                        'Schema mapping',
                        'Query execution',
                        'Knowledge enrichment' if request.enable_world_knowledge else 'Knowledge enrichment (skipped)',
                        'Insight synthesis',
                        'Follow-up generation'
                    ],
                    'execution_time_seconds': 0
                }

                infographic_result = infographic_service.generate_infographic(
                    research_result=result_for_infographic,
                    format=request.infographic_format,
                    include_charts=True,
                    include_visualizations=True
                )
                infographic_data = {
                    'data': infographic_result['data'],
                    'format': infographic_result['format'],
                    'filename': infographic_result['filename'],
                    'size_bytes': infographic_result['size_bytes']
                }
                logger.info(f"Infographic generated: {infographic_result['filename']}")
            except Exception as e:
                logger.error(f"Infographic generation failed: {str(e)}", exc_info=True)

        logger.info(f"Plan execution complete")

        # Return response
        return DeepResearchResponse(
            success=True,
            main_question=request.main_question,
            direct_answer=synthesis.get('direct_answer', 'Analysis complete'),
            key_findings=synthesis.get('key_findings', []),
            supporting_details=synthesis.get('supporting_details', []),
            data_coverage=data_coverage,
            follow_up_questions=follow_up_questions,
            visualizations=visualizations,
            stages_completed=[
                'Question decomposition (user-edited)',
                'Schema mapping',
                'Query execution',
                'Knowledge enrichment' if request.enable_world_knowledge else 'Knowledge enrichment (skipped)',
                'Insight synthesis',
                'Follow-up generation'
            ],
            execution_time_seconds=0,
            infographic=infographic_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Plan execution failed: {str(e)}", exc_info=True)
        return DeepResearchResponse(
            success=False,
            main_question=request.main_question,
            direct_answer="",
            key_findings=[],
            supporting_details=[],
            data_coverage={},
            follow_up_questions=[],
            visualizations=[],
            stages_completed=[],
            execution_time_seconds=0,
            error=str(e)
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "deep_research"}
