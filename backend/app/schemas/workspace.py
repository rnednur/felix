from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any, Dict


class CanvasItemBase(BaseModel):
    type: str = Field(..., description="Item type: query-result, chart, insight-note, code-block, ml-model")
    x: int = Field(..., description="X position")
    y: int = Field(..., description="Y position")
    width: int = Field(..., description="Width in pixels")
    height: int = Field(..., description="Height in pixels")
    z_index: int = Field(default=0, description="Z-index for layering")
    content: Dict[str, Any] = Field(..., description="Item content (flexible JSONB)")


class CanvasItemCreate(CanvasItemBase):
    pass


class CanvasItemUpdate(BaseModel):
    x: Optional[int] = None
    y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    z_index: Optional[int] = None
    content: Optional[Dict[str, Any]] = None


class CanvasItem(CanvasItemBase):
    id: str
    workspace_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    dataset_id: Optional[str] = None
    dataset_group_id: Optional[str] = None


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    dataset_id: Optional[str] = None
    dataset_group_id: Optional[str] = None


class Workspace(WorkspaceBase):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkspaceWithItems(Workspace):
    items: List[CanvasItem] = []

    class Config:
        from_attributes = True


# AG-UI Event Schemas
class AGUIEventBase(BaseModel):
    event: str
    data: Dict[str, Any]


class CanvasStreamRequest(BaseModel):
    workspace_id: str
    message: str
    dataset_id: Optional[str] = None
    dataset_group_id: Optional[str] = None
