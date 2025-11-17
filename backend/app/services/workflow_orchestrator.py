import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.services.duckdb_service import DuckDBService
from app.services.code_executor_service import CodeExecutorService
from app.services.ml_model_service import MLModelService


class WorkflowStep:
    """Represents a single step in an analysis workflow"""

    def __init__(
        self,
        step_num: int,
        step_type: str,
        description: str,
        code: Optional[str] = None,
        sql: Optional[str] = None,
        depends_on: Optional[List[int]] = None
    ):
        self.step_num = step_num
        self.step_type = step_type  # 'sql', 'python', 'ml'
        self.description = description
        self.code = code
        self.sql = sql
        self.depends_on = depends_on or []
        self.status = 'pending'
        self.result = None
        self.error = None
        self.execution_time_ms = 0


class WorkflowOrchestrator:
    """Orchestrate multi-step analysis workflows combining SQL and Python"""

    def __init__(self):
        self.duckdb_service = DuckDBService()
        self.code_executor = CodeExecutorService()
        self.ml_model_service = MLModelService()

    async def execute_workflow(
        self,
        steps: List[Dict[str, Any]],
        dataset_id: str,
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a multi-step workflow"""

        if workflow_id is None:
            workflow_id = str(uuid.uuid4())

        # Convert dicts to WorkflowStep objects
        workflow_steps = [
            WorkflowStep(
                step_num=step.get('step', i + 1),
                step_type=step.get('type', 'python'),
                description=step.get('description', f'Step {i + 1}'),
                code=step.get('code'),
                sql=step.get('sql'),
                depends_on=step.get('depends_on', [])
            )
            for i, step in enumerate(steps)
        ]

        # Execution context - shared state between steps
        context = {
            'dataset_id': dataset_id,
            'workflow_id': workflow_id,
            'step_results': {},
            'intermediate_data': {},
            'models': {}
        }

        # Execute steps in order
        workflow_results = []
        start_time = datetime.utcnow()

        for step in workflow_steps:
            step_start = datetime.utcnow()

            # Check dependencies
            if not self._check_dependencies(step, context):
                step.status = 'skipped'
                step.error = 'Dependencies not met'
                continue

            # Execute step based on type
            try:
                if step.step_type == 'sql':
                    result = await self._execute_sql_step(step, context)
                elif step.step_type == 'python' or step.step_type == 'ml':
                    result = await self._execute_python_step(step, context)
                else:
                    raise ValueError(f"Unknown step type: {step.step_type}")

                step.result = result
                step.status = 'success'

                # Store result in context for next steps
                context['step_results'][step.step_num] = result

            except Exception as e:
                step.status = 'failed'
                step.error = str(e)
                result = None

            # Calculate execution time
            step_end = datetime.utcnow()
            step.execution_time_ms = int((step_end - step_start).total_seconds() * 1000)

            # Add to results
            workflow_results.append({
                'step': step.step_num,
                'type': step.step_type,
                'description': step.description,
                'status': step.status,
                'result': result,
                'error': step.error,
                'execution_time_ms': step.execution_time_ms
            })

        # Calculate total execution time
        end_time = datetime.utcnow()
        total_time_ms = int((end_time - start_time).total_seconds() * 1000)

        # Workflow summary
        success_count = sum(1 for s in workflow_steps if s.status == 'success')
        failed_count = sum(1 for s in workflow_steps if s.status == 'failed')

        return {
            'workflow_id': workflow_id,
            'status': 'completed' if failed_count == 0 else 'partial_failure',
            'total_steps': len(workflow_steps),
            'successful_steps': success_count,
            'failed_steps': failed_count,
            'steps': workflow_results,
            'final_result': workflow_results[-1]['result'] if workflow_results else None,
            'total_execution_time_ms': total_time_ms,
            'models_created': list(context['models'].keys())
        }

    async def _execute_sql_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a SQL step"""

        dataset_id = context['dataset_id']

        # Execute SQL query
        result_df = self.duckdb_service.execute_query(
            sql=step.sql,
            dataset_id=dataset_id
        )

        # Store intermediate data if needed for next steps
        context['intermediate_data'][f'step_{step.step_num}'] = result_df

        return {
            'row_count': len(result_df),
            'columns': result_df.columns.tolist(),
            'data': result_df.head(100).to_dict('records'),  # Limit to first 100 rows
            'summary': f"Returned {len(result_df)} rows with {len(result_df.columns)} columns"
        }

    async def _execute_python_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a Python/ML step"""

        dataset_id = context['dataset_id']

        # Inject context into code if step references previous results
        code = step.code

        # Check if code references previous step results
        for step_num, result_data in context['intermediate_data'].items():
            placeholder = f'{{{step_num}}}'
            if placeholder in code:
                # Replace placeholder with actual data loading
                code = code.replace(
                    placeholder,
                    f"pd.DataFrame({result_data.to_dict('records')})"
                )

        # Execute code
        execution_result = self.code_executor.execute_python(
            code=code,
            dataset_id=dataset_id
        )

        if execution_result['status'] != 'SUCCESS':
            raise Exception(execution_result.get('error', 'Execution failed'))

        # Check if a model was created
        if execution_result.get('model'):
            # Save the model
            model_metadata = execution_result['output'].get('model_metadata', {})
            # Note: Actual model object would need to be passed differently
            # This is a placeholder for the integration
            context['models'][f'step_{step.step_num}'] = model_metadata

        return execution_result['output']

    def _check_dependencies(
        self,
        step: WorkflowStep,
        context: Dict[str, Any]
    ) -> bool:
        """Check if step dependencies are met"""

        if not step.depends_on:
            return True

        # Check that all dependent steps have completed successfully
        for dep_step in step.depends_on:
            if dep_step not in context['step_results']:
                return False

        return True

    def create_workflow_from_nl(
        self,
        nl_query: str,
        detected_steps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create workflow structure from natural language and detected steps"""

        workflow = []

        for i, step_info in enumerate(detected_steps):
            workflow.append({
                'step': i + 1,
                'type': step_info.get('type', 'python'),
                'description': step_info.get('description'),
                'code': step_info.get('code'),
                'sql': step_info.get('sql'),
                'depends_on': step_info.get('depends_on', [i] if i > 0 else [])
            })

        return workflow

    def optimize_workflow(
        self,
        steps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Optimize workflow by identifying parallelizable steps"""

        # Simple optimization: identify steps that don't depend on each other
        # and can be run in parallel (future enhancement)

        optimized = []

        for step in steps:
            # For now, just return as-is
            # Future: analyze dependencies and create parallel execution groups
            optimized.append(step)

        return optimized

    def get_workflow_visualization(
        self,
        steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate visualization data for workflow graph"""

        nodes = []
        edges = []

        for step in steps:
            nodes.append({
                'id': f"step_{step['step']}",
                'label': step['description'],
                'type': step['type']
            })

            # Create edges based on dependencies
            depends_on = step.get('depends_on', [])
            for dep in depends_on:
                edges.append({
                    'from': f"step_{dep}",
                    'to': f"step_{step['step']}"
                })

        return {
            'nodes': nodes,
            'edges': edges
        }
