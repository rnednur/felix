from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.dataset import Dataset, SourceType, DatasetStatus
from app.models.user import User
from app.models.dataset_member import DatasetMember, DatasetRole
from app.schemas.dataset import DatasetResponse, DatasetPreviewResponse, SchemaResponse
from app.services.storage_service import StorageService
from app.services.analysis_service import AnalysisService
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload CSV/XLSX and create dataset"""
    # Create dataset ID
    dataset_id = str(uuid.uuid4())

    # Save to storage (Parquet + JSON + embeddings)
    storage = StorageService()
    analysis_service = AnalysisService()

    # Parse file
    try:
        if file.filename.endswith('.csv'):
            # Save CSV to temp file for DuckDB processing (memory efficient)
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp:
                content = await file.read()
                tmp.write(content)
                temp_csv_path = tmp.name

            try:
                # Use DuckDB to convert CSV -> Parquet without loading into pandas
                paths = storage.save_dataset_from_csv(temp_csv_path, dataset_id)
                source_type = SourceType.CSV

                # Get row count from schema
                schema = storage.load_schema(dataset_id)
                row_count = schema['total_rows']

                # For analysis, we still need a sample in pandas (just first 1000 rows)
                df_sample = pd.read_parquet(paths['parquet_path'], engine='pyarrow')
                if len(df_sample) > 1000:
                    df_sample = df_sample.head(1000)

                dataset_description = analysis_service.generate_dataset_description(df_sample, schema)
                natural_description = analysis_service.generate_natural_description(dataset_description)
            finally:
                # Clean up temp file
                os.unlink(temp_csv_path)

        elif file.filename.endswith('.xlsx'):
            # For XLSX, still use pandas (no memory-efficient alternative)
            df = pd.read_excel(file.file)
            source_type = SourceType.XLSX

            paths = storage.save_dataset(df, dataset_id)
            schema = storage.load_schema(dataset_id)
            row_count = len(df)

            dataset_description = analysis_service.generate_dataset_description(df, schema)
            natural_description = analysis_service.generate_natural_description(dataset_description)
        else:
            raise HTTPException(400, "Only CSV and XLSX files supported")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(400, f"Failed to parse file: {str(e)}")

    # Create DB record with metadata and set owner
    dataset = Dataset(
        id=dataset_id,
        name=file.filename,
        owner_id=current_user.id,  # Set owner
        parquet_path=paths['parquet_path'],
        schema_path=paths['schema_path'],
        embedding_path=paths['embedding_path'],
        source_type=source_type,
        status=DatasetStatus.READY,
        row_count=row_count,
        size_bytes=file.size or 0
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    # Create dataset member entry for owner
    owner_member = DatasetMember(
        dataset_id=dataset_id,
        user_id=current_user.id,
        role=DatasetRole.OWNER
    )
    db.add(owner_member)
    db.commit()

    # Add analysis as metadata to response
    response = {
        **dataset.__dict__,
        "analysis": dataset_description,
        "description_text": natural_description
    }

    return response


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dataset metadata"""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    # Check permissions
    if not PermissionService.can_access_dataset(db, current_user, dataset_id):
        raise HTTPException(403, "Access denied")

    return dataset


@router.get("/{dataset_id}/schema", response_model=SchemaResponse)
async def get_schema(dataset_id: str, db: Session = Depends(get_db)):
    """Get dataset schema with stats"""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    storage = StorageService()
    try:
        schema = storage.load_schema(dataset_id)
        return schema
    except Exception as e:
        raise HTTPException(500, f"Failed to load schema: {str(e)}")


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
async def preview_dataset(
    dataset_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get first N rows"""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    storage = StorageService()
    try:
        df = storage.load_dataset(dataset_id)
        preview = df.head(limit)

        return {
            "columns": preview.columns.tolist(),
            "rows": preview.to_dict('records'),
            "total_rows": len(df)
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to load preview: {str(e)}")


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Soft delete dataset"""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    dataset.deleted_at = datetime.utcnow()
    db.commit()

    return {"message": "Dataset deleted successfully"}


@router.get("/", response_model=list[DatasetResponse])
async def list_datasets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all datasets the current user has access to"""
    datasets = PermissionService.get_user_datasets(db, current_user)
    # Sort by created_at descending
    datasets.sort(key=lambda d: d.created_at, reverse=True)
    return datasets
