"""
Data Scouting API Endpoints

Provides intelligent data profiling and scouting capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Dataset, User
from app.services.data_scouting_service import DataScoutingService

router = APIRouter()


class ScoutRequest(BaseModel):
    sample_size: int = 1000


class RegenerateObservationsRequest(BaseModel):
    use_llm: bool = True


@router.post("/{dataset_id}/scout")
async def scout_dataset(
    dataset_id: str,
    request: ScoutRequest = ScoutRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform data scouting on a dataset.

    Returns:
    - First Look Observations (data quality, patterns, discrepancies)
    - Scouting Questions (targeted follow-up questions)
    - Column profiles (detailed statistics)
    - Discrepancies (metadata vs actual data)
    """
    # Get dataset
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Perform scouting
    try:
        scouting_service = DataScoutingService()
        result = scouting_service.scout_dataset(dataset_id, request.sample_size)

        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Data scouting failed: {str(e)}"
        )


@router.post("/{dataset_id}/scout/regenerate-observations")
async def regenerate_observations(
    dataset_id: str,
    request: RegenerateObservationsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Regenerate observations using LLM for more natural, conversational output.
    """
    # Get dataset
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        scouting_service = DataScoutingService()

        # First get the profiling data
        scout_result = scouting_service.scout_dataset(dataset_id, 1000)

        if request.use_llm:
            # Load sample data
            sample_df = scouting_service._load_sample(dataset_id, 100)
            schema = scouting_service.storage_service.load_schema(dataset_id)

            # Generate LLM observations
            llm_observations = await scouting_service.generate_llm_observations(
                dataset_id,
                scout_result['column_profiles'],
                schema,
                sample_df
            )

            return {
                'success': True,
                'observations': llm_observations,
                'method': 'llm'
            }
        else:
            return {
                'success': True,
                'observations': scout_result['observations'],
                'method': 'rule-based'
            }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to regenerate observations: {str(e)}"
        )


@router.get("/{dataset_id}/scout/summary")
async def get_scout_summary(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a quick summary of data scouting results (cached if available).
    """
    # Get dataset
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    try:
        scouting_service = DataScoutingService()
        result = scouting_service.scout_dataset(dataset_id, 500)  # Smaller sample for quick summary

        # Return simplified summary
        return {
            'success': True,
            'dataset_id': dataset_id,
            'dataset_name': dataset.name,
            'total_rows': result['total_rows'],
            'observations_count': len(result['observations']),
            'questions_count': len(result['scouting_questions']),
            'discrepancies_count': len(result['discrepancies']),
            'high_priority_issues': [
                d for d in result['discrepancies']
                if d['severity'] == 'high'
            ]
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get scout summary: {str(e)}"
        )
