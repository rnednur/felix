from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.core.database import get_db
from app.services.deep_research_service import DeepResearchService
from app.services.infographic_service import InfographicService
from app.services.research_persistence_service import ResearchPersistenceService
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
    verbose_mode: bool = Field(default=True, description="Generate comprehensive multi-page analysis")
    generate_infographic: bool = Field(default=False, description="Auto-generate infographic")
    infographic_format: str = Field(default='pdf', description="Infographic format: 'pdf' or 'png'")
    infographic_color_scheme: str = Field(default='professional', description="Color scheme: 'professional', 'modern', or 'corporate'")
    infographic_generation_method: str = Field(default='template', description="Generation method: 'template' (free) or 'ai' (Gemini Nano Banana Pro, paid)")


class DeepResearchResponse(BaseModel):
    """Response from deep research analysis"""
    success: bool
    main_question: str
    direct_answer: str
    key_findings: List[str]
    supporting_details: List[Dict[str, Any]]
    data_coverage: Dict[str, Any]
    follow_up_questions: List[str]
    visualizations: List[Dict[str, Any]]
    stages_completed: List[str]
    execution_time_seconds: float
    error: Optional[str] = None
    infographic: Optional[Dict[str, Any]] = None

    # Verbose mode fields
    executive_summary: Optional[str] = None
    methodology: Optional[Dict[str, Any]] = None
    detailed_findings: Optional[List[Dict[str, Any]]] = None
    cross_analysis: Optional[Dict[str, Any]] = None
    limitations: Optional[List[Any]] = None  # Can be List[str] or List[Dict] depending on LLM response
    recommendations: Optional[List[Dict[str, Any]]] = None
    technical_appendix: Optional[Dict[str, Any]] = None


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
    verbose_mode: bool = Field(default=True, description="Generate comprehensive multi-page analysis")
    generate_infographic: bool = Field(default=False, description="Auto-generate infographic")
    infographic_format: str = Field(default='pdf', description="Infographic format: 'pdf' or 'png'")
    infographic_color_scheme: str = Field(default='professional', description="Color scheme: 'professional', 'modern', or 'corporate'")
    infographic_generation_method: str = Field(default='template', description="Generation method: 'template' (free) or 'ai' (Gemini Nano Banana Pro, paid)")


