"""
Evaluation Harness - systematic testing framework for agents

Implements pass@k, pass^k metrics and systematic evaluation.
"""
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging


@dataclass
class EvalTask:
    """
    Definition of an evaluation task

    An eval task has:
    - Input (query/request)
    - Expected output or success criteria
    - Grader function to check correctness
    """
    id: str
    name: str
    description: str
    input: Dict[str, Any]
    expected_output: Optional[Any] = None
    success_criteria: Optional[str] = None
    grader: Optional[Callable] = None
    category: str = "general"
    difficulty: str = "medium"  # easy, medium, hard


@dataclass
class EvalResult:
    """Result of an evaluation run"""
    task_id: str
    task_name: str
    success: bool
    output: Any
    expected: Any
    score: float  # 0.0 to 1.0
    error: Optional[str] = None
    execution_time_ms: int = 0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EvalHarness:
    """
    Evaluation harness for systematic agent testing

    Features:
    - pass@k: Probability of success in k attempts
    - pass^k: Probability of consistent success
    - Capability evals: Test new features
    - Regression evals: Ensure existing features work
    """

    def __init__(self):
        self.logger = logging.getLogger("eval.harness")
        self.tasks: Dict[str, EvalTask] = {}
        self.results: List[EvalResult] = []

    def register_task(self, task: EvalTask):
        """
        Register an evaluation task

        Args:
            task: EvalTask to register
        """
        self.tasks[task.id] = task
        self.logger.info(f"Registered eval task: {task.id} - {task.name}")

    def register_tasks(self, tasks: List[EvalTask]):
        """Register multiple tasks"""
        for task in tasks:
            self.register_task(task)

    async def run_task(
        self,
        task_id: str,
        agent_fn: Callable,
        context: Optional[Dict[str, Any]] = None
    ) -> EvalResult:
        """
        Run a single evaluation task

        Args:
            task_id: Task ID
            agent_fn: Async function that executes the agent
            context: Additional context

        Returns:
            EvalResult
        """
        task = self.tasks.get(task_id)

        if not task:
            raise ValueError(f"Task not found: {task_id}")

        self.logger.info(f"Running eval task: {task.id}")

        start_time = datetime.utcnow()

        try:
            # Execute agent
            output = await agent_fn(task.input, context)

            # Calculate execution time
            end_time = datetime.utcnow()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Grade result
            if task.grader:
                success, score = task.grader(output, task.expected_output)
            else:
                # Default grading: check if output matches expected
                success = output == task.expected_output
                score = 1.0 if success else 0.0

            result = EvalResult(
                task_id=task.id,
                task_name=task.name,
                success=success,
                output=output,
                expected=task.expected_output,
                score=score,
                execution_time_ms=execution_time_ms,
                metadata={
                    "category": task.category,
                    "difficulty": task.difficulty
                }
            )

            self.results.append(result)
            return result

        except Exception as e:
            self.logger.error(f"Eval task failed: {task.id} - {str(e)}")

            end_time = datetime.utcnow()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

            result = EvalResult(
                task_id=task.id,
                task_name=task.name,
                success=False,
                output=None,
                expected=task.expected_output,
                score=0.0,
                error=str(e),
                execution_time_ms=execution_time_ms,
                metadata={
                    "category": task.category,
                    "difficulty": task.difficulty
                }
            )

            self.results.append(result)
            return result

    async def run_task_multiple_times(
        self,
        task_id: str,
        agent_fn: Callable,
        k: int = 3,
        context: Optional[Dict[str, Any]] = None
    ) -> List[EvalResult]:
        """
        Run a task k times for pass@k evaluation

        Args:
            task_id: Task ID
            agent_fn: Agent function
            k: Number of attempts
            context: Context

        Returns:
            List of k EvalResults
        """
        results = []

        for i in range(k):
            self.logger.info(f"Running attempt {i+1}/{k} for task {task_id}")
            result = await self.run_task(task_id, agent_fn, context)
            results.append(result)

        return results

    def calculate_pass_at_k(self, results: List[EvalResult]) -> float:
        """
        Calculate pass@k: probability of at least one success in k attempts

        Args:
            results: List of results from k attempts

        Returns:
            pass@k score (0.0 to 1.0)
        """
        if not results:
            return 0.0

        # pass@k = 1 if any attempt succeeded
        return 1.0 if any(r.success for r in results) else 0.0

    def calculate_pass_power_k(self, results: List[EvalResult]) -> float:
        """
        Calculate pass^k: probability of consistent success across k attempts

        Args:
            results: List of results from k attempts

        Returns:
            pass^k score (0.0 to 1.0)
        """
        if not results:
            return 0.0

        # pass^k = 1 if all attempts succeeded
        return 1.0 if all(r.success for r in results) else 0.0

    async def run_eval_suite(
        self,
        agent_fn: Callable,
        task_ids: Optional[List[str]] = None,
        k: int = 1,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run a complete evaluation suite

        Args:
            agent_fn: Agent function to evaluate
            task_ids: List of task IDs (None = all tasks)
            k: Number of attempts per task
            context: Context

        Returns:
            Evaluation report
        """
        self.logger.info(f"Running eval suite with {len(task_ids or self.tasks)} tasks")

        tasks_to_run = task_ids or list(self.tasks.keys())
        all_results = {}

        for task_id in tasks_to_run:
            results = await self.run_task_multiple_times(task_id, agent_fn, k, context)
            all_results[task_id] = results

        # Calculate metrics
        report = self.generate_report(all_results, k)

        return report

    def generate_report(
        self,
        results_by_task: Dict[str, List[EvalResult]],
        k: int
    ) -> Dict[str, Any]:
        """
        Generate evaluation report

        Args:
            results_by_task: Results grouped by task
            k: Number of attempts per task

        Returns:
            Report dictionary
        """
        total_tasks = len(results_by_task)
        pass_at_k_scores = []
        pass_power_k_scores = []
        avg_execution_times = []
        category_results = {}

        for task_id, results in results_by_task.items():
            pass_at_k = self.calculate_pass_at_k(results)
            pass_power_k = self.calculate_pass_power_k(results)

            pass_at_k_scores.append(pass_at_k)
            pass_power_k_scores.append(pass_power_k)

            avg_time = sum(r.execution_time_ms for r in results) / len(results)
            avg_execution_times.append(avg_time)

            # Group by category
            category = results[0].metadata.get("category", "general")
            if category not in category_results:
                category_results[category] = []
            category_results[category].append(pass_at_k)

        # Overall metrics
        overall_pass_at_k = sum(pass_at_k_scores) / total_tasks if total_tasks > 0 else 0.0
        overall_pass_power_k = sum(pass_power_k_scores) / total_tasks if total_tasks > 0 else 0.0
        avg_execution_time = sum(avg_execution_times) / total_tasks if total_tasks > 0 else 0

        # Category breakdown
        category_metrics = {
            cat: sum(scores) / len(scores) if scores else 0.0
            for cat, scores in category_results.items()
        }

        report = {
            "summary": {
                "total_tasks": total_tasks,
                "attempts_per_task": k,
                "overall_pass_at_k": overall_pass_at_k,
                "overall_pass_power_k": overall_pass_power_k,
                "avg_execution_time_ms": avg_execution_time
            },
            "by_category": category_metrics,
            "by_task": {
                task_id: {
                    "pass_at_k": self.calculate_pass_at_k(results),
                    "pass_power_k": self.calculate_pass_power_k(results),
                    "avg_score": sum(r.score for r in results) / len(results),
                    "attempts": len(results),
                    "successes": sum(1 for r in results if r.success)
                }
                for task_id, results in results_by_task.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        return report

    def get_failed_tasks(self) -> List[EvalResult]:
        """Get all failed eval results"""
        return [r for r in self.results if not r.success]

    def clear_results(self):
        """Clear all results"""
        self.results = []


# Utility graders

def exact_match_grader(output: Any, expected: Any) -> tuple[bool, float]:
    """Grade by exact match"""
    success = output == expected
    return success, 1.0 if success else 0.0


def contains_grader(output: str, expected: str) -> tuple[bool, float]:
    """Grade by substring containment"""
    success = expected.lower() in str(output).lower()
    return success, 1.0 if success else 0.0


def threshold_grader(threshold: float):
    """Create a threshold grader"""
    def grader(output: Any, expected: Any) -> tuple[bool, float]:
        if isinstance(output, (int, float)) and isinstance(expected, (int, float)):
            diff = abs(output - expected)
            success = diff <= threshold
            score = max(0.0, 1.0 - (diff / (expected if expected != 0 else 1.0)))
            return success, score
        return False, 0.0
    return grader
