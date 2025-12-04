from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Workspace, CanvasItem, User
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    Workspace as WorkspaceSchema,
    WorkspaceWithItems,
    CanvasItemCreate,
    CanvasItemUpdate,
    CanvasItem as CanvasItemSchema,
)

router = APIRouter()


@router.get("/", response_model=List[WorkspaceSchema])
def list_workspaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
):
    """List all workspaces owned by the current user"""
    workspaces = (
        db.query(Workspace)
        .filter(
            and_(
                Workspace.owner_id == current_user.id,
                Workspace.deleted_at.is_(None)
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    return workspaces


@router.post("/", response_model=WorkspaceSchema, status_code=status.HTTP_201_CREATED)
def create_workspace(
    workspace_in: WorkspaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new workspace"""
    workspace = Workspace(
        name=workspace_in.name,
        description=workspace_in.description,
        owner_id=current_user.id,
        dataset_id=workspace_in.dataset_id,
        dataset_group_id=workspace_in.dataset_group_id,
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


@router.get("/{workspace_id}", response_model=WorkspaceWithItems)
def get_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a workspace with all its canvas items"""
    workspace = (
        db.query(Workspace)
        .filter(
            and_(
                Workspace.id == workspace_id,
                Workspace.owner_id == current_user.id,
                Workspace.deleted_at.is_(None)
            )
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    return workspace


@router.put("/{workspace_id}", response_model=WorkspaceSchema)
def update_workspace(
    workspace_id: str,
    workspace_in: WorkspaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a workspace"""
    workspace = (
        db.query(Workspace)
        .filter(
            and_(
                Workspace.id == workspace_id,
                Workspace.owner_id == current_user.id,
                Workspace.deleted_at.is_(None)
            )
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    # Update fields
    if workspace_in.name is not None:
        workspace.name = workspace_in.name
    if workspace_in.description is not None:
        workspace.description = workspace_in.description
    if workspace_in.dataset_id is not None:
        workspace.dataset_id = workspace_in.dataset_id
    if workspace_in.dataset_group_id is not None:
        workspace.dataset_group_id = workspace_in.dataset_group_id

    workspace.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(workspace)
    return workspace


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft delete a workspace"""
    workspace = (
        db.query(Workspace)
        .filter(
            and_(
                Workspace.id == workspace_id,
                Workspace.owner_id == current_user.id,
                Workspace.deleted_at.is_(None)
            )
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    workspace.deleted_at = datetime.utcnow()
    db.commit()


# Canvas Items endpoints
@router.post("/{workspace_id}/items", response_model=CanvasItemSchema, status_code=status.HTTP_201_CREATED)
def create_canvas_item(
    workspace_id: str,
    item_in: CanvasItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add an item to the canvas"""
    # Verify workspace ownership
    workspace = (
        db.query(Workspace)
        .filter(
            and_(
                Workspace.id == workspace_id,
                Workspace.owner_id == current_user.id,
                Workspace.deleted_at.is_(None)
            )
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    item = CanvasItem(
        workspace_id=workspace_id,
        type=item_in.type,
        x=item_in.x,
        y=item_in.y,
        width=item_in.width,
        height=item_in.height,
        z_index=item_in.z_index,
        content=item_in.content,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{workspace_id}/items/{item_id}", response_model=CanvasItemSchema)
def update_canvas_item(
    workspace_id: str,
    item_id: str,
    item_in: CanvasItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a canvas item"""
    # Verify workspace ownership
    workspace = (
        db.query(Workspace)
        .filter(
            and_(
                Workspace.id == workspace_id,
                Workspace.owner_id == current_user.id,
                Workspace.deleted_at.is_(None)
            )
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    item = (
        db.query(CanvasItem)
        .filter(
            and_(
                CanvasItem.id == item_id,
                CanvasItem.workspace_id == workspace_id
            )
        )
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Canvas item not found"
        )

    # Update fields
    if item_in.x is not None:
        item.x = item_in.x
    if item_in.y is not None:
        item.y = item_in.y
    if item_in.width is not None:
        item.width = item_in.width
    if item_in.height is not None:
        item.height = item_in.height
    if item_in.z_index is not None:
        item.z_index = item_in.z_index
    if item_in.content is not None:
        item.content = item_in.content

    item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{workspace_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_canvas_item(
    workspace_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a canvas item"""
    # Verify workspace ownership
    workspace = (
        db.query(Workspace)
        .filter(
            and_(
                Workspace.id == workspace_id,
                Workspace.owner_id == current_user.id,
                Workspace.deleted_at.is_(None)
            )
        )
        .first()
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )

    item = (
        db.query(CanvasItem)
        .filter(
            and_(
                CanvasItem.id == item_id,
                CanvasItem.workspace_id == workspace_id
            )
        )
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Canvas item not found"
        )

    db.delete(item)
    db.commit()
