from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.core.database import get_db
from app.models.dataset import DatasetGroup, DatasetGroupMembership, Dataset
from app.schemas.dataset import (
    DatasetGroupCreate,
    DatasetGroupUpdate,
    DatasetGroupResponse,
    DatasetGroupListResponse,
    DatasetGroupMembershipCreate,
    DatasetGroupMembershipResponse
)

router = APIRouter(prefix="/dataset-groups", tags=["dataset-groups"])


@router.post("/", response_model=DatasetGroupResponse)
async def create_dataset_group(
    group: DatasetGroupCreate,
    db: Session = Depends(get_db)
):
    """Create a new dataset group"""
    db_group = DatasetGroup(
        name=group.name,
        description=group.description
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)

    return db_group


@router.get("/", response_model=List[DatasetGroupListResponse])
async def list_dataset_groups(db: Session = Depends(get_db)):
    """List all active dataset groups"""
    groups = db.query(DatasetGroup).filter(
        DatasetGroup.deleted_at.is_(None)
    ).order_by(DatasetGroup.created_at.desc()).all()

    # Format response with dataset count
    result = []
    for group in groups:
        result.append({
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "created_at": group.created_at,
            "dataset_count": len([m for m in group.memberships if m.dataset.deleted_at is None])
        })

    return result


@router.get("/{group_id}", response_model=DatasetGroupResponse)
async def get_dataset_group(group_id: str, db: Session = Depends(get_db)):
    """Get dataset group with all members"""
    group = db.query(DatasetGroup).filter(
        DatasetGroup.id == group_id,
        DatasetGroup.deleted_at.is_(None)
    ).first()

    if not group:
        raise HTTPException(404, "Dataset group not found")

    return group


@router.patch("/{group_id}", response_model=DatasetGroupResponse)
async def update_dataset_group(
    group_id: str,
    updates: DatasetGroupUpdate,
    db: Session = Depends(get_db)
):
    """Update dataset group metadata"""
    group = db.query(DatasetGroup).filter(
        DatasetGroup.id == group_id,
        DatasetGroup.deleted_at.is_(None)
    ).first()

    if not group:
        raise HTTPException(404, "Dataset group not found")

    if updates.name is not None:
        group.name = updates.name
    if updates.description is not None:
        group.description = updates.description

    db.commit()
    db.refresh(group)

    return group


@router.delete("/{group_id}")
async def delete_dataset_group(group_id: str, db: Session = Depends(get_db)):
    """Soft delete a dataset group"""
    group = db.query(DatasetGroup).filter(
        DatasetGroup.id == group_id,
        DatasetGroup.deleted_at.is_(None)
    ).first()

    if not group:
        raise HTTPException(404, "Dataset group not found")

    group.deleted_at = datetime.utcnow()
    db.commit()

    return {"message": "Dataset group deleted successfully"}


@router.post("/{group_id}/datasets", response_model=DatasetGroupMembershipResponse)
async def add_dataset_to_group(
    group_id: str,
    membership: DatasetGroupMembershipCreate,
    db: Session = Depends(get_db)
):
    """Add a dataset to a group"""
    # Verify group exists
    group = db.query(DatasetGroup).filter(
        DatasetGroup.id == group_id,
        DatasetGroup.deleted_at.is_(None)
    ).first()

    if not group:
        raise HTTPException(404, "Dataset group not found")

    # Verify dataset exists
    dataset = db.query(Dataset).filter(
        Dataset.id == membership.dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    # Check if already in group
    existing = db.query(DatasetGroupMembership).filter(
        DatasetGroupMembership.group_id == group_id,
        DatasetGroupMembership.dataset_id == membership.dataset_id
    ).first()

    if existing:
        raise HTTPException(400, "Dataset already in group")

    # Create membership
    db_membership = DatasetGroupMembership(
        group_id=group_id,
        dataset_id=membership.dataset_id,
        alias=membership.alias,
        display_order=membership.display_order
    )
    db.add(db_membership)
    db.commit()
    db.refresh(db_membership)

    return db_membership


@router.delete("/{group_id}/datasets/{dataset_id}")
async def remove_dataset_from_group(
    group_id: str,
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """Remove a dataset from a group"""
    membership = db.query(DatasetGroupMembership).filter(
        DatasetGroupMembership.group_id == group_id,
        DatasetGroupMembership.dataset_id == dataset_id
    ).first()

    if not membership:
        raise HTTPException(404, "Dataset not in group")

    db.delete(membership)
    db.commit()

    return {"message": "Dataset removed from group successfully"}


@router.patch("/{group_id}/datasets/{dataset_id}")
async def update_group_membership(
    group_id: str,
    dataset_id: str,
    alias: str = None,
    display_order: int = None,
    db: Session = Depends(get_db)
):
    """Update dataset membership settings (alias, order)"""
    membership = db.query(DatasetGroupMembership).filter(
        DatasetGroupMembership.group_id == group_id,
        DatasetGroupMembership.dataset_id == dataset_id
    ).first()

    if not membership:
        raise HTTPException(404, "Dataset not in group")

    if alias is not None:
        membership.alias = alias
    if display_order is not None:
        membership.display_order = display_order

    db.commit()
    db.refresh(membership)

    return membership


@router.get("/{group_id}/schemas")
async def get_group_schemas(group_id: str, db: Session = Depends(get_db)):
    """Get schemas for all datasets in a group"""
    from app.services.storage_service import StorageService

    group = db.query(DatasetGroup).filter(
        DatasetGroup.id == group_id,
        DatasetGroup.deleted_at.is_(None)
    ).first()

    if not group:
        raise HTTPException(404, "Dataset group not found")

    storage = StorageService()
    schemas = []

    for membership in sorted(group.memberships, key=lambda m: m.display_order):
        if membership.dataset.deleted_at is not None:
            continue

        try:
            schema = storage.load_schema(membership.dataset_id)
            schemas.append({
                "dataset_id": membership.dataset_id,
                "dataset_name": membership.dataset.name,
                "alias": membership.alias or membership.dataset.name,
                "row_count": membership.dataset.row_count,
                "schema": schema
            })
        except Exception as e:
            print(f"Error loading schema for dataset {membership.dataset_id}: {e}")
            continue

    return schemas


@router.get("/{group_id}/preview")
async def get_group_preview(group_id: str, db: Session = Depends(get_db)):
    """Get preview data for all datasets in a group"""
    from app.services.storage_service import StorageService
    import pandas as pd
    import numpy as np

    group = db.query(DatasetGroup).filter(
        DatasetGroup.id == group_id,
        DatasetGroup.deleted_at.is_(None)
    ).first()

    if not group:
        raise HTTPException(404, "Dataset group not found")

    storage = StorageService()
    previews = []

    for membership in sorted(group.memberships, key=lambda m: m.display_order):
        if membership.dataset.deleted_at is not None:
            continue

        try:
            # Load first 100 rows
            df = pd.read_parquet(membership.dataset.parquet_path, engine='pyarrow')
            preview_df = df.head(100)

            # Replace NaN, inf, -inf with None for JSON serialization
            preview_df = preview_df.replace([np.inf, -np.inf], None)
            preview_df = preview_df.where(pd.notna(preview_df), None)

            previews.append({
                "dataset_id": membership.dataset_id,
                "dataset_name": membership.dataset.name,
                "alias": membership.alias or membership.dataset.name,
                "row_count": membership.dataset.row_count,
                "preview_rows": len(preview_df),
                "columns": list(preview_df.columns),
                "data": preview_df.to_dict('records')
            })
        except Exception as e:
            print(f"Error loading preview for dataset {membership.dataset_id}: {e}")
            continue

    return previews
