from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.dataset import Dataset
from app.services.storage_service import StorageService
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/datasets/{dataset_id}/describe")
async def describe_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Get detailed description and analysis of dataset"""
    # Verify dataset exists
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    # Load data and schema
    storage = StorageService()
    analysis_service = AnalysisService()

    try:
        df = storage.load_dataset(dataset_id)
        schema = storage.load_schema(dataset_id)

        # Generate analysis
        description = analysis_service.generate_dataset_description(df, schema)
        natural_text = analysis_service.generate_natural_description(description)

        return {
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "analysis": description,
            "description_text": natural_text
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to analyze dataset: {str(e)}")


@router.get("/datasets/{dataset_id}/summary")
async def get_dataset_summary(dataset_id: str, db: Session = Depends(get_db)):
    """Get quick summary statistics"""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    storage = StorageService()
    analysis_service = AnalysisService()

    try:
        df = storage.load_dataset(dataset_id)
        schema = storage.load_schema(dataset_id)

        description = analysis_service.generate_dataset_description(df, schema)

        return {
            "overview": description["overview"],
            "data_quality": description["data_quality"],
            "key_insights": description["key_insights"][:3],
            "suggestions": description["suggestions"][:3]
        }

    except Exception as e:
        raise HTTPException(500, f"Failed to get summary: {str(e)}")
