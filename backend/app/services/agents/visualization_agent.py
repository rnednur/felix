"""
Visualization Agent - creates optimal charts and visualizations
"""
from typing import Dict, Any
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent import AgentConfig, AgentRequest, AgentResponse, AgentContext
from app.services.duckdb_service import DuckDBService
from app.services.storage_service import StorageService
import json


class VisualizationAgent(BaseAgent):
    """
    Visualization Agent - generates optimal chart specifications

    Creates Vega-Lite chart specs based on data characteristics and user intent.
    Handles various chart types: bar, line, scatter, heatmap, etc.
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.duckdb_service = DuckDBService()
        self.storage_service = StorageService()

    def can_handle(self, request: AgentRequest) -> float:
        """
        Calculate confidence for handling visualization requests

        High confidence for queries like:
        - "Create a chart showing..."
        - "Visualize sales by category"
        - "Plot trend over time"
        - "Show distribution of..."
        """
        return self.calculate_confidence(
            request.query,
            self.config.intent_keywords
        )

    async def process(self, request: AgentRequest, context: AgentContext) -> AgentResponse:
        """
        Process visualization request

        Args:
            request: Agent request with visualization intent
            context: Execution context

        Returns:
            AgentResponse with Vega-Lite spec and chart metadata
        """
        try:
            self.logger.info(f"Creating visualization for dataset: {request.dataset_id}")

            # Get dataset info from database
            from app.core.database import get_db
            from app.models import Dataset

            db = next(get_db())
            dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
            if not dataset:
                raise Exception(f"Dataset {request.dataset_id} not found")

            # In DuckDB, table is always called "dataset"
            table_name = "dataset"

            # Get schema by querying information schema
            schema_query = """
                SELECT column_name, column_type
                FROM (DESCRIBE dataset)
            """
            schema_result = self.duckdb_service.execute_query(schema_query, dataset_id=dataset.id)

            # Convert to schema format
            schema_info = {
                'columns': [
                    {'name': row['column_name'], 'type': row['column_type']}
                    for _, row in schema_result.iterrows()
                ]
            }

            # Sample data for analysis
            sample_query = f"SELECT * FROM {table_name} LIMIT 100"
            sample_data_df = self.duckdb_service.execute_query(sample_query, dataset_id=dataset.id)
            sample_data = sample_data_df.to_dict('records')

            # Determine chart type and axes based on query and data
            chart_suggestion = self._suggest_chart(
                query=request.query,
                schema=schema_info,
                sample_data=sample_data
            )

            # Generate Vega-Lite spec
            vega_spec = self._generate_vega_spec(
                chart_suggestion=chart_suggestion,
                table_name=table_name,
                schema=schema_info
            )

            # Execute query to get data for preview
            if chart_suggestion.get('sql_query'):
                result_df = self.duckdb_service.execute_query(
                    chart_suggestion['sql_query'],
                    dataset_id=dataset.id
                )
                result = result_df.to_dict('records')
                preview_data = result[:50]  # First 50 rows for preview
            else:
                preview_data = sample_data[:50]

            response_data = {
                'summary': f"Created {chart_suggestion['chart_type']} chart",
                'chart_type': chart_suggestion['chart_type'],
                'vega_spec': vega_spec,
                'preview_data': preview_data,
                'sql_query': chart_suggestion.get('sql_query'),
                'explanation': chart_suggestion.get('explanation'),
                'type': 'visualization'
            }

            response = AgentResponse(
                agent_name=self.config.name,
                success=True,
                data=response_data,
                code=chart_suggestion.get('sql_query'),
                metadata={
                    'chart_type': chart_suggestion['chart_type'],
                    'x_axis': chart_suggestion.get('x_field'),
                    'y_axis': chart_suggestion.get('y_field')
                }
            )

            self.log_execution(request, response)
            return response

        except Exception as e:
            self.logger.error(f"Visualization agent failed: {str(e)}", exc_info=True)

            error_response = AgentResponse(
                agent_name=self.config.name,
                success=False,
                data={},
                error=f"Visualization creation failed: {str(e)}"
            )

            self.log_execution(request, error_response)
            return error_response

    def _suggest_chart(
        self,
        query: str,
        schema: Dict[str, Any],
        sample_data: list
    ) -> Dict[str, Any]:
        """
        Suggest optimal chart type based on query and data characteristics
        """
        query_lower = query.lower()

        # Extract column info
        columns = schema.get('columns', [])
        numeric_cols = [c for c in columns if c['type'] in ('INTEGER', 'DOUBLE', 'DECIMAL', 'BIGINT', 'FLOAT')]
        text_cols = [c for c in columns if c['type'] in ('VARCHAR', 'TEXT')]
        date_cols = [c for c in columns if c['type'] in ('DATE', 'TIMESTAMP')]

        # Time series patterns
        if any(word in query_lower for word in ['trend', 'over time', 'timeline', 'time series']) and date_cols:
            return {
                'chart_type': 'line',
                'x_field': date_cols[0]['name'],
                'y_field': numeric_cols[0]['name'] if numeric_cols else text_cols[0]['name'],
                'explanation': 'Line chart for time series analysis',
                'sql_query': None  # Use full dataset
            }

        # Distribution patterns
        if any(word in query_lower for word in ['distribution', 'histogram', 'spread']):
            return {
                'chart_type': 'histogram',
                'x_field': numeric_cols[0]['name'] if numeric_cols else text_cols[0]['name'],
                'explanation': 'Histogram showing distribution',
                'sql_query': None
            }

        # Comparison patterns (bar chart)
        if any(word in query_lower for word in ['by', 'compare', 'breakdown', 'group']) and text_cols and numeric_cols:
            # Group by categorical and aggregate numeric
            return {
                'chart_type': 'bar',
                'x_field': text_cols[0]['name'],
                'y_field': numeric_cols[0]['name'],
                'explanation': f"Bar chart comparing {numeric_cols[0]['name']} by {text_cols[0]['name']}",
                'sql_query': f"SELECT {text_cols[0]['name']}, SUM({numeric_cols[0]['name']}) as total FROM dataset GROUP BY {text_cols[0]['name']} ORDER BY total DESC LIMIT 20"
            }

        # Scatter plot for correlation
        if any(word in query_lower for word in ['correlation', 'relationship', 'scatter', 'vs']) and len(numeric_cols) >= 2:
            return {
                'chart_type': 'scatter',
                'x_field': numeric_cols[0]['name'],
                'y_field': numeric_cols[1]['name'],
                'explanation': f"Scatter plot showing relationship between {numeric_cols[0]['name']} and {numeric_cols[1]['name']}",
                'sql_query': None
            }

        # Default: bar chart
        if text_cols and numeric_cols:
            return {
                'chart_type': 'bar',
                'x_field': text_cols[0]['name'],
                'y_field': numeric_cols[0]['name'],
                'explanation': f"Bar chart of {numeric_cols[0]['name']} by {text_cols[0]['name']}",
                'sql_query': f"SELECT {text_cols[0]['name']}, SUM({numeric_cols[0]['name']}) as total FROM dataset GROUP BY {text_cols[0]['name']} LIMIT 20"
            }

        # Fallback
        return {
            'chart_type': 'bar',
            'x_field': columns[0]['name'] if columns else 'x',
            'y_field': columns[1]['name'] if len(columns) > 1 else 'y',
            'explanation': 'Default bar chart',
            'sql_query': None
        }

    def _generate_vega_spec(
        self,
        chart_suggestion: Dict[str, Any],
        table_name: str,
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate Vega-Lite specification
        """
        chart_type = chart_suggestion['chart_type']
        x_field = chart_suggestion['x_field']
        y_field = chart_suggestion.get('y_field')

        # Base spec
        spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "description": chart_suggestion.get('explanation', 'Chart'),
            "width": 600,
            "height": 400,
            "data": {"name": "table"},
            "mark": {"type": chart_type},
            "encoding": {}
        }

        # Configure encodings based on chart type
        if chart_type == 'bar':
            spec["encoding"] = {
                "x": {"field": x_field, "type": "nominal", "axis": {"labelAngle": -45}},
                "y": {"field": y_field, "type": "quantitative"},
                "tooltip": [
                    {"field": x_field, "type": "nominal"},
                    {"field": y_field, "type": "quantitative"}
                ]
            }

        elif chart_type == 'line':
            spec["encoding"] = {
                "x": {"field": x_field, "type": "temporal"},
                "y": {"field": y_field, "type": "quantitative"},
                "tooltip": [
                    {"field": x_field, "type": "temporal"},
                    {"field": y_field, "type": "quantitative"}
                ]
            }

        elif chart_type == 'scatter':
            spec["encoding"] = {
                "x": {"field": x_field, "type": "quantitative"},
                "y": {"field": y_field, "type": "quantitative"},
                "tooltip": [
                    {"field": x_field, "type": "quantitative"},
                    {"field": y_field, "type": "quantitative"}
                ]
            }

        elif chart_type == 'histogram':
            spec["mark"] = "bar"
            spec["encoding"] = {
                "x": {"field": x_field, "type": "quantitative", "bin": True},
                "y": {"aggregate": "count", "type": "quantitative"}
            }

        return spec
