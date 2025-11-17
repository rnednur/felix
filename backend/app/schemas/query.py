from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class NLQueryRequest(BaseModel):
    dataset_id: str
    query: str


class SQLQueryRequest(BaseModel):
    dataset_id: str
    sql: str


class QueryResponse(BaseModel):
    query_id: str
    sql: str
    rows: List[Dict[str, Any]]
    total_rows: int
    execution_time_ms: Optional[int] = None
    retrieved_columns: Optional[List[str]] = None
    status: str

    class Config:
        from_attributes = True
