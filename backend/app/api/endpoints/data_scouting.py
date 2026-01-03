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


class InteractiveScoutRequest(BaseModel):
    """
    Interactive scouting request with user-provided rules and context
    """
    sample_size: int = 1000
    custom_rules: list[str] = []  # User-provided validation rules
    business_context: str = ""     # User-provided business context
    specific_questions: list[str] = []  # Specific questions user wants answered


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


@router.post("/{dataset_id}/scout/interactive")
async def interactive_scout(
    dataset_id: str,
    request: InteractiveScoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Interactive data scouting with user-provided rules and context.

    This endpoint allows users to:
    - Provide custom validation rules
    - Add business context for better analysis
    - Ask specific questions about the data

    Returns enhanced scouting results incorporating user input.
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

        # Perform base scouting
        base_result = scouting_service.scout_dataset(dataset_id, request.sample_size)

        # Load sample data for LLM analysis
        sample_df = scouting_service._load_sample(dataset_id, min(request.sample_size, 100))
        schema = scouting_service.storage_service.load_schema(dataset_id)

        # Build enhanced prompt with user context
        enhanced_observations = await _generate_interactive_observations(
            scouting_service,
            dataset_id,
            base_result,
            sample_df,
            schema,
            request
        )

        return {
            'success': True,
            'dataset_id': dataset_id,
            'sample_size': len(sample_df),
            'total_rows': schema.get('total_rows', 0),
            'observations': enhanced_observations['observations'],
            'answers': enhanced_observations.get('answers', []),
            'additional_questions': enhanced_observations.get('additional_questions', []),
            'rule_validations': enhanced_observations.get('rule_validations', []),
            'column_profiles': base_result['column_profiles'],
            'discrepancies': base_result['discrepancies'],
            'timestamp': base_result['timestamp']
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Interactive scouting failed: {str(e)}"
        )


async def _generate_interactive_observations(
    scouting_service: DataScoutingService,
    dataset_id: str,
    base_result: Dict[str, Any],
    sample_df: Any,
    schema: Dict[str, Any],
    request: InteractiveScoutRequest
) -> Dict[str, Any]:
    """
    Generate enhanced observations using LLM with user-provided context
    """
    import openai

    # Prepare context
    profiles = base_result['column_profiles'][:10]
    discrepancies = base_result['discrepancies']

    # Build prompt with user context
    prompt_parts = [
        f"You are analyzing a dataset called '{schema.get('dataset_name', 'dataset')}' with {schema.get('total_rows', 0):,} rows.",
        "",
        "=== Sample Data (first 5 rows) ===",
        str(sample_df.head(5).to_dict('records')),
        "",
        "=== Column Profiles ===",
        str(profiles),
        "",
        "=== Detected Discrepancies ===",
        str(discrepancies)
    ]

    # Add user context if provided
    if request.business_context:
        prompt_parts.extend([
            "",
            "=== Business Context (provided by user) ===",
            request.business_context
        ])

    # Add custom rules if provided
    if request.custom_rules:
        prompt_parts.extend([
            "",
            "=== Validation Rules to Check ===",
            "\n".join([f"- {rule}" for rule in request.custom_rules])
        ])

    # Add specific questions if provided
    if request.specific_questions:
        prompt_parts.extend([
            "",
            "=== Specific Questions to Answer ===",
            "\n".join([f"{i+1}. {q}" for i, q in enumerate(request.specific_questions)])
        ])

    prompt_parts.extend([
        "",
        "=== Your Task ===",
        "Provide a comprehensive data scouting report in JSON format:",
        "{",
        '  "observations": ["List 6-8 key observations about data quality, patterns, and issues"],',
        '  "answers": ["If specific questions were asked, provide clear answers to each"],',
        '  "rule_validations": ["If validation rules were provided, report which pass/fail with examples"],',
        '  "additional_questions": ["Suggest 3-5 follow-up questions the user should consider"]',
        "}",
        "",
        "Be specific, actionable, and reference actual data values when possible."
    ])

    full_prompt = "\n".join(prompt_parts)

    try:
        response = openai.ChatCompletion.create(
            model=scouting_service.llm_model,
            messages=[
                {"role": "system", "content": "You are a data profiling expert who provides clear, actionable insights in JSON format."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=1500,
            temperature=scouting_service.llm_temperature
        )

        content = response['choices'][0]['message']['content'].strip()

        # Extract JSON if wrapped in markdown
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
            content = content.strip()

        import json
        result = json.loads(content)
        return result

    except Exception as e:
        print(f"LLM interactive observation generation failed: {e}")
        # Fallback to base observations
        return {
            'observations': base_result['observations'],
            'answers': [],
            'rule_validations': [],
            'additional_questions': base_result['scouting_questions']
        }
