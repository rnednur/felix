"""
Annotation schemas for dashboard editing via visual feedback
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, Literal
from datetime import datetime


class AnnotationRequest(BaseModel):
    """Request containing annotation data from frontend"""
    model_config = ConfigDict(populate_by_name=True)
    
    element_selector: str = Field(
        ...,
        alias="elementSelector",
        description="CSS selector to identify the annotated element"
    )
    element_type: str = Field(
        ...,
        alias="elementType",
        description="Type of element: kpi, chart, insight, table, map, code"
    )
    element_config: Dict[str, Any] = Field(
        default_factory=dict,
        alias="elementConfig",
        description="Current configuration of the element"
    )
    feedback: str = Field(
        ...,
        description="User's feedback/request for changes"
    )
    workspace_id: Optional[str] = Field(
        None,
        alias="workspaceId",
        description="Optional workspace context"
    )
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the annotation"
    )


class DashboardEdit(BaseModel):
    """Structured edit instruction for a dashboard element"""
    model_config = ConfigDict(populate_by_name=True)

    element_id: str = Field(
        ...,
        alias="elementId",
        serialization_alias="elementId",
        description="ID of the element to edit"
    )
    action: Literal["modify", "add", "remove"] = Field(
        ...,
        description="Type of edit action"
    )
    changes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Changes to apply to the element"
    )
    reasoning: Optional[str] = Field(
        None,
        description="Agent's reasoning for the edit"
    )


class AnnotationResponse(BaseModel):
    """Response from annotation processing"""
    success: bool = Field(
        ...,
        description="Whether the annotation was processed successfully"
    )
    edit: Optional[DashboardEdit] = Field(
        None,
        description="The edit to apply, if successful"
    )
    message: Optional[str] = Field(
        None,
        description="Additional message or error description"
    )


class IntentAnalysis(BaseModel):
    """Analysis of user intent from annotation feedback"""
    intent_type: str = Field(
        ...,
        description="Type of intent: change_chart_type, modify_styling, update_data, reword_insight, remove_element"
    )
    target_element: str = Field(
        ...,
        description="Element being targeted"
    )
    specific_changes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Specific changes requested"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in intent analysis"
    )


class AnnotationBatchRequest(BaseModel):
    """Request for batch annotation processing"""
    annotations: list[AnnotationRequest] = Field(
        ...,
        description="List of annotations to process"
    )
    apply_immediately: bool = Field(
        default=False,
        description="Whether to apply changes immediately"
    )


class AnnotationBatchResponse(BaseModel):
    """Response from batch annotation processing"""
    success: bool
    edits: list[DashboardEdit] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class KPIContext(BaseModel):
    """KPI data for context-aware creation"""
    id: str
    name: str
    value: Any = None
    formatted_value: str = Field(default="", alias="formattedValue")
    trend: Optional[float] = None
    trend_direction: Optional[str] = Field(default=None, alias="trendDirection")

    model_config = ConfigDict(populate_by_name=True)


class ChartContext(BaseModel):
    """Chart data for context-aware creation"""
    id: str
    chart_type: str = Field(alias="chartType")
    title: Optional[str] = None
    data: list[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class DashboardContext(BaseModel):
    """Full dashboard context for smart element creation"""
    model_config = ConfigDict(populate_by_name=True)

    dataset_id: Optional[str] = Field(default=None, alias="datasetId")
    workspace_id: Optional[str] = Field(default=None, alias="workspaceId")
    kpis: list[KPIContext] = Field(default_factory=list)
    charts: list[ChartContext] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list, description="Available dataset columns")
    sample_data: list[Dict[str, Any]] = Field(
        default_factory=list,
        alias="sampleData",
        description="Sample rows from dataset"
    )


class ContextCreateRequest(BaseModel):
    """Request to create element with full dashboard context"""
    model_config = ConfigDict(populate_by_name=True)

    feedback: str = Field(..., description="User's request for what to create")
    context: DashboardContext = Field(..., description="Full dashboard context")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
