from pydantic import BaseModel
from typing import Dict, Any, List


class VizSuggestionRequest(BaseModel):
    query_id: str


class ChartSuggestion(BaseModel):
    type: str
    spec: Dict[str, Any]


class VizSuggestionsResponse(BaseModel):
    suggestions: List[ChartSuggestion]


class CreateVizRequest(BaseModel):
    query_id: str
    name: str
    chart_type: str
    vega_spec: Dict[str, Any]


class VizResponse(BaseModel):
    id: str
    query_id: str
    name: str
    chart_type: str
    vega_spec: Dict[str, Any]

    class Config:
        from_attributes = True
