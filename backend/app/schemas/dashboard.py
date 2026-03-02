"""
Dashboard Generation Schemas

Pydantic models for the one-click dashboard generation feature.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class KPIAggregation(str, Enum):
    """Aggregation types for KPIs"""
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"
    COUNT_DISTINCT = "count_distinct"


class KPIFormat(str, Enum):
    """Display formats for KPI values"""
    NUMBER = "number"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    DECIMAL = "decimal"
    INTEGER = "integer"
    COMPACT = "compact"  # 1.2K, 3.4M, etc.


class TrendDirection(str, Enum):
    """Trend direction indicators"""
    UP = "up"
    DOWN = "down"
    FLAT = "flat"


class DashboardPhase(str, Enum):
    """Dashboard generation phases"""
    ANALYZING = "analyzing"
    KPIS = "kpis"
    CHARTS = "charts"
    SUMMARY = "summary"
    INSIGHTS = "insights"
    LAYOUT = "layout"
    COMPLETE = "complete"
    ERROR = "error"


# ============== Request Schemas ==============

class DashboardOptions(BaseModel):
    """Options for dashboard generation"""
    include_kpis: bool = Field(default=True, description="Include KPI cards")
    include_charts: bool = Field(default=True, description="Include visualizations")
    include_insights: bool = Field(default=True, description="Include AI insights")
    include_summary_table: bool = Field(default=True, description="Include summary/pivot table")
    max_charts: int = Field(default=6, ge=1, le=12, description="Maximum charts to generate")
    max_kpis: int = Field(default=4, ge=1, le=8, description="Maximum KPIs to generate")


class DashboardGenerateRequest(BaseModel):
    """Request to generate a dashboard"""
    dataset_id: str = Field(..., description="Dataset ID to generate dashboard from")
    prompt: Optional[str] = Field(None, description="Optional focus prompt (e.g., 'focus on sales metrics')")
    options: DashboardOptions = Field(default_factory=DashboardOptions)
    name: Optional[str] = Field(None, description="Optional dashboard name")


# ============== KPI Schemas ==============

class KPIDefinition(BaseModel):
    """Definition of a KPI to calculate"""
    id: str = Field(..., description="Unique KPI ID")
    name: str = Field(..., description="Display name")
    column: str = Field(..., description="Source column")
    aggregation: KPIAggregation = Field(..., description="Aggregation function")
    format: KPIFormat = Field(default=KPIFormat.NUMBER, description="Display format")
    trend_column: Optional[str] = Field(None, description="Column to calculate trend from (usually date)")
    comparison: Optional[str] = Field(None, description="Comparison type: vs_prev_period, vs_target")
    filter_sql: Optional[str] = Field(None, description="Optional SQL filter")


class KPIResult(BaseModel):
    """Calculated KPI result"""
    id: str
    name: str
    value: Any = Field(..., description="Raw value")
    formatted_value: str = Field(..., description="Formatted display value")
    trend: Optional[float] = Field(None, description="Trend percentage change")
    trend_direction: Optional[TrendDirection] = Field(None, description="Trend direction")
    comparison_label: Optional[str] = Field(None, description="Comparison label (e.g., 'vs last month')")
    column: str = Field(..., description="Source column")
    aggregation: str = Field(..., description="Aggregation used")
    sparkline_data: Optional[List[float]] = Field(None, description="Optional sparkline data points")


# ============== Chart Schemas ==============

class ChartDefinition(BaseModel):
    """Definition of a chart to generate"""
    id: str
    chart_type: str = Field(..., description="Chart type: bar, line, scatter, pie, heatmap, histogram")
    title: str
    x_field: str
    y_field: Optional[str] = None
    color_field: Optional[str] = None
    aggregation: Optional[str] = None
    sql_query: Optional[str] = None
    explanation: str = Field(..., description="Why this chart was chosen")


class ChartResult(BaseModel):
    """Generated chart result"""
    id: str
    chart_type: str
    title: str
    vega_spec: Dict[str, Any] = Field(..., description="Vega-Lite specification")
    data: List[Dict[str, Any]] = Field(..., description="Chart data")
    insight: Optional[str] = Field(None, description="AI insight for this chart")
    explanation: str


# ============== Summary Table Schemas ==============

class SummaryTableDefinition(BaseModel):
    """Definition of summary/pivot table"""
    id: str
    title: str
    group_by_columns: List[str]
    aggregate_columns: List[Dict[str, str]]  # [{"column": "sales", "aggregation": "sum"}]
    sql_query: str


class SummaryTableResult(BaseModel):
    """Generated summary table result"""
    id: str
    title: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int
    insight: Optional[str] = None


# ============== Insight Schemas ==============

class InsightResult(BaseModel):
    """AI-generated insight"""
    id: str
    content: str = Field(..., description="Markdown content of insight")
    related_to: Optional[str] = Field(None, description="ID of related chart/KPI")
    tags: List[str] = Field(default_factory=list)


# ============== Map Schemas ==============

class MapResult(BaseModel):
    """Generated map visualization result"""
    id: str
    title: str = Field(default="Geographic Distribution", description="Map title")
    data: List[Dict[str, Any]] = Field(..., description="Data points for the map")
    spatial_columns: Dict[str, str] = Field(..., description="Lat/lng column mapping, e.g., {'lat': 'latitude', 'lng': 'longitude'}")
    config: Optional[Dict[str, Any]] = Field(None, description="Map configuration")
    dataset_id: str = Field(..., description="Source dataset ID")
    row_count: int = Field(..., description="Number of data points")


# ============== Progress/Response Schemas ==============

class DashboardProgressData(BaseModel):
    """Optional data included in progress updates"""
    kpis: Optional[List[KPIResult]] = None
    charts: Optional[List[Dict[str, Any]]] = None  # Partial chart info
    insights: Optional[List[str]] = None
    workspace_id: Optional[str] = None  # Set on completion


class DashboardProgress(BaseModel):
    """Progress update during dashboard generation"""
    phase: DashboardPhase
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    message: str
    data: Optional[DashboardProgressData] = None


class DashboardGenerateResult(BaseModel):
    """Final result of dashboard generation"""
    workspace_id: str
    name: str
    dataset_id: str
    kpi_count: int
    chart_count: int
    insight_count: int
    summary_table_included: bool
    generation_time_seconds: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DashboardGenerateError(BaseModel):
    """Error response for dashboard generation"""
    error: str
    details: Optional[str] = None
    phase: Optional[DashboardPhase] = None


# ============== Data Profile Schemas ==============

class ColumnProfile(BaseModel):
    """Profile of a single column"""
    name: str
    dtype: str
    is_numeric: bool = False
    is_categorical: bool = False
    is_temporal: bool = False
    is_text: bool = False
    null_count: int = 0
    null_percentage: float = 0.0
    unique_count: int = 0
    unique_percentage: float = 0.0
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    std_value: Optional[float] = None
    top_values: Optional[List[Dict[str, Any]]] = None  # [{"value": "X", "count": 10}]
    sample_values: Optional[List[Any]] = None


class DataProfile(BaseModel):
    """Complete profile of a dataset"""
    dataset_id: str
    row_count: int
    column_count: int
    columns: List[ColumnProfile]
    numeric_columns: List[str] = Field(default_factory=list)
    categorical_columns: List[str] = Field(default_factory=list)
    temporal_columns: List[str] = Field(default_factory=list)
    text_columns: List[str] = Field(default_factory=list)
    potential_kpi_columns: List[str] = Field(default_factory=list)
    potential_group_by_columns: List[str] = Field(default_factory=list)


# ============== Layout Schemas ==============

class LayoutPosition(BaseModel):
    """Position and size for a canvas item"""
    x: int
    y: int
    width: int
    height: int
    z_index: int = 0


class LayoutItem(BaseModel):
    """Item to be positioned in layout"""
    id: str
    type: str  # 'kpi-card', 'chart', 'insight-note', 'query-result'
    content: Dict[str, Any]
    position: Optional[LayoutPosition] = None


class DashboardLayout(BaseModel):
    """Complete dashboard layout"""
    items: List[LayoutItem]
    total_width: int = 1200
    total_height: int = 0  # Calculated based on items
