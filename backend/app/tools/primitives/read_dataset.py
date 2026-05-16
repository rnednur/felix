"""
Read Dataset Tool - primitive for reading dataset metadata and schema
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
from app.core.database import SessionLocal
from app.models.dataset import Dataset
from sqlalchemy.orm import Session


class ReadDatasetTool(BaseTool):
    """
    Atomic tool for reading dataset information

    This tool provides read-only access to dataset metadata, schema,
    and basic statistics. It does not execute queries or modify data.
    """

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name="read_dataset",
            description="Read dataset metadata, schema, and basic information",
            category="data_access",
            parameters=[
                ToolParameter(
                    name="dataset_id",
                    type=ToolParameterType.STRING,
                    description="UUID of the dataset to read",
                    required=True
                ),
                ToolParameter(
                    name="include_schema",
                    type=ToolParameterType.BOOLEAN,
                    description="Include column schema information",
                    required=False,
                    default=True
                ),
                ToolParameter(
                    name="include_stats",
                    type=ToolParameterType.BOOLEAN,
                    description="Include basic statistics",
                    required=False,
                    default=False
                )
            ],
            returns={
                "type": "object",
                "properties": {
                    "dataset_id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "row_count": {"type": "integer"},
                    "column_count": {"type": "integer"},
                    "schema": {"type": "object"},
                    "stats": {"type": "object"}
                }
            },
            examples=[
                {
                    "parameters": {
                        "dataset_id": "123e4567-e89b-12d3-a456-426614174000",
                        "include_schema": True,
                        "include_stats": False
                    },
                    "returns": {
                        "dataset_id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Sales Data",
                        "row_count": 1000,
                        "column_count": 5,
                        "schema": {"columns": []}
                    }
                }
            ],
            requires_approval=False,
            is_destructive=False,
            estimated_duration_ms=100
        )

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="Dataset Information Access",
            description="Read metadata and schema information from datasets",
            use_cases=[
                "Get dataset structure before querying",
                "Check available columns and data types",
                "Understand dataset size and dimensions",
                "Retrieve dataset metadata"
            ],
            limitations=[
                "Does not return actual data rows",
                "Does not execute queries",
                "Read-only access"
            ]
        )

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute the read_dataset tool

        Args:
            parameters: Tool parameters

        Returns:
            ToolResult with dataset information
        """
        dataset_id = parameters["dataset_id"]
        include_schema = parameters.get("include_schema", True)
        include_stats = parameters.get("include_stats", False)

        db: Session = SessionLocal()

        try:
            # Get dataset from database
            dataset = db.query(Dataset).filter(
                Dataset.id == dataset_id,
                Dataset.deleted_at.is_(None)
            ).first()

            if not dataset:
                return ToolResult(
                    tool_name="read_dataset",
                    success=False,
                    data={},
                    error=f"Dataset not found: {dataset_id}"
                )

            # Build result data
            result_data = {
                "dataset_id": str(dataset.id),
                "name": dataset.name,
                "description": dataset.description or "",
                "row_count": dataset.row_count or 0,
                "column_count": len(dataset.columns) if dataset.columns else 0,
                "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
                "updated_at": dataset.updated_at.isoformat() if dataset.updated_at else None
            }

            # Add schema if requested
            if include_schema and dataset.columns:
                result_data["schema"] = {
                    "columns": [
                        {
                            "name": col.name,
                            "type": col.type,
                            "nullable": col.nullable,
                            "description": col.description
                        }
                        for col in dataset.columns
                    ]
                }

            # Add stats if requested
            if include_stats and dataset.stats:
                result_data["stats"] = dataset.stats

            return ToolResult(
                tool_name="read_dataset",
                success=True,
                data=result_data,
                metadata={
                    "dataset_name": dataset.name,
                    "include_schema": include_schema,
                    "include_stats": include_stats
                }
            )

        except Exception as e:
            return ToolResult(
                tool_name="read_dataset",
                success=False,
                data={},
                error=f"Failed to read dataset: {str(e)}"
            )
        finally:
            db.close()
