"""
Calculate Stats Tool - primitive for statistical calculations
"""
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from app.tools.base_tool import BaseTool
from app.schemas.tool import (
    ToolSchema,
    ToolParameter,
    ToolParameterType,
    ToolResult,
    ToolCapability
)
from app.services.duckdb_service import DuckDBService


class CalculateStatsTool(BaseTool):
    """
    Atomic tool for calculating statistics

    This tool computes statistical metrics for dataset columns.
    It's a pure computation tool that operates on numeric data.
    """

    def __init__(self):
        super().__init__()
        self.duckdb_service = DuckDBService()

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name="calculate_stats",
            description="Calculate statistical metrics for dataset columns",
            category="computation",
            parameters=[
                ToolParameter(
                    name="dataset_id",
                    type=ToolParameterType.STRING,
                    description="UUID of the dataset",
                    required=True
                ),
                ToolParameter(
                    name="columns",
                    type=ToolParameterType.ARRAY,
                    description="List of columns to analyze (empty for all numeric columns)",
                    required=False,
                    default=[]
                ),
                ToolParameter(
                    name="metrics",
                    type=ToolParameterType.ARRAY,
                    description="Metrics to calculate: mean, median, std, min, max, count, sum, quartiles",
                    required=False,
                    default=["mean", "median", "std", "min", "max", "count"]
                )
            ],
            returns={
                "type": "object",
                "properties": {
                    "statistics": {"type": "object"},
                    "columns_analyzed": {"type": "array"}
                }
            },
            examples=[
                {
                    "parameters": {
                        "dataset_id": "123e4567-e89b-12d3-a456-426614174000",
                        "columns": ["price", "quantity"],
                        "metrics": ["mean", "median", "std"]
                    },
                    "returns": {
                        "statistics": {
                            "price": {"mean": 99.5, "median": 100, "std": 15.2},
                            "quantity": {"mean": 25, "median": 20, "std": 8.5}
                        },
                        "columns_analyzed": ["price", "quantity"]
                    }
                }
            ],
            requires_approval=False,
            is_destructive=False,
            estimated_duration_ms=800
        )

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="Statistical Analysis",
            description="Compute statistical metrics for numeric data",
            use_cases=[
                "Calculate mean, median, standard deviation",
                "Find min/max values",
                "Compute quartiles and percentiles",
                "Count non-null values",
                "Sum columns"
            ],
            limitations=[
                "Only works with numeric columns",
                "Requires data to fit in memory",
                "Does not handle missing values (returns null)"
            ]
        )

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Calculate statistics

        Args:
            parameters: Tool parameters

        Returns:
            ToolResult with statistics
        """
        dataset_id = parameters["dataset_id"]
        columns = parameters.get("columns", [])
        metrics = parameters.get("metrics", ["mean", "median", "std", "min", "max", "count"])

        try:
            # Get dataset data
            query = "SELECT * FROM dataset"
            result = await self.duckdb_service.execute_query(
                dataset_id=dataset_id,
                query=query,
                limit=100000  # Higher limit for stats
            )

            # Convert to DataFrame
            df = pd.DataFrame(result.get("data", []), columns=result.get("columns", []))

            if df.empty:
                return ToolResult(
                    tool_name="calculate_stats",
                    success=False,
                    data={},
                    error="Dataset is empty"
                )

            # Determine columns to analyze
            if not columns:
                # Auto-detect numeric columns
                columns = df.select_dtypes(include=[np.number]).columns.tolist()

            if not columns:
                return ToolResult(
                    tool_name="calculate_stats",
                    success=False,
                    data={},
                    error="No numeric columns found"
                )

            # Calculate statistics
            statistics = {}

            for col in columns:
                if col not in df.columns:
                    continue

                col_stats = {}
                col_data = df[col]

                # Skip non-numeric columns
                if not pd.api.types.is_numeric_dtype(col_data):
                    continue

                # Calculate each metric
                if "mean" in metrics:
                    col_stats["mean"] = float(col_data.mean()) if not col_data.empty else None

                if "median" in metrics:
                    col_stats["median"] = float(col_data.median()) if not col_data.empty else None

                if "std" in metrics:
                    col_stats["std"] = float(col_data.std()) if not col_data.empty else None

                if "min" in metrics:
                    col_stats["min"] = float(col_data.min()) if not col_data.empty else None

                if "max" in metrics:
                    col_stats["max"] = float(col_data.max()) if not col_data.empty else None

                if "count" in metrics:
                    col_stats["count"] = int(col_data.count())

                if "sum" in metrics:
                    col_stats["sum"] = float(col_data.sum()) if not col_data.empty else None

                if "quartiles" in metrics:
                    q1, q2, q3 = col_data.quantile([0.25, 0.5, 0.75])
                    col_stats["quartiles"] = {
                        "q1": float(q1),
                        "q2": float(q2),
                        "q3": float(q3)
                    }

                statistics[col] = col_stats

            return ToolResult(
                tool_name="calculate_stats",
                success=True,
                data={
                    "statistics": statistics,
                    "columns_analyzed": list(statistics.keys()),
                    "metrics_calculated": metrics
                },
                metadata={
                    "dataset_id": dataset_id,
                    "column_count": len(statistics),
                    "row_count": len(df)
                }
            )

        except Exception as e:
            return ToolResult(
                tool_name="calculate_stats",
                success=False,
                data={},
                error=f"Statistics calculation failed: {str(e)}"
            )
