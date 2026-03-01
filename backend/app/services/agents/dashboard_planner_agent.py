"""
Dashboard Planner Agent

Orchestrates automatic dashboard generation from datasets using a 5-phase pipeline:
1. Data Understanding - Profile dataset, identify column types
2. KPI Selection - Select and calculate key metrics
3. Chart Generation - Generate optimal visualizations
4. Summary Table - Create aggregation table
5. Insight Generation - Generate AI insights
"""
from typing import Dict, Any, List, AsyncIterator, Optional
import json
import uuid
import time
import logging
from datetime import datetime

from app.services.agents.base_agent import BaseAgent
from app.services.agents.llm_service import LLMService
from app.services.duckdb_service import DuckDBService
from app.services.storage_service import StorageService
from app.services.data_scouting_service import DataScoutingService
from app.services.dashboard_layout_service import create_dashboard_layout
from app.services.spatial_service import SpatialService

from app.schemas.agent import AgentConfig, AgentRequest, AgentResponse, AgentContext
from app.schemas.dashboard import (
    DashboardGenerateRequest,
    DashboardOptions,
    DashboardProgress,
    DashboardPhase,
    DashboardProgressData,
    DashboardGenerateResult,
    DataProfile,
    ColumnProfile,
    KPIDefinition,
    KPIResult,
    KPIAggregation,
    KPIFormat,
    TrendDirection,
    ChartDefinition,
    ChartResult,
    SummaryTableDefinition,
    SummaryTableResult,
    InsightResult,
    MapResult,
)


logger = logging.getLogger(__name__)


def make_json_serializable(obj: Any) -> Any:
    """
    Recursively convert non-JSON-serializable objects to serializable formats.
    Handles Pandas Timestamps, numpy types, datetime objects, NaN, Inf, etc.
    """
    import pandas as pd
    import numpy as np
    import math

    if obj is None:
        return None
    elif isinstance(obj, bool):
        # Check bool before int since bool is a subclass of int
        return obj
    elif isinstance(obj, str):
        return obj
    elif isinstance(obj, float):
        # Handle NaN and Inf values which are not valid JSON
        if math.isnan(obj):
            return None
        elif math.isinf(obj):
            return None  # Or could use a large number like 1e308
        return obj
    elif isinstance(obj, int):
        return obj
    elif isinstance(obj, (datetime, pd.Timestamp)):
        return obj.isoformat()
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        # Handle numpy NaN and Inf
        val = float(obj)
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return make_json_serializable(obj.tolist())
    elif isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    elif hasattr(obj, 'isoformat'):  # datetime-like objects
        return obj.isoformat()
    elif hasattr(obj, 'tolist'):  # numpy arrays
        return make_json_serializable(obj.tolist())
    elif hasattr(obj, '__dict__'):
        return make_json_serializable(obj.__dict__)
    else:
        # Last resort: convert to string
        return str(obj)


