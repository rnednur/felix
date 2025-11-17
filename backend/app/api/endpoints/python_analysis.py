from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import time
from datetime import datetime

from app.core.database import get_db
from app.models.dataset import Dataset
from app.models.code_execution import CodeExecution, MLModel, ExecutionMode, ExecutionStatus
from app.services.nl_to_python_service import NLToPythonService
from app.services.code_executor_service import CodeExecutorService
from app.services.ml_model_service import MLModelService
from app.services.workflow_orchestrator import WorkflowOrchestrator
from app.services.code_fixer_service import CodeFixerService

router = APIRouter(prefix="/python-analysis", tags=["python-analysis"])


# Request/Response schemas
class PythonAnalysisRequest(BaseModel):
    dataset_id: str
    query: str
    mode: Optional[str] = None  # 'auto', 'python', 'ml', 'stats', 'workflow'
    execute_immediately: bool = False  # If False, just generate code


class CodeExecutionRequest(BaseModel):
    execution_id: str


class WorkflowExecutionRequest(BaseModel):
    dataset_id: str
    query: str


class PythonAnalysisResponse(BaseModel):
    execution_id: str
    mode: str
    generated_code: str
    steps: Optional[List[Dict[str, Any]]] = None
    estimated_runtime: str
    requires_review: bool
    safety_warnings: Optional[List[str]] = None


class ExecutionResultResponse(BaseModel):
    execution_id: str
    status: str
    output: Optional[Dict[str, Any]] = None
    visualizations: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None


