"""
Evaluation tasks for testing individual tools

These are capability evals that test each tool primitive.
"""
from app.evals.harness import EvalTask, exact_match_grader, contains_grader, threshold_grader
from typing import List


def get_tool_eval_tasks() -> List[EvalTask]:
    """
    Get evaluation tasks for tool primitives

    Returns:
        List of EvalTask
    """
    return [
        # ReadDatasetTool Evals
        EvalTask(
            id="tool_read_dataset_basic",
            name="Read Dataset - Basic Info",
            description="Test reading basic dataset information",
            input={
                "tool_name": "read_dataset",
                "parameters": {
                    "dataset_id": "test_dataset_1",
                    "include_schema": False,
                    "include_stats": False
                }
            },
            expected_output={
                "success": True,
                "has_dataset_id": True,
                "has_name": True,
                "has_row_count": True
            },
            grader=lambda output, expected: (
                output.get("success") == True and
                "dataset_id" in output.get("data", {}),
                1.0 if output.get("success") else 0.0
            ),
            category="data_access",
            difficulty="easy"
        ),

        EvalTask(
            id="tool_read_dataset_with_schema",
            name="Read Dataset - With Schema",
            description="Test reading dataset schema information",
            input={
                "tool_name": "read_dataset",
                "parameters": {
                    "dataset_id": "test_dataset_1",
                    "include_schema": True,
                    "include_stats": False
                }
            },
            expected_output={
                "success": True,
                "has_schema": True
            },
            grader=lambda output, expected: (
                output.get("success") == True and
                "schema" in output.get("data", {}),
                1.0 if output.get("success") and "schema" in output.get("data", {}) else 0.0
            ),
            category="data_access",
            difficulty="easy"
        ),

        # ExecuteSQLTool Evals
        EvalTask(
            id="tool_execute_sql_select_all",
            name="Execute SQL - SELECT *",
            description="Test simple SELECT * query",
            input={
                "tool_name": "execute_sql",
                "parameters": {
                    "dataset_id": "test_dataset_1",
                    "sql": "SELECT * FROM dataset LIMIT 10",
                    "limit": 10
                }
            },
            expected_output={
                "success": True,
                "has_rows": True,
                "has_columns": True
            },
            grader=lambda output, expected: (
                output.get("success") == True and
                len(output.get("data", {}).get("rows", [])) > 0,
                1.0 if output.get("success") and len(output.get("data", {}).get("rows", [])) > 0 else 0.0
            ),
            category="data_access",
            difficulty="easy"
        ),

        EvalTask(
            id="tool_execute_sql_aggregate",
            name="Execute SQL - Aggregation",
            description="Test SQL query with GROUP BY and aggregation",
            input={
                "tool_name": "execute_sql",
                "parameters": {
                    "dataset_id": "test_dataset_1",
                    "sql": "SELECT category, COUNT(*) as count, AVG(price) as avg_price FROM dataset GROUP BY category",
                    "limit": 100
                }
            },
            expected_output={
                "success": True,
                "has_aggregation": True
            },
            grader=lambda output, expected: (
                output.get("success") == True and
                "columns" in output.get("data", {}) and
                "count" in [col.lower() for col in output.get("data", {}).get("columns", [])],
                1.0 if output.get("success") else 0.0
            ),
            category="data_access",
            difficulty="medium"
        ),

        EvalTask(
            id="tool_execute_sql_forbidden",
            name="Execute SQL - Block Forbidden Operations",
            description="Test that forbidden SQL operations are blocked",
            input={
                "tool_name": "execute_sql",
                "parameters": {
                    "dataset_id": "test_dataset_1",
                    "sql": "DELETE FROM dataset WHERE id = 1",
                    "limit": 100
                }
            },
            expected_output={
                "success": False,
                "error_contains": "forbidden"
            },
            grader=lambda output, expected: (
                output.get("success") == False and
                "forbidden" in output.get("error", "").lower(),
                1.0 if not output.get("success") else 0.0
            ),
            category="security",
            difficulty="easy"
        ),

        # CalculateStatsTool Evals
        EvalTask(
            id="tool_calculate_stats_basic",
            name="Calculate Stats - Basic Metrics",
            description="Test calculating basic statistics",
            input={
                "tool_name": "calculate_stats",
                "parameters": {
                    "dataset_id": "test_dataset_1",
                    "columns": ["price", "quantity"],
                    "metrics": ["mean", "median", "std"]
                }
            },
            expected_output={
                "success": True,
                "has_statistics": True
            },
            grader=lambda output, expected: (
                output.get("success") == True and
                "statistics" in output.get("data", {}) and
                len(output.get("data", {}).get("statistics", {})) > 0,
                1.0 if output.get("success") else 0.0
            ),
            category="computation",
            difficulty="easy"
        ),

        EvalTask(
            id="tool_calculate_stats_all_metrics",
            name="Calculate Stats - All Metrics",
            description="Test calculating all available metrics",
            input={
                "tool_name": "calculate_stats",
                "parameters": {
                    "dataset_id": "test_dataset_1",
                    "columns": ["price"],
                    "metrics": ["mean", "median", "std", "min", "max", "count", "sum", "quartiles"]
                }
            },
            expected_output={
                "success": True,
                "has_all_metrics": True
            },
            grader=lambda output, expected: (
                output.get("success") == True and
                "mean" in output.get("data", {}).get("statistics", {}).get("price", {}) and
                "quartiles" in output.get("data", {}).get("statistics", {}).get("price", {}),
                1.0 if output.get("success") else 0.0
            ),
            category="computation",
            difficulty="medium"
        ),

        # GenerateChartTool Evals
        EvalTask(
            id="tool_generate_chart_bar",
            name="Generate Chart - Bar Chart",
            description="Test generating a bar chart specification",
            input={
                "tool_name": "generate_chart",
                "parameters": {
                    "chart_type": "bar",
                    "x_column": "category",
                    "y_column": "sales",
                    "title": "Sales by Category",
                    "aggregate": "sum"
                }
            },
            expected_output={
                "success": True,
                "has_spec": True,
                "chart_type": "bar"
            },
            grader=lambda output, expected: (
                output.get("success") == True and
                "spec" in output.get("data", {}) and
                output.get("data", {}).get("chart_type") == "bar",
                1.0 if output.get("success") else 0.0
            ),
            category="visualization",
            difficulty="easy"
        ),

        EvalTask(
            id="tool_generate_chart_scatter",
            name="Generate Chart - Scatter Plot",
            description="Test generating a scatter plot specification",
            input={
                "tool_name": "generate_chart",
                "parameters": {
                    "chart_type": "scatter",
                    "x_column": "price",
                    "y_column": "quantity",
                    "title": "Price vs Quantity"
                }
            },
            expected_output={
                "success": True,
                "chart_type": "scatter"
            },
            grader=lambda output, expected: (
                output.get("success") == True and
                output.get("data", {}).get("chart_type") == "scatter",
                1.0 if output.get("success") else 0.0
            ),
            category="visualization",
            difficulty="easy"
        ),

        EvalTask(
            id="tool_generate_chart_with_color",
            name="Generate Chart - With Color Encoding",
            description="Test generating chart with color encoding",
            input={
                "tool_name": "generate_chart",
                "parameters": {
                    "chart_type": "bar",
                    "x_column": "category",
                    "y_column": "sales",
                    "color_column": "region",
                    "aggregate": "sum"
                }
            },
            expected_output={
                "success": True,
                "has_color_encoding": True
            },
            grader=lambda output, expected: (
                output.get("success") == True and
                output.get("metadata", {}).get("has_color_encoding") == True,
                1.0 if output.get("success") else 0.0
            ),
            category="visualization",
            difficulty="medium"
        ),
    ]