class DashboardPlannerAgent(BaseAgent):
    """
    Dashboard Planner Agent - orchestrates automatic dashboard generation.

    Uses a multi-phase pipeline to analyze data and generate a complete
    dashboard with KPIs, charts, summary tables, and AI insights.
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.llm_service = LLMService(
            default_model=config.llm_config.get('default_model'),
            default_temperature=config.llm_config.get('temperature', 0.3)
        )
        self.duckdb_service = DuckDBService()
        self.storage_service = StorageService()
        self.scouting_service = DataScoutingService()
        self.spatial_service = SpatialService()

    def can_handle(self, request: AgentRequest) -> float:
        """Calculate confidence for handling dashboard generation requests."""
        return self.calculate_confidence(
            request.query,
            self.config.intent_keywords
        )

    async def process(self, request: AgentRequest, context: AgentContext) -> AgentResponse:
        """
        Process a dashboard generation request (non-streaming).

        For streaming generation, use generate_dashboard_streaming() instead.
        """
        try:
            options = DashboardOptions()
            results = []

            async for progress in self.generate_dashboard_streaming(
                dataset_id=request.dataset_id,
                options=options,
                prompt=request.query
            ):
                results.append(progress)

            # Get final result
            final = results[-1] if results else None

            if final and final.phase == DashboardPhase.COMPLETE:
                return AgentResponse(
                    agent_name=self.config.name,
                    success=True,
                    data={"progress": [p.model_dump() for p in results]},
                    metadata={"phase": "complete"}
                )
            else:
                return AgentResponse(
                    agent_name=self.config.name,
                    success=False,
                    data={},
                    error="Dashboard generation did not complete"
                )

        except Exception as e:
            logger.error(f"Dashboard planner failed: {str(e)}", exc_info=True)
            return AgentResponse(
                agent_name=self.config.name,
                success=False,
                data={},
                error=str(e)
            )

    async def generate_dashboard_streaming(
        self,
        dataset_id: str,
        options: DashboardOptions,
        prompt: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> AsyncIterator[DashboardProgress]:
        """
        Generate a dashboard with streaming progress updates.

        Yields DashboardProgress objects at each phase.
        """
        start_time = time.time()

        try:
            # ========== Phase 1: Data Understanding ==========
            yield DashboardProgress(
                phase=DashboardPhase.ANALYZING,
                progress=5,
                message="Analyzing dataset structure..."
            )

            data_profile = await self._phase_data_understanding(dataset_id)

            yield DashboardProgress(
                phase=DashboardPhase.ANALYZING,
                progress=15,
                message=f"Found {data_profile.column_count} columns, {data_profile.row_count:,} rows"
            )

            # ========== Phase 2: KPI Selection ==========
            kpis: List[KPIResult] = []
            if options.include_kpis:
                yield DashboardProgress(
                    phase=DashboardPhase.KPIS,
                    progress=20,
                    message="Identifying key metrics..."
                )

                kpi_definitions = await self._phase_kpi_selection(
                    data_profile, prompt, options.max_kpis
                )

                yield DashboardProgress(
                    phase=DashboardPhase.KPIS,
                    progress=25,
                    message=f"Calculating {len(kpi_definitions)} KPIs..."
                )

                kpis = await self._calculate_kpis(dataset_id, kpi_definitions, data_profile)

                yield DashboardProgress(
                    phase=DashboardPhase.KPIS,
                    progress=35,
                    message=f"Generated {len(kpis)} KPI cards",
                    data=DashboardProgressData(kpis=kpis)
                )

            # ========== Phase 3: Chart Generation ==========
            charts: List[ChartResult] = []
            if options.include_charts:
                yield DashboardProgress(
                    phase=DashboardPhase.CHARTS,
                    progress=40,
                    message="Selecting optimal visualizations..."
                )

                chart_definitions = await self._phase_chart_selection(
                    data_profile, prompt, options.max_charts
                )

                yield DashboardProgress(
                    phase=DashboardPhase.CHARTS,
                    progress=50,
                    message=f"Generating {len(chart_definitions)} charts..."
                )

                charts = await self._generate_charts(dataset_id, chart_definitions)

                yield DashboardProgress(
                    phase=DashboardPhase.CHARTS,
                    progress=65,
                    message=f"Created {len(charts)} visualizations",
                    data=DashboardProgressData(
                        charts=[{"id": c.id, "type": c.chart_type, "title": c.title} for c in charts]
                    )
                )

            # ========== Phase 4: Map Generation (auto-detect spatial data) ==========
            maps: List[MapResult] = []
            spatial_info = await self._detect_spatial_data(dataset_id)
            if spatial_info:  # Returns None if no spatial data found
                yield DashboardProgress(
                    phase=DashboardPhase.CHARTS,  # Reuse charts phase
                    progress=68,
                    message="Generating map visualization..."
                )

                map_result = await self._generate_map(dataset_id, spatial_info, data_profile)
                if map_result:
                    maps.append(map_result)
                    yield DashboardProgress(
                        phase=DashboardPhase.CHARTS,
                        progress=70,
                        message="Map visualization added"
                    )

            # ========== Phase 5: Summary Table ==========
            summary_table: Optional[SummaryTableResult] = None
            if options.include_summary_table and data_profile.categorical_columns:
                yield DashboardProgress(
                    phase=DashboardPhase.SUMMARY,
                    progress=72,
                    message="Creating summary table..."
                )

                summary_table = await self._phase_summary_table(dataset_id, data_profile)

                yield DashboardProgress(
                    phase=DashboardPhase.SUMMARY,
                    progress=80,
                    message="Summary table generated"
                )

            # ========== Phase 5: Insight Generation ==========
            insights: List[InsightResult] = []
            if options.include_insights:
                yield DashboardProgress(
                    phase=DashboardPhase.INSIGHTS,
                    progress=85,
                    message="Generating AI insights..."
                )

                insights = await self._phase_insight_generation(
                    data_profile, kpis, charts, summary_table
                )

                yield DashboardProgress(
                    phase=DashboardPhase.INSIGHTS,
                    progress=95,
                    message=f"Generated {len(insights)} insights",
                    data=DashboardProgressData(insights=[i.content for i in insights])
                )

            # ========== Phase 6: Layout & Save ==========
            yield DashboardProgress(
                phase=DashboardPhase.LAYOUT,
                progress=97,
                message="Creating dashboard layout..."
            )

            # Create workspace and canvas items
            workspace_id = await self._create_workspace(
                dataset_id=dataset_id,
                user_id=user_id,
                kpis=kpis,
                charts=charts,
                summary_table=summary_table,
                insights=insights,
                maps=maps,
                prompt=prompt
            )

            generation_time = time.time() - start_time

            # Final completion - include workspace_id for frontend navigation
            yield DashboardProgress(
                phase=DashboardPhase.COMPLETE,
                progress=100,
                message="Dashboard created successfully!",
                data=DashboardProgressData(
                    kpis=kpis,
                    charts=[{"id": c.id, "type": c.chart_type, "title": c.title} for c in charts],
                    insights=[i.content for i in insights],
                    workspace_id=workspace_id
                )
            )

            logger.info(f"Dashboard generated in {generation_time:.2f}s for dataset {dataset_id}")

        except Exception as e:
            logger.error(f"Dashboard generation failed: {str(e)}", exc_info=True)
            yield DashboardProgress(
                phase=DashboardPhase.ERROR,
                progress=0,
                message=f"Error: {str(e)}"
            )

    # ============== Phase 1: Data Understanding ==============

    async def _phase_data_understanding(self, dataset_id: str) -> DataProfile:
        """Analyze dataset structure and identify column types."""
        # Load schema
        schema = self.storage_service.load_schema(dataset_id)

        # Get row count
        count_query = "SELECT COUNT(*) as cnt FROM dataset"
        count_result = self.duckdb_service.execute_query(count_query, dataset_id=dataset_id)
        row_count = int(count_result.iloc[0]['cnt'])

        # Analyze each column
        columns: List[ColumnProfile] = []
        numeric_cols = []
        categorical_cols = []
        temporal_cols = []
        text_cols = []

        schema_columns = schema.get('columns', [])

        for col_info in schema_columns:
            col_name = col_info['name']
            col_type = col_info.get('dtype', col_info.get('type', 'VARCHAR'))

            # Determine column category
            is_numeric = col_type.upper() in ('INTEGER', 'BIGINT', 'DOUBLE', 'FLOAT', 'DECIMAL', 'NUMERIC', 'REAL')
            is_temporal = col_type.upper() in ('DATE', 'TIMESTAMP', 'DATETIME', 'TIME')
            is_categorical = not is_numeric and not is_temporal

            # Get basic stats
            stats_query = f"""
                SELECT
                    COUNT(*) as total,
                    COUNT(DISTINCT "{col_name}") as unique_count,
                    SUM(CASE WHEN "{col_name}" IS NULL THEN 1 ELSE 0 END) as null_count
                FROM dataset
            """
            stats_result = self.duckdb_service.execute_query(stats_query, dataset_id=dataset_id)
            stats_row = stats_result.iloc[0]

            profile = ColumnProfile(
                name=col_name,
                dtype=col_type,
                is_numeric=is_numeric,
                is_categorical=is_categorical,
                is_temporal=is_temporal,
                null_count=int(stats_row['null_count']),
                null_percentage=float(stats_row['null_count']) / row_count * 100 if row_count > 0 else 0,
                unique_count=int(stats_row['unique_count']),
                unique_percentage=float(stats_row['unique_count']) / row_count * 100 if row_count > 0 else 0
            )

            # Get numeric-specific stats
            if is_numeric:
                numeric_query = f"""
                    SELECT
                        MIN("{col_name}") as min_val,
                        MAX("{col_name}") as max_val,
                        AVG("{col_name}") as mean_val,
                        MEDIAN("{col_name}") as median_val,
                        STDDEV("{col_name}") as std_val
                    FROM dataset
                    WHERE "{col_name}" IS NOT NULL
                """
                try:
                    num_result = self.duckdb_service.execute_query(numeric_query, dataset_id=dataset_id)
                    num_row = num_result.iloc[0]
                    profile.min_value = num_row['min_val']
                    profile.max_value = num_row['max_val']
                    profile.mean_value = float(num_row['mean_val']) if num_row['mean_val'] is not None else None
                    profile.median_value = float(num_row['median_val']) if num_row['median_val'] is not None else None
                    profile.std_value = float(num_row['std_val']) if num_row['std_val'] is not None else None
                except Exception:
                    pass

                numeric_cols.append(col_name)

            # Get top values for categorical
            if is_categorical and profile.unique_count <= 100:
                top_query = f"""
                    SELECT "{col_name}" as value, COUNT(*) as count
                    FROM dataset
                    WHERE "{col_name}" IS NOT NULL
                    GROUP BY "{col_name}"
                    ORDER BY count DESC
                    LIMIT 10
                """
                try:
                    top_result = self.duckdb_service.execute_query(top_query, dataset_id=dataset_id)
                    profile.top_values = [
                        {"value": str(row['value']), "count": int(row['count'])}
                        for _, row in top_result.iterrows()
                    ]
                except Exception:
                    pass

                categorical_cols.append(col_name)

            if is_temporal:
                temporal_cols.append(col_name)

            if not is_numeric and not is_temporal and profile.unique_count > 100:
                text_cols.append(col_name)

            columns.append(profile)

        # Identify potential KPI columns (numeric with reasonable cardinality)
        potential_kpi_cols = [
            c for c in numeric_cols
            if any(kw in c.lower() for kw in ['amount', 'total', 'sum', 'count', 'price', 'cost', 'revenue', 'sales', 'quantity', 'value', 'profit'])
        ] or numeric_cols[:4]

        # Identify potential group-by columns
        potential_groupby = [
            c for c in categorical_cols
            if columns[next(i for i, col in enumerate(columns) if col.name == c)].unique_count <= 50
        ]

        return DataProfile(
            dataset_id=dataset_id,
            row_count=row_count,
            column_count=len(columns),
            columns=columns,
            numeric_columns=numeric_cols,
            categorical_columns=categorical_cols,
            temporal_columns=temporal_cols,
            text_columns=text_cols,
            potential_kpi_columns=potential_kpi_cols,
            potential_group_by_columns=potential_groupby
        )

    # ============== Phase 2: KPI Selection ==============

    async def _phase_kpi_selection(
        self,
        profile: DataProfile,
        prompt: Optional[str],
        max_kpis: int
    ) -> List[KPIDefinition]:
        """Use LLM to select optimal KPIs based on data profile."""

        # Build column info for prompt
        column_info = []
        for col in profile.columns:
            if col.is_numeric:
                info = f"- {col.name} (numeric): min={col.min_value}, max={col.max_value}, mean={col.mean_value:.2f}" if col.mean_value else f"- {col.name} (numeric)"
                column_info.append(info)
            elif col.is_categorical and col.top_values:
                top_vals = ", ".join([v['value'] for v in col.top_values[:3]])
                column_info.append(f"- {col.name} (categorical): top values = {top_vals}")
            elif col.is_temporal:
                column_info.append(f"- {col.name} (date/time)")

        prompt_text = f"""Analyze this dataset and select the {max_kpis} most important KPIs (Key Performance Indicators).