@router.post("/generate", response_model=PythonAnalysisResponse)
async def generate_python_code(
    request: PythonAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Generate Python code from natural language query"""

    # Verify dataset exists
    dataset = db.query(Dataset).filter(
        Dataset.id == request.dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    # Generate Python code
    nl_python_service = NLToPythonService()

    try:
        result = await nl_python_service.generate_python_code(
            nl_query=request.query,
            dataset_id=request.dataset_id,
            mode=request.mode if request.mode != 'auto' else None
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to generate code: {str(e)}")

    # Validate code safety
    safety_check = nl_python_service.validate_code_safety(result['code'])

    # Create code execution record
    execution_id = str(uuid.uuid4())
    code_execution = CodeExecution(
        id=execution_id,
        dataset_id=request.dataset_id,
        nl_input=request.query,
        mode=ExecutionMode(result['mode']),
        generated_code=result['code'],
        execution_status=ExecutionStatus.PENDING,
        code_metadata=result
    )
    db.add(code_execution)
    db.commit()

    # Auto-execute if requested and safe
    if request.execute_immediately and safety_check['is_safe']:
        # Execute in background (in production, use Celery task)
        try:
            executor = CodeExecutorService()
            exec_result = executor.execute_python(
                code=result['code'],
                dataset_id=request.dataset_id
            )

            # Update execution record
            code_execution.execution_status = ExecutionStatus(exec_result['status'])
            code_execution.result_summary = exec_result.get('output')
            code_execution.visualizations = exec_result.get('visualizations')
            code_execution.error_message = exec_result.get('error')
            code_execution.completed_at = datetime.utcnow()
            db.commit()

        except Exception as e:
            code_execution.execution_status = ExecutionStatus.FAILED
            code_execution.error_message = str(e)
            db.commit()

    return {
        'execution_id': execution_id,
        'mode': result['mode'],
        'generated_code': result['code'],
        'steps': result.get('steps'),
        'estimated_runtime': result['estimated_runtime'],
        'requires_review': not safety_check['is_safe'],
        'safety_warnings': safety_check.get('issues') if not safety_check['is_safe'] else None
    }


@router.post("/execute", response_model=ExecutionResultResponse)
async def execute_python_code(
    request: CodeExecutionRequest,
    db: Session = Depends(get_db)
):
    """Execute previously generated Python code with auto-retry on common errors"""

    # Get code execution record
    code_execution = db.query(CodeExecution).filter(
        CodeExecution.id == request.execution_id
    ).first()

    if not code_execution:
        raise HTTPException(404, "Code execution not found")

    if code_execution.execution_status == ExecutionStatus.RUNNING:
        raise HTTPException(400, "Code is already running")

    # Update status
    code_execution.execution_status = ExecutionStatus.RUNNING
    code_execution.started_at = datetime.utcnow()
    db.commit()

    # Execute code with auto-retry
    executor = CodeExecutorService()
    fixer = CodeFixerService()

    max_retries = 2
    current_code = code_execution.generated_code
    exec_result = None

    try:
        start_time = time.time()

        for attempt in range(max_retries + 1):
            exec_result = executor.execute_python(
                code=current_code,
                dataset_id=code_execution.dataset_id
            )

            # If successful, break
            if exec_result['status'] == 'SUCCESS':
                break

            # If failed and we have retries left, try to fix
            if attempt < max_retries and exec_result.get('error'):
                print(f"⚠️ Code execution failed (attempt {attempt + 1}/{max_retries + 1})")
                print(f"Error: {exec_result['error']}")

                # First try simple pattern-based fixes
                fixed_code = fixer.attempt_fix(current_code, exec_result['error'])

                # If no simple fix found, try LLM-based fix
                if not fixed_code or fixed_code == current_code:
                    print(f"🤖 Trying LLM-based fix...")
                    fixed_code = await fixer.attempt_fix_with_llm(
                        current_code,
                        exec_result['error'],
                        exec_result.get('error_trace')
                    )

                if fixed_code and fixed_code != current_code:
                    fix_type = "LLM" if not fixer.get_fix_suggestion(exec_result['error']) else "Pattern"
                    print(f"✅ Applied {fix_type}-based fix, retrying...")
                    current_code = fixed_code
                    continue
                else:
                    print(f"❌ No fix available, stopping retries")
                    break

        execution_time_ms = int((time.time() - start_time) * 1000)

        # Update execution record
        code_execution.execution_status = ExecutionStatus(exec_result['status'])
        code_execution.execution_time_ms = execution_time_ms
        code_execution.result_summary = exec_result.get('output')
        code_execution.visualizations = exec_result.get('visualizations')
        code_execution.error_message = exec_result.get('error')
        code_execution.error_trace = exec_result.get('error_trace')
        code_execution.completed_at = datetime.utcnow()

        # If ML model was created, save it
        if exec_result.get('model') and exec_result['output']:
            model_service = MLModelService()
            # Note: This is simplified - would need to extract actual model object
            # For now, just store metadata
            model_metadata = exec_result['output'].get('model_metadata', {})

            if model_metadata:
                ml_model = MLModel(
                    id=str(uuid.uuid4()),
                    dataset_id=code_execution.dataset_id,
                    code_execution_id=code_execution.id,
                    model_type=model_metadata.get('model_type', 'unknown'),
                    features=model_metadata.get('features', []),
                    target_column=model_metadata.get('target_column'),
                    metrics=model_metadata.get('metrics', {}),
                    model_artifact_path='',  # Would be populated by model_service
                    status='active'
                )
                db.add(ml_model)

        db.commit()

        return {
            'execution_id': request.execution_id,
            'status': exec_result['status'],
            'output': exec_result.get('output'),
            'visualizations': exec_result.get('visualizations'),
            'error': exec_result.get('error'),
            'execution_time_ms': execution_time_ms
        }

    except Exception as e:
        # Update with error
        code_execution.execution_status = ExecutionStatus.FAILED
        code_execution.error_message = str(e)
        code_execution.completed_at = datetime.utcnow()
        db.commit()

        raise HTTPException(500, f"Code execution failed: {str(e)}")


@router.get("/execution/{execution_id}", response_model=ExecutionResultResponse)
async def get_execution_result(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """Get execution result"""

    code_execution = db.query(CodeExecution).filter(
        CodeExecution.id == execution_id
    ).first()

    if not code_execution:
        raise HTTPException(404, "Execution not found")

    return {
        'execution_id': execution_id,
        'status': code_execution.execution_status.value,
        'output': code_execution.result_summary,
        'visualizations': code_execution.visualizations,
        'error': code_execution.error_message,
        'execution_time_ms': code_execution.execution_time_ms
    }


@router.post("/workflow", response_model=Dict[str, Any])
async def execute_workflow(
    request: WorkflowExecutionRequest,
    db: Session = Depends(get_db)
):
    """Execute multi-step workflow"""

    # Verify dataset
    dataset = db.query(Dataset).filter(
        Dataset.id == request.dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    # Generate workflow steps
    nl_python_service = NLToPythonService()

    try:
        result = await nl_python_service.generate_python_code(
            nl_query=request.query,
            dataset_id=request.dataset_id,
            mode='workflow'
        )
    except Exception as e:
        raise HTTPException(500, f"Failed to generate workflow: {str(e)}")

    # Execute workflow
    orchestrator = WorkflowOrchestrator()

    try:
        workflow_result = await orchestrator.execute_workflow(
            steps=result['steps'],
            dataset_id=request.dataset_id
        )

        # Save workflow execution records
        workflow_id = workflow_result['workflow_id']

        for step_result in workflow_result['steps']:
            execution_id = str(uuid.uuid4())
            code_execution = CodeExecution(
                id=execution_id,
                dataset_id=request.dataset_id,
                nl_input=request.query,
                mode=ExecutionMode.WORKFLOW,
                generated_code=step_result.get('code', ''),
                execution_status=ExecutionStatus(step_result['status'].upper()),
                execution_time_ms=step_result['execution_time_ms'],
                result_summary=step_result.get('result'),
                error_message=step_result.get('error'),
                workflow_id=workflow_id,
                step_number=step_result['step'],
                completed_at=datetime.utcnow()
            )
            db.add(code_execution)

        db.commit()

        return workflow_result

    except Exception as e:
        raise HTTPException(500, f"Workflow execution failed: {str(e)}")


@router.get("/executions/dataset/{dataset_id}")
async def list_dataset_executions(
    dataset_id: str,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List code executions for a dataset"""

    executions = db.query(CodeExecution).filter(
        CodeExecution.dataset_id == dataset_id
    ).order_by(
        CodeExecution.created_at.desc()
    ).limit(limit).all()

    return [
        {
            'execution_id': ex.id,
            'nl_input': ex.nl_input,
            'mode': ex.mode.value,
            'status': ex.execution_status.value,
            'execution_time_ms': ex.execution_time_ms,
            'created_at': ex.created_at.isoformat(),
            'workflow_id': ex.workflow_id
        }
        for ex in executions
    ]


@router.get("/models/dataset/{dataset_id}")
async def list_dataset_models(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """List ML models for a dataset"""

    models = db.query(MLModel).filter(
        MLModel.dataset_id == dataset_id,
        MLModel.status == 'active'
    ).order_by(
        MLModel.created_at.desc()
    ).all()

    return [
        {
            'model_id': model.id,
            'name': model.name,
            'model_type': model.model_type,
            'framework': model.framework,
            'features': model.features,
            'target_column': model.target_column,
            'metrics': model.metrics,
            'created_at': model.created_at.isoformat()
        }
        for model in models
    ]
