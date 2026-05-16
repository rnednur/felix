"""
Execute SQL Tool - primitive for executing SQL queries
"""
from typing import Dict, Any
from app.tools.base_tool import BaseTool
from app.schemas.tool import (
    ToolSchema,
    ToolParameter,
    ToolParameterType,
    ToolResult,
    ToolCapability
)
from app.services.duckdb_service import DuckDBService


class ExecuteSQLTool(BaseTool):
    """
    Atomic tool for executing SQL queries

    This tool executes SQL queries against datasets using DuckDB.
    It provides safe, sandboxed query execution with result limits.
    """

    def __init__(self):
        super().__init__()
        self.duckdb_service = DuckDBService()

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name="execute_sql",
            description="Execute a SQL query against a dataset",
            category="data_access",
            parameters=[
                ToolParameter(
                    name="dataset_id",
                    type=ToolParameterType.STRING,
                    description="UUID of the dataset to query",
                    required=True
                ),
                ToolParameter(
                    name="sql",
                    type=ToolParameterType.STRING,
                    description="SQL query to execute",
                    required=True
                ),
                ToolParameter(
                    name="limit",
                    type=ToolParameterType.INTEGER,
                    description="Maximum number of rows to return",
                    required=False,
                    default=100,
                    min_value=1,
                    max_value=10000
                )
            ],
            returns={
                "type": "object",
                "properties": {
                    "columns": {"type": "array"},
                    "rows": {"type": "array"},
                    "row_count": {"type": "integer"},
                    "truncated": {"type": "boolean"}
                }
            },
            examples=[
                {
                    "parameters": {
                        "dataset_id": "123e4567-e89b-12d3-a456-426614174000",
                        "sql": "SELECT * FROM dataset WHERE price > 100",
                        "limit": 100
                    },
                    "returns": {
                        "columns": ["id", "name", "price"],
                        "rows": [[1, "Product A", 150]],
                        "row_count": 1,
                        "truncated": False
                    }
                }
            ],
            requires_approval=False,
            is_destructive=False,
            estimated_duration_ms=500
        )

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="SQL Query Execution",
            description="Execute SQL queries against datasets with result limits",
            use_cases=[
                "Filter and select specific rows",
                "Aggregate data (SUM, AVG, COUNT, etc.)",
                "Join multiple datasets",
                "Sort and order results",
                "Group data by columns"
            ],
            limitations=[
                "Read-only queries only (no INSERT/UPDATE/DELETE)",
                "Results limited by max_rows parameter",
                "Query timeout after 30 seconds",
                "Sandboxed execution environment"
            ]
        )

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute SQL query

        Args:
            parameters: Tool parameters

        Returns:
            ToolResult with query results
        """
        dataset_id = parameters["dataset_id"]
        sql = parameters["sql"]
        limit = parameters.get("limit", 100)

        try:
            # Validate query is read-only
            sql_upper = sql.upper().strip()
            forbidden_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]

            for keyword in forbidden_keywords:
                if keyword in sql_upper:
                    return ToolResult(
                        tool_name="execute_sql",
                        success=False,
                        data={},
                        error=f"Forbidden operation: {keyword}. Only SELECT queries are allowed."
                    )

            # Execute query
            result = await self.duckdb_service.execute_query(
                dataset_id=dataset_id,
                query=sql,
                limit=limit
            )

            # Format result
            columns = result.get("columns", [])
            rows = result.get("data", [])
            total_count = len(rows)
            truncated = total_count >= limit

            return ToolResult(
                tool_name="execute_sql",
                success=True,
                data={
                    "columns": columns,
                    "rows": rows,
                    "row_count": total_count,
                    "truncated": truncated,
                    "sql": sql
                },
                metadata={
                    "dataset_id": dataset_id,
                    "row_count": total_count,
                    "column_count": len(columns),
                    "truncated": truncated
                }
            )

        except Exception as e:
            return ToolResult(
                tool_name="execute_sql",
                success=False,
                data={},
                error=f"SQL execution failed: {str(e)}"
            )