Dataset has {profile.row_count:,} rows and {profile.column_count} columns.

Columns:
{chr(10).join(column_info)}

{f"User focus: {prompt}" if prompt else ""}

Return a JSON array of KPI definitions. Each KPI should have:
- id: unique string id
- name: display name (concise, e.g., "Total Revenue")
- column: source column name
- aggregation: one of "sum", "avg", "count", "min", "max", "count_distinct"
- format: one of "number", "currency", "percentage", "decimal", "compact"

Example:
[
  {{"id": "kpi_1", "name": "Total Sales", "column": "sales_amount", "aggregation": "sum", "format": "currency"}},
  {{"id": "kpi_2", "name": "Average Order Value", "column": "order_value", "aggregation": "avg", "format": "currency"}}
]

Return ONLY the JSON array, no other text."""

        response = await self.llm_service.generate(prompt_text, response_format="json")

        try:
            kpi_data = json.loads(response)
            # Handle case where LLM returns object with nested array
            if isinstance(kpi_data, dict):
                kpi_data = kpi_data.get('kpis', kpi_data.get('data', []))
            if not isinstance(kpi_data, list):
                kpi_data = []
            kpis = []
            for item in kpi_data[:max_kpis]:
                kpi = KPIDefinition(
                    id=item.get('id', f"kpi_{len(kpis)+1}"),
                    name=item['name'],
                    column=item['column'],
                    aggregation=KPIAggregation(item['aggregation']),
                    format=KPIFormat(item.get('format', 'number'))
                )
                kpis.append(kpi)
            return kpis
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse KPI response: {e}")
            # Fallback: generate basic KPIs from numeric columns
            return self._fallback_kpi_selection(profile, max_kpis)

    def _fallback_kpi_selection(self, profile: DataProfile, max_kpis: int) -> List[KPIDefinition]:
        """Fallback KPI selection when LLM fails."""
        kpis = []
        for i, col_name in enumerate(profile.potential_kpi_columns[:max_kpis]):
            kpis.append(KPIDefinition(
                id=f"kpi_{i+1}",
                name=f"Total {col_name.replace('_', ' ').title()}",
                column=col_name,
                aggregation=KPIAggregation.SUM,
                format=KPIFormat.COMPACT
            ))
        return kpis

    async def _calculate_kpis(
        self,
        dataset_id: str,
        definitions: List[KPIDefinition],
        profile: DataProfile
    ) -> List[KPIResult]:
        """Calculate KPI values from dataset."""
        results = []

        for kpi in definitions:
            try:
                # Build aggregation query
                agg_func = {
                    KPIAggregation.SUM: "SUM",
                    KPIAggregation.AVG: "AVG",
                    KPIAggregation.COUNT: "COUNT",
                    KPIAggregation.MIN: "MIN",
                    KPIAggregation.MAX: "MAX",
                    KPIAggregation.COUNT_DISTINCT: "COUNT(DISTINCT",
                    KPIAggregation.MEDIAN: "MEDIAN"
                }.get(kpi.aggregation, "SUM")

                if kpi.aggregation == KPIAggregation.COUNT_DISTINCT:
                    query = f'SELECT {agg_func} "{kpi.column}") as value FROM dataset'
                else:
                    query = f'SELECT {agg_func}("{kpi.column}") as value FROM dataset'

                result = self.duckdb_service.execute_query(query, dataset_id=dataset_id)
                value = result.iloc[0]['value']

                # Format value
                formatted = self._format_kpi_value(value, kpi.format)

                # Calculate trend if temporal column exists
                trend = None
                trend_direction = None
                if profile.temporal_columns:
                    trend, trend_direction = await self._calculate_trend(
                        dataset_id, kpi, profile.temporal_columns[0]
                    )

                results.append(KPIResult(
                    id=kpi.id,
                    name=kpi.name,
                    value=value,
                    formatted_value=formatted,
                    trend=trend,
                    trend_direction=trend_direction,
                    comparison_label="vs previous period" if trend is not None else None,
                    column=kpi.column,
                    aggregation=kpi.aggregation.value
                ))

            except Exception as e:
                logger.warning(f"Failed to calculate KPI {kpi.name}: {e}")

        return results

    def _format_kpi_value(self, value: Any, format_type: KPIFormat) -> str:
        """Format a KPI value for display."""
        if value is None:
            return "N/A"

        try:
            num_value = float(value)

            if format_type == KPIFormat.CURRENCY:
                if num_value >= 1_000_000:
                    return f"${num_value/1_000_000:.1f}M"
                elif num_value >= 1_000:
                    return f"${num_value/1_000:.1f}K"
                return f"${num_value:,.2f}"

            elif format_type == KPIFormat.PERCENTAGE:
                return f"{num_value:.1f}%"

            elif format_type == KPIFormat.COMPACT:
                if num_value >= 1_000_000_000:
                    return f"{num_value/1_000_000_000:.1f}B"
                elif num_value >= 1_000_000:
                    return f"{num_value/1_000_000:.1f}M"
                elif num_value >= 1_000:
                    return f"{num_value/1_000:.1f}K"
                return f"{num_value:,.0f}"

            elif format_type == KPIFormat.INTEGER:
                return f"{int(num_value):,}"

            elif format_type == KPIFormat.DECIMAL:
                return f"{num_value:,.2f}"

            else:  # NUMBER
                if num_value >= 1_000_000:
                    return f"{num_value:,.0f}"
                return f"{num_value:,.2f}"

        except (ValueError, TypeError):
            return str(value)

    async def _calculate_trend(
        self,
        dataset_id: str,
        kpi: KPIDefinition,
        date_column: str
    ) -> tuple[Optional[float], Optional[TrendDirection]]:
        """Calculate trend for a KPI based on date column."""
        try:
            agg_func = kpi.aggregation.value.upper()
            if kpi.aggregation == KPIAggregation.COUNT_DISTINCT:
                agg_expr = f'COUNT(DISTINCT "{kpi.column}")'
            else:
                agg_expr = f'{agg_func}("{kpi.column}")'

            # Get the most recent two periods
            query = f"""
                WITH periods AS (
                    SELECT
                        CASE WHEN "{date_column}" >= (SELECT MAX("{date_column}") - INTERVAL '30 days' FROM dataset)
                             THEN 'current' ELSE 'previous' END as period,
                        {agg_expr} as value
                    FROM dataset
                    WHERE "{date_column}" >= (SELECT MAX("{date_column}") - INTERVAL '60 days' FROM dataset)
                    GROUP BY 1
                )
                SELECT * FROM periods
            """

            result = self.duckdb_service.execute_query(query, dataset_id=dataset_id)

            if len(result) >= 2:
                current = result[result['period'] == 'current']['value'].iloc[0]
                previous = result[result['period'] == 'previous']['value'].iloc[0]

                if previous and previous != 0:
                    trend = ((current - previous) / previous) * 100
                    direction = TrendDirection.UP if trend > 1 else (TrendDirection.DOWN if trend < -1 else TrendDirection.FLAT)
                    return round(trend, 1), direction

        except Exception as e:
            logger.debug(f"Could not calculate trend: {e}")

        return None, None

    # ============== Phase 3: Chart Generation ==============

    async def _phase_chart_selection(
        self,
        profile: DataProfile,
        prompt: Optional[str],
        max_charts: int
    ) -> List[ChartDefinition]:
        """Use LLM to select optimal charts."""

        column_info = []
        for col in profile.columns[:20]:  # Limit columns in prompt
            if col.is_numeric:
                column_info.append(f"- {col.name} (numeric)")
            elif col.is_categorical:
                column_info.append(f"- {col.name} (categorical, {col.unique_count} unique values)")
            elif col.is_temporal:
                column_info.append(f"- {col.name} (date/time)")

        prompt_text = f"""Select the {max_charts} most insightful charts for this dataset.

