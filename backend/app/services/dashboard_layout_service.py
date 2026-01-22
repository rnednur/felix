"""
Dashboard Layout Service

Handles intelligent positioning of dashboard items (KPIs, charts, tables, insights)
in a grid-based layout system.

Layout Structure:
┌──────────┬──────────┬──────────┬──────────┐
│   KPI 1  │   KPI 2  │   KPI 3  │   KPI 4  │  Row 1: KPIs (150px height)
├──────────┴──────────┼──────────┴──────────┤
│      Chart 1        │      Chart 2        │  Row 2+: Charts (400px each)
│    + Insight 1      │    + Insight 2      │
├─────────────────────┼─────────────────────┤
│      Chart 3        │      Chart 4        │
│    + Insight 3      │    + Insight 4      │
├─────────────────────┴─────────────────────┤
│            Summary Table                   │  Full width (300px)
└───────────────────────────────────────────┘
"""
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime


def make_json_serializable(obj: Any) -> Any:
    """
    Recursively convert non-JSON-serializable objects to serializable formats.
    Handles Pandas Timestamps, numpy types, datetime objects, etc.
    """
    try:
        import pandas as pd
        import numpy as np

        if obj is None:
            return None
        elif isinstance(obj, (str, int, float, bool)):
            return obj
        elif isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, (np.bool_,)):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [make_json_serializable(item) for item in obj]
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif hasattr(obj, 'tolist'):
            return obj.tolist()
        else:
            return str(obj)
    except Exception:
        return str(obj)


from app.schemas.dashboard import (
    KPIResult,
    ChartResult,
    SummaryTableResult,
    InsightResult,
    LayoutItem,
    LayoutPosition,
    DashboardLayout,
)
from app.schemas.workspace import CanvasItemCreate
import uuid