class InfographicRequest(BaseModel):
    """Request for infographic generation"""
    format: str = Field(default='pdf', description="Output format: 'pdf' or 'png'")
    color_scheme: str = Field(default='professional', description="Color scheme: 'professional', 'modern', or 'corporate'")
    generation_method: str = Field(default='template', description="Generation method: 'template' (free) or 'ai' (Gemini Nano Banana Pro, paid)")
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
        logger.info(f"🔍 VERBOSE MODE: {request.verbose_mode}")

        # Initialize service
        service = DeepResearchService()

        # Execute deep research
        result = await service.research(
            main_question=request.question,
            dataset_id=request.dataset_id,
            max_sub_questions=request.max_sub_questions,
            enable_python=request.enable_python,
            enable_world_knowledge=request.enable_world_knowledge,
            verbose_mode=request.verbose_mode
        )

        logger.info(f"Deep research completed in {result.get('execution_time_seconds', 0):.2f}s")
        logger.info(f"📦 Result keys from service: {list(result.keys())}")

        # Save research to filesystem for later retrieval
        try:
            persistence = ResearchPersistenceService()
            research_id = persistence.save_research(
                dataset_id=request.dataset_id,
                research_result=result,
                metadata={
                    'verbose_mode': request.verbose_mode,
                    'enable_python': request.enable_python,
                    'enable_world_knowledge': request.enable_world_knowledge
                }
            )
            logger.info(f"💾 Research saved: {research_id}")
        except Exception as e:
            logger.error(f"Failed to save research: {str(e)}")
            # Don't fail the request if save fails

        # Check if verbose fields are present
        verbose_fields_present = [
            'executive_summary', 'methodology', 'detailed_findings',
            'cross_analysis', 'limitations', 'recommendations', 'technical_appendix'
        ]
        verbose_in_result = [f for f in verbose_fields_present if f in result]
        if verbose_in_result:
            logger.info(f"✅ Verbose fields found in result: {verbose_in_result}")
        else:
            logger.warning(f"⚠️ No verbose fields found in result despite verbose_mode={request.verbose_mode}")

        # Optionally generate infographic
        infographic_data = None
        if request.generate_infographic:
            try:
                logger.info(f"Auto-generating infographic using {request.infographic_generation_method} method...")
                infographic_service = InfographicService(template=request.infographic_color_scheme)
                infographic_result = infographic_service.generate_infographic(
                    research_result=result,
                    format=request.infographic_format,
                    include_charts=True,
                    include_visualizations=True,
                    generation_method=request.infographic_generation_method
                )
                infographic_data = {
                    'data': infographic_result['data'],
                    'format': infographic_result['format'],
                    'filename': infographic_result['filename'],
                    'size_bytes': infographic_result['size_bytes']
                }
                if request.infographic_generation_method == 'ai':
                    infographic_data['generation_method'] = 'ai'
                    infographic_data['model'] = 'google/gemini-3-pro-image-preview'
                logger.info(f"Infographic generated: {infographic_result['filename']}")
            except Exception as e:
                logger.error(f"Infographic generation failed: {str(e)}", exc_info=True)
                # Continue without infographic - don't fail the whole request

        # Build response with verbose fields if present
        response_data = {
            'success': True,
            'main_question': result['main_question'],
            'direct_answer': result['direct_answer'],
            'key_findings': result['key_findings'],
            'supporting_details': result['supporting_details'],
            'data_coverage': result['data_coverage'],
            'follow_up_questions': result['follow_up_questions'],
            'visualizations': result.get('visualizations', []),
            'stages_completed': result['stages_completed'],
            'execution_time_seconds': result['execution_time_seconds'],
            'infographic': infographic_data
        }

        # Add verbose fields if they exist in result
        if request.verbose_mode:
            verbose_mapping = {
                'executive_summary': result.get('executive_summary'),
                'methodology': result.get('methodology'),
                'detailed_findings': result.get('detailed_findings'),
                'cross_analysis': result.get('cross_analysis'),
                'limitations': result.get('limitations'),
                'recommendations': result.get('recommendations'),
                'technical_appendix': result.get('technical_appendix')
            }
            response_data.update(verbose_mapping)
            logger.info(f"📝 Adding verbose fields to response: {[k for k, v in verbose_mapping.items() if v is not None]}")

        return DeepResearchResponse(**response_data)

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
        logger.info(f"Generating {infographic_request.format} infographic with {infographic_request.color_scheme} theme using {infographic_request.generation_method} method")

        # Initialize infographic service
        infographic_service = InfographicService(template=infographic_request.color_scheme)

        # Generate infographic
        result = infographic_service.generate_infographic(
            research_result=research_result,
            format=infographic_request.format,
            include_charts=infographic_request.include_charts,
            include_visualizations=infographic_request.include_visualizations,
            generation_method=infographic_request.generation_method
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
        logger.info(f"Generating infographic from research results using {infographic_request.generation_method} method")

        infographic_service = InfographicService(template=infographic_request.color_scheme)
        infographic_result = infographic_service.generate_infographic(
            research_result=research_result,
            format=infographic_request.format,
            include_charts=infographic_request.include_charts,
            include_visualizations=infographic_request.include_visualizations,
            generation_method=infographic_request.generation_method
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

        # Stage 7: Generate Verbose Analysis (if requested)
        verbose_analysis = {}
        if request.verbose_mode:
            logger.info(f"🔍 VERBOSE MODE ENABLED in execute-plan - generating comprehensive analysis...")
            try:
                verbose_analysis = await service._generate_verbose_analysis(
                    request.main_question,
                    sub_questions,
                    classified,
                    results,
                    world_knowledge,
                    synthesis,
                    schema
                )
                logger.info(f"✅ Verbose analysis generated with sections: {list(verbose_analysis.keys())}")
            except Exception as e:
                logger.error(f"❌ Verbose analysis generation failed: {str(e)}", exc_info=True)

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
                    include_visualizations=True,
                    generation_method=request.infographic_generation_method
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

        # Build complete result dict for saving
        complete_result = {
            'research_id': f"plan_exec_{int(datetime.utcnow().timestamp())}",
            'main_question': request.main_question,
            'sub_questions_count': len(sub_questions),
            'direct_answer': synthesis.get('direct_answer', 'Analysis complete'),
            'key_findings': synthesis.get('key_findings', []),
            'supporting_details': synthesis.get('supporting_details', []),
            'data_coverage': data_coverage,
            'follow_up_questions': follow_up_questions,
            'visualizations': visualizations,
            'stages_completed': [
                'Question decomposition (user-edited)',
                'Schema mapping',
                'Query execution',
                'Knowledge enrichment' if request.enable_world_knowledge else 'Knowledge enrichment (skipped)',
                'Insight synthesis',
                'Follow-up generation',
                'Verbose analysis generation' if request.verbose_mode and verbose_analysis else None
            ],
            'execution_time_seconds': 0
        }

        # Add verbose fields if generated
        if request.verbose_mode and verbose_analysis:
            complete_result.update(verbose_analysis)

        # Save research to filesystem
        try:
            persistence = ResearchPersistenceService()
            research_id = persistence.save_research(
                dataset_id=request.dataset_id,
                research_result=complete_result,
                metadata={
                    'source': 'execute_plan',
                    'verbose_mode': request.verbose_mode,
                    'enable_python': request.enable_python,
                    'enable_world_knowledge': request.enable_world_knowledge
                }
            )
            logger.info(f"💾 Research saved: {research_id}")
        except Exception as e:
            logger.error(f"Failed to save research: {str(e)}")

        # Build response data with verbose fields if present
        response_data = {
            'success': True,
            'main_question': request.main_question,
            'direct_answer': synthesis.get('direct_answer', 'Analysis complete'),
            'key_findings': synthesis.get('key_findings', []),
            'supporting_details': synthesis.get('supporting_details', []),
            'data_coverage': data_coverage,
            'follow_up_questions': follow_up_questions,
            'visualizations': visualizations,
            'stages_completed': [
                'Question decomposition (user-edited)',
                'Schema mapping',
                'Query execution',
                'Knowledge enrichment' if request.enable_world_knowledge else 'Knowledge enrichment (skipped)',
                'Insight synthesis',
                'Follow-up generation',
                'Verbose analysis generation' if request.verbose_mode and verbose_analysis else None
            ],
            'execution_time_seconds': 0,
            'infographic': infographic_data
        }

        # Filter out None from stages_completed
        response_data['stages_completed'] = [s for s in response_data['stages_completed'] if s is not None]

        # Add verbose fields if they exist
        if request.verbose_mode and verbose_analysis:
            verbose_mapping = {
                'executive_summary': verbose_analysis.get('executive_summary'),
                'methodology': verbose_analysis.get('methodology'),
                'detailed_findings': verbose_analysis.get('detailed_findings'),
                'cross_analysis': verbose_analysis.get('cross_analysis'),
                'limitations': verbose_analysis.get('limitations'),
                'recommendations': verbose_analysis.get('recommendations'),
                'technical_appendix': verbose_analysis.get('technical_appendix')
            }
            response_data.update(verbose_mapping)
            logger.info(f"📝 Adding verbose fields to execute-plan response: {[k for k, v in verbose_mapping.items() if v is not None]}")

        # Return response
        return DeepResearchResponse(**response_data)

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


@router.get("/history")
async def list_research_history(
    dataset_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List saved research jobs

    Query Parameters:
    - dataset_id: Filter by dataset (optional)
    - limit: Maximum number of results (default: 50)
    """
    try:
        persistence = ResearchPersistenceService()
        jobs = persistence.list_research_jobs(dataset_id=dataset_id, limit=limit)

        return {
            "success": True,
            "count": len(jobs),
            "jobs": jobs
        }

    except Exception as e:
        logger.error(f"Failed to list research history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{research_id}")
async def get_research_by_id(
    research_id: str,
    db: Session = Depends(get_db)
):
    """
    Load a specific saved research job

    Returns the complete research result with all verbose sections
    """
    try:
        persistence = ResearchPersistenceService()
        record = persistence.load_research(research_id)

        if not record:
            raise HTTPException(status_code=404, detail=f"Research {research_id} not found")

        return {
            "success": True,
            **record
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load research {research_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{research_id}")
async def delete_research_by_id(
    research_id: str,
    db: Session = Depends(get_db)
):
    """Delete a saved research job"""
    try:
        persistence = ResearchPersistenceService()
        deleted = persistence.delete_research(research_id)

        if not deleted:
            raise HTTPException(status_code=404, detail=f"Research {research_id} not found")

        return {
            "success": True,
            "message": f"Research {research_id} deleted"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete research {research_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_research(
    q: str,
    dataset_id: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Search research jobs by question or findings

    Query Parameters:
    - q: Search query
    - dataset_id: Filter by dataset (optional)
    - limit: Maximum results (default: 20)
    """
    try:
        persistence = ResearchPersistenceService()
        results = persistence.search_research(
            query=q,
            dataset_id=dataset_id,
            limit=limit
        )

        return {
            "success": True,
            "query": q,
            "count": len(results),
            "results": results
        }

    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "deep_research"}


# ============================================================================
# ASYNC JOB ENDPOINTS
# ============================================================================

class AsyncResearchRequest(BaseModel):
    """Request for async deep research analysis"""
    dataset_id: str = Field(..., description="Dataset ID to analyze")
    question: str = Field(..., description="Main research question")
    verbose: int = Field(default=0, ge=0, le=1, description="Verbose mode: 0=off, 1=on")


class AsyncResearchResponse(BaseModel):
    """Response from async research submission"""
    success: bool
    job_id: str
    message: str
    status: str


class JobStatusResponse(BaseModel):
    """Response for job status check"""
    success: bool
    job_id: str
    status: str  # pending, running, completed, failed, cancelled
    current_stage: Optional[str] = None
    progress_percentage: int
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_seconds: Optional[int] = None


@router.post("/jobs/submit", response_model=AsyncResearchResponse)
async def submit_research_job(
    request: AsyncResearchRequest,
    db: Session = Depends(get_db)
):
    """
    Submit a deep research job for async execution

    Returns immediately with a job ID.
    Use GET /jobs/{job_id} to check status and get results.
    """
    try:
        from app.models.research_job import ResearchJob, ResearchJobStatus
        from app.tasks.research_tasks import run_deep_research
        import uuid

        # Validate dataset exists
        dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail=f"Dataset {request.dataset_id} not found")

        # Create job record
        job_id = str(uuid.uuid4())
        job = ResearchJob(
            id=job_id,
            dataset_id=request.dataset_id,
            main_question=request.question,
            verbose_mode=request.verbose,
            status=ResearchJobStatus.PENDING,
            job_metadata={"submitted_via": "api"}
        )
        db.add(job)
        db.commit()

        # Submit to Celery
        task = run_deep_research.apply_async(
            args=[job_id, request.dataset_id, request.question, request.verbose],
            task_id=job_id  # Use job_id as celery task_id for easier tracking
        )

        # Update job with celery task ID
        job.celery_task_id = task.id
        db.commit()

        logger.info(f"Submitted research job {job_id} for dataset {request.dataset_id}")

        return AsyncResearchResponse(
            success=True,
            job_id=job_id,
            message="Research job submitted successfully",
            status="pending"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit research job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get status and results of a research job

    Returns:
    - status: pending, running, completed, failed, cancelled
    - progress_percentage: 0-100
    - result: Full research result (only when status=completed)
    - error_message: Error details (only when status=failed)
    """
    try:
        from app.models.research_job import ResearchJob

        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return JobStatusResponse(
            success=True,
            job_id=job.id,
            status=job.status.value,
            current_stage=job.current_stage,
            progress_percentage=job.progress_percentage,
            result=job.result,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            execution_time_seconds=job.execution_time_seconds
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Cancel a running research job

    Note: This will attempt to revoke the Celery task.
    Jobs that are already in progress may not cancel immediately.
    """
    try:
        from app.models.research_job import ResearchJob, ResearchJobStatus
        from app.core.celery_app import celery_app

        job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # Can only cancel pending or running jobs
        if job.status in [ResearchJobStatus.COMPLETED, ResearchJobStatus.FAILED, ResearchJobStatus.CANCELLED]:
            return {
                "success": False,
                "message": f"Cannot cancel job with status: {job.status.value}"
            }

        # Revoke the Celery task
        if job.celery_task_id:
            celery_app.control.revoke(job.celery_task_id, terminate=True)

        # Update job status
        job.status = ResearchJobStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        if job.started_at:
            job.execution_time_seconds = int((job.completed_at - job.started_at).total_seconds())
        db.commit()

        logger.info(f"Cancelled job {job_id}")

        return {
            "success": True,
            "message": "Job cancelled successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def list_jobs(
    dataset_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List research jobs with optional filters

    Query Parameters:
    - dataset_id: Filter by dataset
    - status: Filter by status (pending, running, completed, failed, cancelled)
    - limit: Maximum number of results (default: 50)
    """
    try:
        from app.models.research_job import ResearchJob, ResearchJobStatus

        query = db.query(ResearchJob)

        if dataset_id:
            query = query.filter(ResearchJob.dataset_id == dataset_id)

        if status:
            try:
                status_enum = ResearchJobStatus(status)
                query = query.filter(ResearchJob.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        jobs = query.order_by(ResearchJob.created_at.desc()).limit(limit).all()

        return {
            "success": True,
            "count": len(jobs),
            "jobs": [
                {
                    "job_id": job.id,
                    "dataset_id": job.dataset_id,
                    "main_question": job.main_question,
                    "status": job.status.value,
                    "progress_percentage": job.progress_percentage,
                    "current_stage": job.current_stage,
                    "created_at": job.created_at.isoformat(),
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "execution_time_seconds": job.execution_time_seconds,
                    "has_result": job.result is not None,
                    "error_message": job.error_message
                }
                for job in jobs
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list jobs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PRESENTATION GENERATION
# ============================================================================

class PresentationRequest(BaseModel):
    """Request for PowerPoint generation"""
    research_id: Optional[str] = Field(None, description="Research ID to load from history")
    research_result: Optional[Dict[str, Any]] = Field(None, description="Research result data")
    theme: str = Field(default="professional", description="Color theme: professional, modern, corporate, vibrant")
    include_verbose: bool = Field(default=False, description="Include verbose analysis sections")


@router.post("/generate-presentation")
async def generate_presentation(
    request: PresentationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate PowerPoint presentation from research results

    Provide either research_id (to load from history) or research_result (direct data)
    """
    try:
        from app.services.presentation_service import PresentationService
        from app.services.research_persistence_service import ResearchPersistenceService

        # Get research data
        if request.research_id:
            # Load from history
            persistence = ResearchPersistenceService()
            research_data = persistence.load_research(request.research_id)
            if not research_data:
                raise HTTPException(status_code=404, detail=f"Research {request.research_id} not found")
        elif request.research_result:
            research_data = request.research_result
        else:
            raise HTTPException(
                status_code=400,
                detail="Either research_id or research_result must be provided"
            )

        # Generate presentation using Gemini 2.0
        ppt_service = PresentationService()
        output_path = await ppt_service.generate_presentation(
            research_result=research_data,
            theme=request.theme,
            include_verbose=request.include_verbose
        )

        # Read file for download
        with open(output_path, 'rb') as f:
            ppt_data = f.read()

        import base64
        ppt_base64 = base64.b64encode(ppt_data).decode('utf-8')

        return {
            "success": True,
            "message": "Presentation generated successfully",
            "file_path": output_path,
            "file_name": output_path.split('/')[-1],
            "file_size": len(ppt_data),
            "data": ppt_base64,
            "theme": request.theme
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate presentation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download-presentation/{filename}")
async def download_presentation(filename: str):
    """Download generated PowerPoint file"""
    try:
        import os
        file_path = f"data/presentations/{filename}"

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Presentation file not found")

        return Response(
            content=open(file_path, 'rb').read(),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download presentation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
