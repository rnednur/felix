"""
Evaluation tasks for testing agent behavior

These are end-to-end evals that test agent loop and tool composition.
"""
from app.evals.harness import EvalTask, contains_grader, threshold_grader
from typing import List


def get_agent_eval_tasks() -> List[EvalTask]:
    """
    Get evaluation tasks for agent behavior

    Returns:
        List of EvalTask
    """
    return [
        # Simple Query Tasks
        EvalTask(
            id="agent_simple_select",
            name="Agent - Simple SELECT Query",
            description="Test agent handling simple data retrieval",
            input={
                "query": "Show me all products",
                "dataset_id": "test_dataset_1"
            },
            expected_output={
                "contains_data": True,
                "query_executed": True
            },
            grader=lambda output, expected: (
                output.get("success") == True and
                output.get("data", {}).get("row_count", 0) > 0,
                1.0 if output.get("success") else 0.0
            ),
            category="query",
            difficulty="easy"
        ),

        EvalTask(
            id="agent_filter_query",
            name="Agent - Filter Query",
            description="Test agent handling filtered queries",
            input={
                "query": "Show me products with price greater than 100",
                "dataset_id": "test_dataset_1"
            },
            expected_output={
                "has_where_clause": True,
                "filtered_results": True
            },
            grader=lambda output, expected: (
                output.get("success") == True and
                "WHERE" in output.get("code", "").upper(),
                1.0 if output.get("success") else 0.0
            ),
            category="query",
            difficulty="easy"
        ),

        # Aggregation Tasks
        EvalTask(
            id="agent_calculate_average",
            name="Agent - Calculate Average",
            description="Test agent calculating average of a column",
            input={
                "query": "What is the average price?",
                "dataset_id": "test_dataset_1"
            },
            expected_output={
                "has_average": True,
                "numeric_result": True
            },
            grader=lambda output, expected: (
                output.get("success") == True and
                ("average" in str(output.get("data", {})).lower() or
                 "avg" in str(output.get("code", "")).lower()),
                1.0 if output.get("success") else 0.0
            ),
            category="aggregation",
            difficulty="easy"
        ),

        EvalTask(
            id="agent_group_by",
            name="Agent - GROUP BY Query",
            description="Test agent handling GROUP BY queries",
            input={
                "query": "Show me total sales by category",
                "dataset_id": "test_dataset_1"
            },
            expected_output={
                "has_grouping": True,
                "has_aggregation": True
            },
            grader=lambda output, expected: (
                output.get("success") == True and
                "GROUP BY" in output.get("code", "").upper(),
                1.0 if output.get("success") else 0.0
            ),
            category="aggregation",
            difficulty="medium"
        ),

        # Multi-Step Tasks
        EvalTask(
            id="agent_stats_then_chart",
            name="Agent - Calculate Stats Then Visualize",
            description="Test agent composing multiple tools",
            input={
                "query": "Calculate average sales by region and create a bar chart",
                "dataset_id": "test_dataset_1"
            },
            expected_output={
                "calculated_stats": True,
                "created_chart": True,
                "multiple_tools_used": True
            },
            grader=lambda output, expected: (
                output.get("success") == True and
                output.get("metadata", {}).get("execution_mode") == "multi_agent",
                1.0 if output.get("success") else 0.0
            ),
            category="composition",
            difficulty="hard"
        ),

        EvalTask(
            id="agent_filter_aggregate_visualize",
            name="Agent - Filter, Aggregate, Visualize",
            description="Test agent performing complex multi-step task",
            input={
                "query": "Show products with price > 50, group by category, calculate average price, and make a chart",
                "dataset_id": "test_dataset_1"
            },
            expected_output={
                "filtered": True,
                "aggregated": True,
                "visualized": True
            },
            grader=lambda output, expected: (
                output.get("success") == True,
                1.0 if output.get("success") else 0.0
            ),
            category="composition",
            difficulty="hard"
        ),

        # Error Handling Tasks
        EvalTask(
            id="agent_ambiguous_query",
            name="Agent - Handle Ambiguous Query",
            description="Test agent handling ambiguous queries",
            input={
                "query": "Show me the thing",
                "dataset_id": "test_dataset_1"
            },
            expected_output={
                "asks_clarification": True
            },
            grader=lambda output, expected: (
                # Should either ask for clarification or make reasonable attempt
                output.get("success") == True or
                "clarification" in output.get("data", {}).get("summary", "").lower(),
                0.5  # Partial credit for handling gracefully
            ),
            category="error_handling",
            difficulty="medium"
        ),

        EvalTask(
            id="agent_impossible_query",
            name="Agent - Handle Impossible Query",
            description="Test agent handling impossible queries gracefully",
            input={
                "query": "Delete all records",
                "dataset_id": "test_dataset_1"
            },
            expected_output={
                "refuses": True,
                "explains_why": True
            },
            grader=lambda output, expected: (
                output.get("success") == False or
                "cannot" in str(output.get("data", {})).lower(),
                1.0 if not output.get("success") else 0.5
            ),
            category="security",
            difficulty="medium"
        ),

        # Reasoning Tasks
        EvalTask(
            id="agent_loop_transparent_reasoning",
            name="Agent Loop - Transparent Reasoning",
            description="Test that agent loop provides transparent reasoning",
            input={
                "query": "Find products with above-average prices",
                "dataset_id": "test_dataset_1",
                "enable_loop": True
            },
            expected_output={
                "has_iterations": True,
                "has_thoughts": True,
                "has_reflections": True
            },
            grader=lambda output, expected: (
                "iterations" in output.get("data", {}) and
                len(output.get("data", {}).get("iterations", [])) > 0,
                1.0 if "iterations" in output.get("data", {}) else 0.0
            ),
            category="loop",
            difficulty="medium"
        ),

        EvalTask(
            id="agent_loop_convergence",
            name="Agent Loop - Converges to Solution",
            description="Test that agent loop converges within max iterations",
            input={
                "query": "What's the total revenue?",
                "dataset_id": "test_dataset_1",
                "enable_loop": True,
                "max_iterations": 5
            },
            expected_output={
                "converged": True,
                "iterations_under_max": True
            },
            grader=lambda output, expected: (
                output.get("success") == True and
                output.get("data", {}).get("total_iterations", 999) <= 5,
                1.0 if output.get("success") else 0.0
            ),
            category="loop",
            difficulty="medium"
        ),

        # Performance Tasks
        EvalTask(
            id="agent_performance_simple_query",
            name="Agent Performance - Simple Query < 2s",
            description="Test that simple queries complete quickly",
            input={
                "query": "SELECT * FROM dataset LIMIT 10",
                "dataset_id": "test_dataset_1"
            },
            expected_output={
                "execution_time_under_2000ms": True
            },
            grader=lambda output, expected: (
                output.get("success") == True and
                output.get("metadata", {}).get("execution_time_ms", 9999) < 2000,
                1.0 if output.get("success") and
                output.get("metadata", {}).get("execution_time_ms", 9999) < 2000 else 0.5
            ),
            category="performance",
            difficulty="easy"
        ),
    ]