class DashboardLayoutService:
    """
    Service for calculating dashboard layout positions.

    Uses a grid-based system with:
    - Total width: 1200px
    - KPI row: 4 columns, 150px height each
    - Chart grid: 2 columns, 400px height each
    - Summary table: Full width, 300px height
    - Insights: Attached below related charts (100px height)
    """

    # Layout constants - generous sizing for visibility
    TOTAL_WIDTH = 1400  # Wider canvas
    PADDING = 30
    GAP = 25

    # KPI dimensions - taller for better readability
    KPI_COLUMNS = 4
    KPI_HEIGHT = 180

    # Chart dimensions - much larger for full visibility
    CHART_COLUMNS = 2
    CHART_HEIGHT = 500  # Increased from 400

    # Insight dimensions - taller to show content
    INSIGHT_HEIGHT = 180

    # Summary table dimensions
    SUMMARY_TABLE_HEIGHT = 400

    def __init__(self):
        self.current_y = self.PADDING

    def calculate_layout(
        self,
        kpis: List[KPIResult],
        charts: List[ChartResult],
        summary_table: Optional[SummaryTableResult],
        insights: List[InsightResult]
    ) -> List[CanvasItemCreate]:
        """
        Calculate positions for all dashboard items and return CanvasItemCreate objects.

        Layout order (top to bottom):
        1. KPIs in a row
        2. Charts in 2-column grid
        3. Summary table (full width)
        4. All insights at the bottom

        Args:
            kpis: List of KPI results
            charts: List of chart results
            summary_table: Optional summary table result
            insights: List of insight results

        Returns:
            List of CanvasItemCreate objects ready for database insertion
        """
        self.current_y = self.PADDING
        canvas_items: List[CanvasItemCreate] = []

        # 1. Position KPIs in top row
        if kpis:
            kpi_items = self._position_kpis(kpis)
            canvas_items.extend(kpi_items)

        # 2. Position charts in clean 2-column grid
        if charts:
            chart_items = self._position_charts(charts, {})  # No inline insights
            canvas_items.extend(chart_items)

        # 3. Position summary table (full width)
        if summary_table:
            table_item = self._position_summary_table(summary_table)
            canvas_items.append(table_item)

        # 4. Position ALL insights at the bottom as a summary section
        if insights:
            insight_items = self._position_remaining_insights(insights)
            canvas_items.extend(insight_items)

        return canvas_items

    def _position_kpis(self, kpis: List[KPIResult]) -> List[CanvasItemCreate]:
        """Position KPIs in top row, up to 4 columns."""
        items = []
        num_kpis = min(len(kpis), self.KPI_COLUMNS)

        # Calculate width per KPI card
        available_width = self.TOTAL_WIDTH - (2 * self.PADDING) - ((num_kpis - 1) * self.GAP)
        kpi_width = available_width // num_kpis

        for i, kpi in enumerate(kpis[:num_kpis]):
            x = self.PADDING + (i * (kpi_width + self.GAP))

            # Serialize KPI content to handle numpy types
            content = make_json_serializable({
                "id": kpi.id,
                "name": kpi.name,
                "value": kpi.value,
                "formattedValue": kpi.formatted_value,
                "trend": kpi.trend,
                "trendDirection": kpi.trend_direction.value if kpi.trend_direction else None,
                "comparisonLabel": kpi.comparison_label,
                "column": kpi.column,
                "aggregation": kpi.aggregation,
                "sparklineData": kpi.sparkline_data,
            })

            item = CanvasItemCreate(
                type="kpi-card",
                x=x,
                y=self.current_y,
                width=kpi_width,
                height=self.KPI_HEIGHT,
                z_index=1,
                content=content
            )
            items.append(item)

        # Update current Y position
        self.current_y += self.KPI_HEIGHT + self.GAP

        return items

    def _position_charts(
        self,
        charts: List[ChartResult],
        insight_lookup: Dict[str, InsightResult]
    ) -> List[CanvasItemCreate]:
        """Position charts in a clean 2-column grid layout."""
        items = []

        # Calculate chart width - generous spacing
        available_width = self.TOTAL_WIDTH - (2 * self.PADDING) - self.GAP
        chart_width = available_width // self.CHART_COLUMNS

        # Position charts in rows of 2 - clean grid without inline insights
        for i, chart in enumerate(charts):
            col = i % self.CHART_COLUMNS
            row = i // self.CHART_COLUMNS

            # Calculate position
            x = self.PADDING + (col * (chart_width + self.GAP))
            chart_y = self.current_y + (row * (self.CHART_HEIGHT + self.GAP))

            # Chart content - serialize to handle Timestamps
            chart_content = make_json_serializable({
                "chartType": chart.chart_type,
                "title": chart.title,
                "vegaSpec": chart.vega_spec,
                "data": chart.data[:100] if chart.data else [],  # Limit data for canvas storage
                "insight": chart.insight,
                "explanation": chart.explanation,
            })

            chart_item = CanvasItemCreate(
                type="chart",
                x=x,
                y=chart_y,
                width=chart_width,
                height=self.CHART_HEIGHT,
                z_index=1,
                content=chart_content
            )
            items.append(chart_item)

        # Update current Y position based on number of chart rows
        num_rows = (len(charts) + self.CHART_COLUMNS - 1) // self.CHART_COLUMNS
        self.current_y += num_rows * (self.CHART_HEIGHT + self.GAP)

        return items

    def _position_summary_table(self, table: SummaryTableResult) -> CanvasItemCreate:
        """Position summary table at full width."""
        table_width = self.TOTAL_WIDTH - (2 * self.PADDING)

        # Serialize table content to handle Timestamps
        content = make_json_serializable({
            "title": table.title,
            "columns": table.columns,
            "rows": table.rows[:50] if table.rows else [],  # Limit rows for display
            "totalRows": table.total_rows,
            "insight": table.insight,
            "isSummaryTable": True,
        })

        item = CanvasItemCreate(
            type="query-result",
            x=self.PADDING,
            y=self.current_y,
            width=table_width,
            height=self.SUMMARY_TABLE_HEIGHT,
            z_index=1,
            content=content
        )

        self.current_y += self.SUMMARY_TABLE_HEIGHT + self.GAP

        return item

    def _position_remaining_insights(
        self,
        insights: List[InsightResult]
    ) -> List[CanvasItemCreate]:
        """Position insights in a 2-column grid layout."""
        items = []

        # Use 2-column layout like charts
        available_width = self.TOTAL_WIDTH - (2 * self.PADDING) - self.GAP
        insight_width = available_width // 2

        for i, insight in enumerate(insights):
            col = i % 2
            row = i // 2

            x = self.PADDING + (col * (insight_width + self.GAP))
            y = self.current_y + (row * (self.INSIGHT_HEIGHT + self.GAP))

            content = {
                "content": insight.content,
                "aiGenerated": True,
                "tags": insight.tags,
            }

            item = CanvasItemCreate(
                type="insight-note",
                x=x,
                y=y,
                width=insight_width,
                height=self.INSIGHT_HEIGHT,
                z_index=1,
                content=content
            )
            items.append(item)

        # Update current Y based on number of rows
        num_rows = (len(insights) + 1) // 2  # 2 columns
        self.current_y += num_rows * (self.INSIGHT_HEIGHT + self.GAP)

        return items

    def calculate_total_height(self) -> int:
        """Return the total height of the layout."""
        return self.current_y


def create_dashboard_layout(
    kpis: List[KPIResult],
    charts: List[ChartResult],
    summary_table: Optional[SummaryTableResult],
    insights: List[InsightResult]
) -> Tuple[List[CanvasItemCreate], int]:
    """
    Convenience function to create dashboard layout.

    Returns:
        Tuple of (canvas_items, total_height)
    """
    service = DashboardLayoutService()
    items = service.calculate_layout(kpis, charts, summary_table, insights)
    return items, service.calculate_total_height()
