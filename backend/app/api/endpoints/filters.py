"""
Filters API Endpoints

Provides endpoints for getting filterable columns and distinct values.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, Dataset
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/filters", tags=["filters"])


@router.get("/datasets/{dataset_id}/columns")
async def get_filterable_columns(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get filterable columns for a dataset.

    Returns columns suitable for filtering with their types and cardinality.
    Categorical columns with low cardinality are ideal for dropdown filters.
    """
    # Validate dataset
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        storage = StorageService()
        schema = storage.load_schema(dataset_id)

        if not schema:
            raise HTTPException(status_code=404, detail="Dataset schema not found")

        filterable_columns = []

        for col in schema.get("columns", []):
            col_name = col.get("name")
            col_type = col.get("dtype", "").lower()

            # Determine if column is filterable
            is_filterable = False
            filter_type = "text"
            unique_count = col.get("unique_count", 0)

            # Categorical columns with reasonable cardinality
            if col_type in ["object", "string", "category", "bool", "boolean"]:
                if unique_count <= 100:  # Max 100 distinct values for dropdown
                    is_filterable = True
                    filter_type = "categorical"

            # Numeric columns can use range filters
            elif col_type in ["int64", "float64", "int32", "float32", "int", "float"]:
                is_filterable = True
                filter_type = "numeric"

            # Date columns can use date range filters
            elif "date" in col_type or "time" in col_type:
                is_filterable = True
                filter_type = "date"

            if is_filterable:
                filterable_columns.append({
                    "name": col_name,
                    "type": filter_type,
                    "dtype": col_type,
                    "unique_count": unique_count,
                    "null_count": col.get("null_count", 0)
                })

        return {
            "dataset_id": dataset_id,
            "columns": filterable_columns,
            "total_columns": len(schema.get("columns", [])),
            "filterable_count": len(filterable_columns)
        }

    except Exception as e:
        logger.error(f"Failed to get filterable columns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_id}/columns/{column_name}/values")
async def get_column_distinct_values(
    dataset_id: str,
    column_name: str,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get distinct values for a column.

    Returns unique values sorted by frequency (most common first).
    """
    import duckdb

    # Validate dataset
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        storage = StorageService()
        parquet_path = storage.get_parquet_path(dataset_id)

        # Query distinct values with counts
        conn = duckdb.connect(":memory:")
        query = f"""
            SELECT "{column_name}" as value, COUNT(*) as count
            FROM read_parquet('{parquet_path}')
            WHERE "{column_name}" IS NOT NULL
            GROUP BY "{column_name}"
            ORDER BY count DESC
            LIMIT {limit}
        """

        result = conn.execute(query).fetchall()
        conn.close()

        values = [
            {"value": row[0], "count": row[1]}
            for row in result
        ]

        # Also get total count and null count
        conn = duckdb.connect(":memory:")
        stats_query = f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN "{column_name}" IS NULL THEN 1 ELSE 0 END) as null_count
            FROM read_parquet('{parquet_path}')
        """
        stats = conn.execute(stats_query).fetchone()
        conn.close()

        return {
            "dataset_id": dataset_id,
            "column": column_name,
            "values": values,
            "total_rows": stats[0],
            "null_count": stats[1],
            "distinct_count": len(values)
        }

    except Exception as e:
        logger.error(f"Failed to get column values: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