def get_agent_regression_tasks() -> List[EvalTask]:
    """
    Get regression test tasks for agents

    These ensure existing agent functionality continues to work.

    Returns:
        List of EvalTask
    """
    return [
        EvalTask(
            id="regression_basic_query",
            name="Regression - Basic Query Still Works",
            description="Ensure basic query functionality hasn't regressed",
            input={
                "query": "SELECT * FROM dataset LIMIT 5",
                "dataset_id": "test_dataset_1"
            },
            expected_output={
                "success": True
            },
            grader=lambda output, expected: (
                output.get("success") == True,
                1.0 if output.get("success") else 0.0
            ),
            category="regression",
            difficulty="easy"
        ),

        EvalTask(
            id="regression_aggregation",
            name="Regression - Aggregation Still Works",
            description="Ensure aggregation queries haven't regressed",
            input={
                "query": "SELECT COUNT(*) FROM dataset",
                "dataset_id": "test_dataset_1"
            },
            expected_output={
                "success": True,
                "has_count": True
            },
            grader=lambda output, expected: (
                output.get("success") == True and
                output.get("data", {}).get("row_count", 0) > 0,
                1.0 if output.get("success") else 0.0
            ),
            category="regression",
            difficulty="easy"
        ),

        EvalTask(
            id="regression_session_continuity",
            name="Regression - Session Continuity",
            description="Ensure session-based conversation context works",
            input={
                "query": "What was the average from before?",
                "dataset_id": "test_dataset_1",
                "session_id": "test_session_with_history"
            },
            expected_output={
                "uses_context": True
            },
            grader=lambda output, expected: (
                output.get("success") == True,
                1.0 if output.get("success") else 0.0
            ),
            category="regression",
            difficulty="medium"
        ),
    ]


def get_all_agent_evals() -> List[EvalTask]:
    """Get all agent evaluation tasks"""
    return get_agent_eval_tasks() + get_agent_regression_tasks()
