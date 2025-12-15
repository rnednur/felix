from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import random

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Dataset, User
from app.services.duckdb_service import DuckDBService

router = APIRouter()


def generate_suggestions_from_schema(dataset: Dataset, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate analysis suggestions based on dataset schema
    """
    suggestions = []
    columns = schema.get('columns', [])

    # Extract column types
    numeric_cols = [col['name'] for col in columns if col['dtype'] in ['int64', 'float64', 'int32', 'float32']]
    text_cols = [col['name'] for col in columns if col['dtype'] in ['object', 'string']]
    date_cols = [col['name'] for col in columns if 'date' in col['name'].lower() or 'time' in col['name'].lower()]

    # Suggestion 1: Numeric aggregations
    if numeric_cols:
        primary_numeric = numeric_cols[0]
        suggestions.append({
            'id': f'agg_{primary_numeric}',
            'title': f'Analyze {primary_numeric} Distribution',
            'description': f'See the distribution of {primary_numeric} across your dataset with min, max, and average values',
            'icon': 'trending',
            'query': f'Show me statistics for {primary_numeric} including min, max, average, and total',
            'category': 'overview'
        })

    # Suggestion 2: Categorical breakdown
    if text_cols and numeric_cols:
        category_col = text_cols[0]
        value_col = numeric_cols[0]
        suggestions.append({
            'id': f'breakdown_{category_col}',
            'title': f'{value_col} by {category_col}',
            'description': f'Break down {value_col} across different {category_col} to identify patterns',
            'icon': 'users',
            'query': f'Show me total {value_col} grouped by {category_col}',
            'category': 'insights'
        })

    # Suggestion 3: Time series if date column exists
    if date_cols and numeric_cols:
        date_col = date_cols[0]
        value_col = numeric_cols[0]
        suggestions.append({
            'id': f'trends_{date_col}',
            'title': f'{value_col} Trends Over Time',
            'description': f'Visualize how {value_col} changes over time using {date_col}',
            'icon': 'calendar',
            'query': f'Show me {value_col} trends over time using {date_col}',
            'category': 'trends'
        })

    # Suggestion 4: Top N analysis
    if text_cols and numeric_cols:
        category_col = text_cols[0]
        value_col = numeric_cols[0]
        suggestions.append({
            'id': f'top_{category_col}',
            'title': f'Top 10 {category_col}',
            'description': f'Identify the top performing {category_col} by {value_col}',
            'icon': 'dollar',
            'query': f'What are the top 10 {category_col} by {value_col}?',
            'category': 'insights'
        })

    # Suggestion 5: Multi-dimensional analysis
    if len(text_cols) >= 2 and numeric_cols:
        dim1 = text_cols[0]
        dim2 = text_cols[1]
        value_col = numeric_cols[0]
        suggestions.append({
            'id': f'matrix_{dim1}_{dim2}',
            'title': f'{value_col} by {dim1} and {dim2}',
            'description': f'Multi-dimensional view of {value_col} across {dim1} and {dim2}',
            'icon': 'trending',
            'query': f'Show me {value_col} broken down by {dim1} and {dim2}',
            'category': 'insights'
        })

    # Suggestion 6: Count/distribution
    if text_cols:
        category_col = text_cols[0]
        suggestions.append({
            'id': f'distribution_{category_col}',
            'title': f'{category_col} Distribution',
            'description': f'See the distribution and frequency of different {category_col} values',
            'icon': 'users',
            'query': f'Show me the count of records for each {category_col}',
            'category': 'overview'
        })

    # Return top 6 suggestions
    return suggestions[:6]


@router.post("/{dataset_id}/ai-suggestions")
async def get_ai_suggestions(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate AI-powered analysis suggestions based on dataset schema
    """
    # Get dataset
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Get schema
    try:
        duckdb_service = DuckDBService()
        schema = duckdb_service.get_schema(dataset_id)

        # Generate suggestions
        suggestions = generate_suggestions_from_schema(dataset, schema)

        return {
            'success': True,
            'suggestions': suggestions,
            'dataset_name': dataset.name
        }
    except Exception as e:
        print(f"Error generating suggestions: {e}")
        # Return empty suggestions on error
        return {
            'success': False,
            'suggestions': [],
            'error': str(e)
        }
