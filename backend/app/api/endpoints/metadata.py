from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.models.dataset import Dataset
from app.models.column_metadata import ColumnMetadata, QueryRule
from app.services.ai_metadata_service import AIMetadataService

router = APIRouter(prefix="/metadata", tags=["metadata"])


# Request/Response Schemas
class ColumnMetadataUpdate(BaseModel):
    column_name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    business_definition: Optional[str] = None
    semantic_type: Optional[str] = None
    data_format: Optional[str] = None
    unit: Optional[str] = None
    is_pii: Optional[bool] = None
    is_required: Optional[bool] = None
    valid_values: Optional[List[Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    default_aggregation: Optional[str] = None
    is_dimension: Optional[bool] = None
    is_measure: Optional[bool] = None


class ColumnMetadataResponse(BaseModel):
    id: str
    dataset_id: str
    column_name: str
    display_name: Optional[str]
    description: Optional[str]
    business_definition: Optional[str]
    semantic_type: Optional[str]
    data_format: Optional[str]
    unit: Optional[str]
    is_pii: bool
    is_required: bool
    valid_values: Optional[List[Any]]
    validation_rules: Optional[Dict[str, Any]]
    default_aggregation: Optional[str]
    is_dimension: bool
    is_measure: bool
    created_at: datetime
    updated_at: datetime


class QueryRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    rule_type: str  # "filter", "exclude_column", "always_include"
    condition: Dict[str, Any]
    is_active: bool = True
    priority: int = 0


class QueryRuleResponse(BaseModel):
    id: str
    dataset_id: str
    name: str
    description: Optional[str]
    rule_type: str
    condition: Dict[str, Any]
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime


# Column Metadata Endpoints

@router.get("/datasets/{dataset_id}/columns", response_model=List[ColumnMetadataResponse])
async def get_column_metadata(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """Get metadata for all columns in a dataset"""
    # Verify dataset exists
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    metadata = db.query(ColumnMetadata).filter(
        ColumnMetadata.dataset_id == dataset_id
    ).all()

    return metadata


@router.put("/datasets/{dataset_id}/columns/{column_name}")
async def update_column_metadata(
    dataset_id: str,
    column_name: str,
    update: ColumnMetadataUpdate,
    db: Session = Depends(get_db)
):
    """Update or create metadata for a column"""
    # Verify dataset exists
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    # Get or create metadata
    metadata = db.query(ColumnMetadata).filter(
        ColumnMetadata.dataset_id == dataset_id,
        ColumnMetadata.column_name == column_name
    ).first()

    if not metadata:
        metadata = ColumnMetadata(
            dataset_id=dataset_id,
            column_name=column_name
        )
        db.add(metadata)

    # Update fields
    for field, value in update.dict(exclude_unset=True).items():
        if field != 'column_name':  # Don't update the key
            setattr(metadata, field, value)

    metadata.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(metadata)

    return metadata


@router.delete("/datasets/{dataset_id}/columns/{column_name}")
async def delete_column_metadata(
    dataset_id: str,
    column_name: str,
    db: Session = Depends(get_db)
):
    """Delete metadata for a column"""
    metadata = db.query(ColumnMetadata).filter(
        ColumnMetadata.dataset_id == dataset_id,
        ColumnMetadata.column_name == column_name
    ).first()

    if not metadata:
        raise HTTPException(404, "Column metadata not found")

    db.delete(metadata)
    db.commit()

    return {"status": "deleted"}


# Query Rules Endpoints

@router.get("/datasets/{dataset_id}/rules", response_model=List[QueryRuleResponse])
async def get_query_rules(
    dataset_id: str,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get all query rules for a dataset"""
    # Verify dataset exists
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    query = db.query(QueryRule).filter(QueryRule.dataset_id == dataset_id)

    if active_only:
        query = query.filter(QueryRule.is_active == True)

    rules = query.order_by(QueryRule.priority.desc()).all()

    return rules


@router.post("/datasets/{dataset_id}/rules", response_model=QueryRuleResponse)
async def create_query_rule(
    dataset_id: str,
    rule: QueryRuleCreate,
    db: Session = Depends(get_db)
):
    """Create a new query rule"""
    # Verify dataset exists
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    # Create rule
    new_rule = QueryRule(
        dataset_id=dataset_id,
        **rule.dict()
    )

    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)

    return new_rule


@router.put("/datasets/{dataset_id}/rules/{rule_id}", response_model=QueryRuleResponse)
async def update_query_rule(
    dataset_id: str,
    rule_id: str,
    rule: QueryRuleCreate,
    db: Session = Depends(get_db)
):
    """Update a query rule"""
    existing_rule = db.query(QueryRule).filter(
        QueryRule.id == rule_id,
        QueryRule.dataset_id == dataset_id
    ).first()

    if not existing_rule:
        raise HTTPException(404, "Rule not found")

    # Update fields
    for field, value in rule.dict().items():
        setattr(existing_rule, field, value)

    existing_rule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(existing_rule)

    return existing_rule


@router.delete("/datasets/{dataset_id}/rules/{rule_id}")
async def delete_query_rule(
    dataset_id: str,
    rule_id: str,
    db: Session = Depends(get_db)
):
    """Delete a query rule"""
    rule = db.query(QueryRule).filter(
        QueryRule.id == rule_id,
        QueryRule.dataset_id == dataset_id
    ).first()

    if not rule:
        raise HTTPException(404, "Rule not found")

    db.delete(rule)
    db.commit()

    return {"status": "deleted"}


@router.post("/datasets/{dataset_id}/rules/{rule_id}/toggle")
async def toggle_query_rule(
    dataset_id: str,
    rule_id: str,
    db: Session = Depends(get_db)
):
    """Toggle a rule's active status"""
    rule = db.query(QueryRule).filter(
        QueryRule.id == rule_id,
        QueryRule.dataset_id == dataset_id
    ).first()

    if not rule:
        raise HTTPException(404, "Rule not found")

    rule.is_active = not rule.is_active
    rule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rule)

    return rule


# AI-Powered Metadata and Rules Endpoints

class AIMetadataRequest(BaseModel):
    instruction: str


class AIMetadataResponse(BaseModel):
    success: bool
    message: str
    updates: Optional[Dict[str, Any]] = None
    rules: Optional[List[Dict[str, Any]]] = None
    updated_columns: Optional[List[str]] = None
    created_rules: Optional[List[str]] = None


@router.post("/datasets/{dataset_id}/ai-update", response_model=AIMetadataResponse)
async def ai_update_metadata(
    dataset_id: str,
    request: AIMetadataRequest,
    db: Session = Depends(get_db)
):
    """
    Use AI to update column metadata based on natural language instruction

    Examples:
    - "Mark email and phone columns as PII"
    - "Set revenue and sales to use SUM aggregation"
    - "Add business definitions for customer columns"
    """
    # Verify dataset exists
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    try:
        service = AIMetadataService(db)

        # Generate metadata updates
        updates = await service.generate_metadata_updates(dataset_id, request.instruction)

        # Apply updates
        updated_columns = await service.apply_metadata_updates(dataset_id, updates)

        return {
            "success": True,
            "message": f"Updated metadata for {len(updated_columns)} columns",
            "updates": updates,
            "updated_columns": updated_columns
        }
    except Exception as e:
        print(f"AI metadata update error: {str(e)}")
        raise HTTPException(500, f"Failed to update metadata: {str(e)}")


@router.post("/datasets/{dataset_id}/ai-rules", response_model=AIMetadataResponse)
async def ai_create_rules(
    dataset_id: str,
    request: AIMetadataRequest,
    db: Session = Depends(get_db)
):
    """
    Use AI to create query rules based on natural language instruction

    Examples:
    - "Only show active customers"
    - "Filter out cancelled orders"
    - "Always exclude SSN column"
    - "Only show data from 2024"
    """
    # Verify dataset exists
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    try:
        service = AIMetadataService(db)

        # Generate rules
        rules = await service.generate_query_rules(dataset_id, request.instruction)

        # Apply rules
        created_rules = await service.apply_query_rules(dataset_id, rules)

        return {
            "success": True,
            "message": f"Created {len(created_rules)} query rules",
            "rules": rules,
            "created_rules": created_rules
        }
    except Exception as e:
        print(f"AI rules creation error: {str(e)}")
        raise HTTPException(500, f"Failed to create rules: {str(e)}")