def get_tool_regression_tasks() -> List[EvalTask]:
    """
    Get regression test tasks for tools

    These ensure existing tool functionality continues to work.

    Returns:
        List of EvalTask
    """
    return [
        EvalTask(
            id="regression_read_dataset_nonexistent",
            name="Regression - Read Nonexistent Dataset",
            description="Ensure reading nonexistent dataset returns appropriate error",
            input={
                "tool_name": "read_dataset",
                "parameters": {
                    "dataset_id": "nonexistent_dataset_xyz",
                    "include_schema": False
                }
            },
            expected_output={
                "success": False,
                "has_error": True
            },
            grader=lambda output, expected: (
                output.get("success") == False and
                len(output.get("error", "")) > 0,
                1.0 if not output.get("success") else 0.0
            ),
            category="error_handling",
            difficulty="easy"
        ),

        EvalTask(
            id="regression_sql_syntax_error",
            name="Regression - SQL Syntax Error",
            description="Ensure SQL syntax errors are caught and reported",
            input={
                "tool_name": "execute_sql",
                "parameters": {
                    "dataset_id": "test_dataset_1",
                    "sql": "SELCT * FORM dataset",  # Intentional typo
                    "limit": 10
                }
            },
            expected_output={
                "success": False,
                "has_error": True
            },
            grader=lambda output, expected: (
                output.get("success") == False and
                len(output.get("error", "")) > 0,
                1.0 if not output.get("success") else 0.0
            ),
            category="error_handling",
            difficulty="easy"
        ),

        EvalTask(
            id="regression_stats_empty_dataset",
            name="Regression - Stats on Empty Dataset",
            description="Ensure calculating stats on empty dataset handles gracefully",
            input={
                "tool_name": "calculate_stats",
                "parameters": {
                    "dataset_id": "empty_dataset",
                    "columns": [],
                    "metrics": ["mean", "median"]
                }
            },
            expected_output={
                "success": False,
                "error_mentions_empty": True
            },
            grader=lambda output, expected: (
                output.get("success") == False,
                1.0 if not output.get("success") else 0.0
            ),
            category="error_handling",
            difficulty="easy"
        ),
    ]
