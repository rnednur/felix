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


# Dataset Group Schemas
class DatasetGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class DatasetGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class DatasetGroupMembershipCreate(BaseModel):
    dataset_id: str
    alias: Optional[str] = None
    display_order: Optional[int] = 0


class DatasetGroupMembershipResponse(BaseModel):
    id: str
    dataset_id: str
    alias: Optional[str]
    display_order: int
    dataset: DatasetResponse
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetGroupResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    memberships: List[DatasetGroupMembershipResponse]

    class Config:
        from_attributes = True


class DatasetGroupListResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    dataset_count: int

    class Config:
        from_attributes = True


# Relationship Schemas
class DatasetGroupRelationshipCreate(BaseModel):
    from_dataset_id: str
    from_column: str
    to_dataset_id: str
    to_column: str
    join_type: str = "INNER"


class DatasetGroupRelationshipResponse(BaseModel):
    id: str
    group_id: str
    from_dataset_id: str
    from_column: str
    to_dataset_id: str
    to_column: str
    join_type: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
