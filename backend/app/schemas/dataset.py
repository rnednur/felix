from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None


class DatasetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    source_type: str
    status: str
    row_count: int
    size_bytes: int
    dataset_version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetPreviewResponse(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int


class SchemaColumn(BaseModel):
    name: str
    dtype: str
    nullable: bool
    stats: Dict[str, Any]
    tags: List[str]
    embedding_index: int


class SchemaResponse(BaseModel):
    version: int
    columns: List[SchemaColumn]
    computed_at: str
    total_rows: int
