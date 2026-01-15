"""
Generate Chart Tool - primitive for creating visualizations
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


class GenerateChartTool(BaseTool):
    """
    Atomic tool for generating chart specifications

    This tool creates visualization specifications (not rendered charts).
    It follows the Vega-Lite spec format for maximum compatibility.
    """

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name="generate_chart",
            description="Generate a chart specification for data visualization",
            category="visualization",
            parameters=[
                ToolParameter(
                    name="chart_type",
                    type=ToolParameterType.STRING,
                    description="Type of chart",
                    required=True,
                    enum=["bar", "line", "scatter", "pie", "histogram", "heatmap", "area"]
                ),
                ToolParameter(
                    name="x_column",
                    type=ToolParameterType.STRING,
                    description="Column for X axis",
                    required=True
                ),
                ToolParameter(
                    name="y_column",
                    type=ToolParameterType.STRING,
                    description="Column for Y axis",
                    required=False
                ),
                ToolParameter(
                    name="title",
                    type=ToolParameterType.STRING,
                    description="Chart title",
                    required=False,
                    default=""
                ),
                ToolParameter(
                    name="color_column",
                    type=ToolParameterType.STRING,
                    description="Column for color encoding",
                    required=False
                ),
                ToolParameter(
                    name="aggregate",
                    type=ToolParameterType.STRING,
                    description="Aggregation function",
                    required=False,
                    enum=["sum", "mean", "count", "median", "min", "max"]
                )
            ],
            returns={
                "type": "object",
                "properties": {
                    "spec": {"type": "object"},
                    "chart_type": {"type": "string"},
                    "description": {"type": "string"}
                }
            },
            examples=[
                {
                    "parameters": {
                        "chart_type": "bar",
                        "x_column": "category",
                        "y_column": "sales",
                        "title": "Sales by Category",
                        "aggregate": "sum"
                    },
                    "returns": {
                        "spec": {"mark": "bar", "encoding": {}},
                        "chart_type": "bar",
                        "description": "Bar chart showing sum of sales by category"
                    }
                }
            ],
            requires_approval=False,
            is_destructive=False,
            estimated_duration_ms=100
        )

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="Chart Generation",
            description="Create visualization specifications for data",
            use_cases=[
                "Generate bar charts for categorical data",
                "Create line charts for time series",
                "Build scatter plots for correlations",
                "Make pie charts for proportions",
                "Generate histograms for distributions"
            ],
            limitations=[
                "Generates specifications only (not rendered images)",
                "Requires valid column names",
                "Limited to supported chart types"
            ]
        )

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Generate chart specification

        Args:
            parameters: Tool parameters

        Returns:
            ToolResult with chart spec
        """
        chart_type = parameters["chart_type"]
        x_column = parameters["x_column"]
        y_column = parameters.get("y_column")
        title = parameters.get("title", "")
        color_column = parameters.get("color_column")
        aggregate = parameters.get("aggregate")

        try:
            # Build Vega-Lite specification
            spec = {
                "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
                "mark": chart_type,
                "encoding": {}
            }

            # Add title if provided
            if title:
                spec["title"] = title

            # Build encoding
            if chart_type in ["bar", "line", "area"]:
                spec["encoding"]["x"] = {"field": x_column, "type": "nominal"}
                if y_column:
                    y_encoding = {"field": y_column, "type": "quantitative"}
                    if aggregate:
                        y_encoding["aggregate"] = aggregate
                    spec["encoding"]["y"] = y_encoding

            elif chart_type == "scatter":
                spec["encoding"]["x"] = {"field": x_column, "type": "quantitative"}
                if y_column:
                    spec["encoding"]["y"] = {"field": y_column, "type": "quantitative"}

            elif chart_type == "pie":
                spec["mark"] = {"type": "arc", "innerRadius": 0}
                spec["encoding"]["theta"] = {"field": y_column, "type": "quantitative"}
                spec["encoding"]["color"] = {"field": x_column, "type": "nominal"}

            elif chart_type == "histogram":
                spec["mark"] = "bar"
                spec["encoding"]["x"] = {
                    "field": x_column,
                    "type": "quantitative",
                    "bin": True
                }
                spec["encoding"]["y"] = {"aggregate": "count", "type": "quantitative"}

            elif chart_type == "heatmap":
                spec["mark"] = "rect"
                spec["encoding"]["x"] = {"field": x_column, "type": "nominal"}
                spec["encoding"]["y"] = {"field": y_column, "type": "nominal"}
                if color_column:
                    spec["encoding"]["color"] = {"field": color_column, "type": "quantitative"}

            # Add color encoding if specified
            if color_column and chart_type not in ["pie", "heatmap"]:
                spec["encoding"]["color"] = {"field": color_column, "type": "nominal"}

            # Generate description
            description = f"{chart_type.capitalize()} chart"
            if aggregate:
                description += f" showing {aggregate} of {y_column or x_column}"
            if x_column:
                description += f" by {x_column}"

            return ToolResult(
                tool_name="generate_chart",
                success=True,
                data={
                    "spec": spec,
                    "chart_type": chart_type,
                    "description": description,
                    "x_column": x_column,
                    "y_column": y_column,
                    "title": title
                },
                metadata={
                    "chart_type": chart_type,
                    "has_aggregation": aggregate is not None,
                    "has_color_encoding": color_column is not None
                }
            )

        except Exception as e:
            return ToolResult(
                tool_name="generate_chart",
                success=False,
                data={},
                error=f"Chart generation failed: {str(e)}"
            )