Dataset: {profile.row_count:,} rows

Columns:
{chr(10).join(column_info)}

{f"User focus: {prompt}" if prompt else ""}

Return a JSON array of chart definitions. Each chart should have:
- id: unique string id
- chart_type: one of "bar", "line", "scatter", "pie", "histogram", "heatmap"
- title: descriptive chart title
- x_field: x-axis column name
- y_field: y-axis column name (optional for histogram/pie)
- aggregation: aggregation function if needed ("sum", "avg", "count")
- explanation: why this chart is useful

Guidelines:
- Use bar charts for comparing categories
- Use line charts for time series (if date column exists)
- Use pie charts for composition (max 5-7 categories)
- Use scatter for correlation between two numeric columns
- Use histogram for distribution of a single numeric column
- Ensure variety in chart types

Return ONLY the JSON array, no other text."""

        response = await self.llm_service.generate(prompt_text, response_format="json")

        try:
            chart_data = json.loads(response)
            # Handle case where LLM returns object with nested array
            if isinstance(chart_data, dict):
                chart_data = chart_data.get('charts', chart_data.get('data', []))
            if not isinstance(chart_data, list):
                chart_data = []
            charts = []
            for item in chart_data[:max_charts]:
                chart = ChartDefinition(
                    id=item.get('id', f"chart_{len(charts)+1}"),
                    chart_type=item['chart_type'],
                    title=item['title'],
                    x_field=item['x_field'],
                    y_field=item.get('y_field'),
                    aggregation=item.get('aggregation'),
                    explanation=item.get('explanation', '')
                )
                charts.append(chart)
            return charts
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse chart response: {e}")
            return self._fallback_chart_selection(profile, max_charts)

    def _fallback_chart_selection(self, profile: DataProfile, max_charts: int) -> List[ChartDefinition]:
        """Fallback chart selection when LLM fails."""
        charts = []

        # Bar chart if categorical + numeric
        if profile.categorical_columns and profile.numeric_columns:
            charts.append(ChartDefinition(
                id="chart_1",
                chart_type="bar",
                title=f"{profile.numeric_columns[0]} by {profile.categorical_columns[0]}",
                x_field=profile.categorical_columns[0],
                y_field=profile.numeric_columns[0],
                aggregation="sum",
                explanation="Bar chart comparing values across categories"
            ))

        # Line chart if temporal + numeric
        if profile.temporal_columns and profile.numeric_columns:
            charts.append(ChartDefinition(
                id="chart_2",
                chart_type="line",
                title=f"{profile.numeric_columns[0]} Over Time",
                x_field=profile.temporal_columns[0],
                y_field=profile.numeric_columns[0],
                aggregation="sum",
                explanation="Time series trend"
            ))

        # Histogram for numeric distribution
        if profile.numeric_columns:
            charts.append(ChartDefinition(
                id="chart_3",
                chart_type="histogram",
                title=f"Distribution of {profile.numeric_columns[0]}",
                x_field=profile.numeric_columns[0],
                explanation="Shows value distribution"
            ))

        return charts[:max_charts]

    async def _generate_charts(
        self,
        dataset_id: str,
        definitions: List[ChartDefinition]
    ) -> List[ChartResult]:
        """Generate Vega-Lite specs and data for charts."""
        results = []

        for chart_def in definitions:
            try:
                # Build query for chart data
                query = self._build_chart_query(chart_def)
                data_df = self.duckdb_service.execute_query(query, dataset_id=dataset_id)
                data = data_df.to_dict('records')[:500]  # Limit data points

                # Skip charts with no data or insufficient data
                if not data or len(data) < 2:
                    logger.info(f"Skipping chart '{chart_def.title}' - insufficient data ({len(data) if data else 0} rows)")
                    continue

                # Generate Vega-Lite spec
                vega_spec = self._generate_vega_spec(chart_def, data)

                results.append(ChartResult(
                    id=chart_def.id,
                    chart_type=chart_def.chart_type,
                    title=chart_def.title,
                    vega_spec=vega_spec,
                    data=data,
                    explanation=chart_def.explanation
                ))

            except Exception as e:
                logger.warning(f"Failed to generate chart {chart_def.title}: {e}")

        return results

    def _build_chart_query(self, chart: ChartDefinition) -> str:
        """Build SQL query for chart data."""
        if chart.chart_type == "histogram":
            return f'SELECT "{chart.x_field}" FROM dataset WHERE "{chart.x_field}" IS NOT NULL LIMIT 5000'

        if chart.aggregation and chart.y_field:
            agg = chart.aggregation.upper()
            return f'''
                SELECT "{chart.x_field}", {agg}("{chart.y_field}") as value
                FROM dataset
                WHERE "{chart.x_field}" IS NOT NULL
                GROUP BY "{chart.x_field}"
                ORDER BY value DESC
                LIMIT 1000
            '''

        if chart.y_field:
            return f'''
                SELECT "{chart.x_field}", "{chart.y_field}"
                FROM dataset
                WHERE "{chart.x_field}" IS NOT NULL AND "{chart.y_field}" IS NOT NULL
                LIMIT 500
            '''

        return f'SELECT "{chart.x_field}" FROM dataset LIMIT 500'

    def _generate_vega_spec(self, chart: ChartDefinition, data: List[Dict]) -> Dict[str, Any]:
        """Generate Vega-Lite specification."""
        base_spec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "title": {"text": chart.title, "fontSize": 16, "anchor": "start"},
            "width": "container",  # Responsive width
            "height": "container",  # Responsive height
            "autosize": {"type": "fit", "contains": "padding"},
            "data": {"values": data},
            "config": {
                "view": {"stroke": "transparent"},
                "axis": {"labelFontSize": 11, "titleFontSize": 12},
            }
        }

        if chart.chart_type == "bar":
            y_field = "value" if chart.aggregation else chart.y_field
            base_spec.update({
                "mark": {"type": "bar", "cornerRadiusTopLeft": 4, "cornerRadiusTopRight": 4},
                "encoding": {
                    "x": {"field": chart.x_field, "type": "nominal", "axis": {"labelAngle": -45}},
                    "y": {"field": y_field, "type": "quantitative"},
                    "color": {"value": "#6366f1"},
                    "tooltip": [
                        {"field": chart.x_field, "type": "nominal"},
                        {"field": y_field, "type": "quantitative", "format": ",.0f"}
                    ]
                }
            })

        elif chart.chart_type == "line":
            y_field = "value" if chart.aggregation else chart.y_field
            base_spec.update({
                "mark": {"type": "line", "point": True},
                "encoding": {
                    "x": {"field": chart.x_field, "type": "temporal"},
                    "y": {"field": y_field, "type": "quantitative"},
                    "color": {"value": "#6366f1"},
                    "tooltip": [
                        {"field": chart.x_field, "type": "temporal"},
                        {"field": y_field, "type": "quantitative", "format": ",.0f"}
                    ]
                }
            })

        elif chart.chart_type == "scatter":
            base_spec.update({
                "mark": {"type": "circle", "opacity": 0.7},
                "encoding": {
                    "x": {"field": chart.x_field, "type": "quantitative"},
                    "y": {"field": chart.y_field, "type": "quantitative"},
                    "color": {"value": "#6366f1"},
                    "tooltip": [
                        {"field": chart.x_field, "type": "quantitative"},
                        {"field": chart.y_field, "type": "quantitative"}
                    ]
                }
            })

        elif chart.chart_type == "pie":
            base_spec.update({
                "mark": {"type": "arc", "innerRadius": 50},
                "encoding": {
                    "theta": {"field": "value", "type": "quantitative"},
                    "color": {"field": chart.x_field, "type": "nominal"},
                    "tooltip": [
                        {"field": chart.x_field, "type": "nominal"},
                        {"field": "value", "type": "quantitative", "format": ",.0f"}
                    ]
                }
            })

        elif chart.chart_type == "histogram":
            base_spec.update({
                "mark": {"type": "bar"},
                "encoding": {
                    "x": {"field": chart.x_field, "type": "quantitative", "bin": True},
                    "y": {"aggregate": "count", "type": "quantitative"},
                    "color": {"value": "#6366f1"}
                }
            })

        else:  # Default bar
            base_spec["mark"] = "bar"
            base_spec["encoding"] = {
                "x": {"field": chart.x_field, "type": "nominal"},
                "y": {"field": chart.y_field or "value", "type": "quantitative"}
            }

        return base_spec

    # ============== Phase 4: Summary Table ==============

    async def _phase_summary_table(
        self,
        dataset_id: str,
        profile: DataProfile
    ) -> Optional[SummaryTableResult]:
        """Generate a summary/pivot table."""
        if not profile.categorical_columns or not profile.numeric_columns:
            return None

        try:
            group_col = profile.categorical_columns[0]
            agg_cols = profile.numeric_columns[:3]

            # Build aggregation expressions
            agg_exprs = [f'SUM("{col}") as "{col}_total"' for col in agg_cols]
            agg_exprs.append('COUNT(*) as "row_count"')

            query = f'''
                SELECT "{group_col}", {", ".join(agg_exprs)}
                FROM dataset
                WHERE "{group_col}" IS NOT NULL
                GROUP BY "{group_col}"
                ORDER BY row_count DESC
                LIMIT 1000
            '''

            result_df = self.duckdb_service.execute_query(query, dataset_id=dataset_id)
            rows = result_df.to_dict('records')
            columns = list(result_df.columns)

            return SummaryTableResult(
                id="summary_table",
                title=f"Summary by {group_col}",
                columns=columns,
                rows=rows,
                total_rows=len(rows)
            )

        except Exception as e:
            logger.warning(f"Failed to create summary table: {e}")
            return None

    # ============== Phase 5: Insight Generation ==============

    async def _phase_insight_generation(
        self,
        profile: DataProfile,
        kpis: List[KPIResult],
        charts: List[ChartResult],
        summary_table: Optional[SummaryTableResult]
    ) -> List[InsightResult]:
        """Generate AI insights for KPIs and charts."""
        insights = []

        # Build context for LLM
        kpi_summary = "\n".join([
            f"- {k.name}: {k.formatted_value}" + (f" ({k.trend:+.1f}%)" if k.trend else "")
            for k in kpis
        ])

        chart_summary = "\n".join([
            f"- {c.title} ({c.chart_type})"
            for c in charts
        ])

        prompt = f"""Generate 3-4 key insights for a dashboard based on this data:

Dataset: {profile.row_count:,} rows, {profile.column_count} columns

Key Metrics (KPIs):
{kpi_summary}

Charts:
{chart_summary}

Generate concise, actionable insights. Each insight should:
1. Highlight a key finding or trend
2. Be specific with numbers when possible
3. Suggest implications or actions

Return a JSON array of insights:
[
  {{"id": "insight_1", "content": "**Key Finding:** The insight text here...", "related_to": "chart_id_or_null", "tags": ["trend", "positive"]}},
  ...
]

Use markdown formatting (**bold** for emphasis). Keep each insight under 100 words.
Return ONLY the JSON array."""

        try:
            response = await self.llm_service.generate(prompt, response_format="json")
            insight_data = json.loads(response)
            # Handle case where LLM returns object with nested array
            if isinstance(insight_data, dict):
                insight_data = insight_data.get('insights', insight_data.get('data', []))
            if not isinstance(insight_data, list):
                insight_data = []

            for item in insight_data:
                insights.append(InsightResult(
                    id=item.get('id', f"insight_{len(insights)+1}"),
                    content=item['content'],
                    related_to=item.get('related_to'),
                    tags=item.get('tags', [])
                ))

        except Exception as e:
            logger.warning(f"Failed to generate insights: {e}")
            # Fallback insight
            insights.append(InsightResult(
                id="insight_1",
                content=f"**Overview:** This dataset contains {profile.row_count:,} records across {profile.column_count} columns.",
                tags=["overview"]
            ))

        return insights

    # ============== Map Generation ==============

    async def _detect_spatial_data(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Detect if dataset has spatial columns (lat/lng)."""
        try:
            # Load sample data for spatial detection
            query = "SELECT * FROM dataset LIMIT 1000"
            sample_df = self.duckdb_service.execute_query(query, dataset_id=dataset_id)
            sample_data = sample_df.to_dict('records')

            if not sample_data:
                return None

            # Use spatial service to detect columns (pass DataFrame, not list)
            spatial_info = self.spatial_service.detect_spatial_columns(sample_df)

            if spatial_info and spatial_info.get('type') == 'coordinates':
                # Generate Kepler.gl config
                config = self.spatial_service.generate_kepler_config(
                    spatial_info,
                    sample_df
                )
                spatial_info['default_config'] = config

                logger.info(f"Detected spatial data in dataset {dataset_id}: {spatial_info['columns']}")
                return spatial_info

            return None

        except Exception as e:
            logger.warning(f"Failed to detect spatial data: {e}")
            return None

    async def _generate_map(
        self,
        dataset_id: str,
        spatial_info: Dict[str, Any],
        profile: DataProfile
    ) -> Optional[MapResult]:
        """Generate a map visualization for spatial data."""
        try:
            # Get map data (limited for performance)
            lat_col = spatial_info['columns']['lat']
            lng_col = spatial_info['columns']['lng']

            query = f'''
                SELECT *
                FROM dataset
                WHERE "{lat_col}" IS NOT NULL
                  AND "{lng_col}" IS NOT NULL
                LIMIT 5000
            '''

            data_df = self.duckdb_service.execute_query(query, dataset_id=dataset_id)
            data = data_df.to_dict('records')

            if not data:
                return None

            # Create map result
            map_result = MapResult(
                id="map_1",
                title="Geographic Distribution",
                data=data,
                spatial_columns={
                    'lat': lat_col,
                    'lng': lng_col
                },
                config=spatial_info.get('default_config'),
                dataset_id=dataset_id,
                row_count=len(data)
            )

            return map_result

        except Exception as e:
            logger.warning(f"Failed to generate map: {e}")
            return None

    # ============== Create Workspace ==============

    async def _create_workspace(
        self,
        dataset_id: str,
        user_id: Optional[str],
        kpis: List[KPIResult],
        charts: List[ChartResult],
        summary_table: Optional[SummaryTableResult],
        insights: List[InsightResult],
        maps: Optional[List[MapResult]] = None,
        prompt: Optional[str] = None
    ) -> str:
        """Create workspace with all canvas items."""
        from app.core.database import get_db
        from app.models import Dataset, Workspace, CanvasItem
        import uuid as uuid_lib

        db = next(get_db())

        try:
            # Get dataset name for workspace title
            dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
            dataset_name = dataset.name if dataset else "Dataset"

            # Generate workspace name
            workspace_name = f"{dataset_name} Dashboard"
            if prompt:
                workspace_name = f"{dataset_name} - {prompt[:30]}..."

            # Calculate layout
            canvas_items, total_height = create_dashboard_layout(
                kpis=kpis,
                charts=charts,
                summary_table=summary_table,
                insights=insights,
                maps=maps
            )

            # Create workspace
            workspace_id = str(uuid_lib.uuid4())
            workspace = Workspace(
                id=workspace_id,
                name=workspace_name,
                description=f"Auto-generated dashboard with {len(kpis)} KPIs and {len(charts)} charts",
                owner_id=user_id or "system",
                dataset_id=dataset_id
            )
            db.add(workspace)

            # Create canvas items
            for item_create in canvas_items:
                item = CanvasItem(
                    id=str(uuid_lib.uuid4()),
                    workspace_id=workspace_id,
                    type=item_create.type,
                    x=item_create.x,
                    y=item_create.y,
                    width=item_create.width,
                    height=item_create.height,
                    z_index=item_create.z_index,
                    content=item_create.content
                )
                db.add(item)

            db.commit()

            logger.info(f"Created workspace {workspace_id} with {len(canvas_items)} items")
            return workspace_id

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create workspace: {e}")
            raise
        finally:
            db.close()
