from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import uuid
import time

from app.core.database import get_db
from app.models.dataset import Dataset
from app.models.query import Query, QueryStatus
from app.schemas.query import NLQueryRequest, SQLQueryRequest, QueryResponse
from app.services.nl_to_sql_service import NLToSQLService
from app.services.duckdb_service import DuckDBService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/queries", tags=["queries"])


@router.post("/nl", response_model=QueryResponse)
async def execute_nl_query(
    request: NLQueryRequest,
    db: Session = Depends(get_db)
):
    """Natural language to SQL query"""
    # Verify dataset exists
    dataset = db.query(Dataset).filter(
        Dataset.id == request.dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    # Generate SQL
    nl_service = NLToSQLService()
    try:
        result = await nl_service.generate_sql(request.query, request.dataset_id)
    except Exception as e:
        raise HTTPException(500, f"Failed to generate SQL: {str(e)}")

    # Execute SQL
    duckdb_service = DuckDBService()
    query_id = str(uuid.uuid4())

    try:
        start_time = time.time()
        df = duckdb_service.execute_query(result['sql'], request.dataset_id)
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Save query result
        storage = StorageService()
        result_path = storage.save_query_result(df, query_id)

        # Save query record
        query = Query(
            id=query_id,
            dataset_id=request.dataset_id,
            nl_input=request.query,
            generated_sql=result['sql'],
            execution_time_ms=execution_time_ms,
            result_rows=len(df),
            result_path=result_path,
            status=QueryStatus.SUCCESS,
            query_metadata=result
        )
        db.add(query)
        db.commit()

        return {
            "query_id": query_id,
            "sql": result['sql'],
            "rows": df.head(1000).to_dict('records'),  # Return first 1000
            "total_rows": len(df),
            "execution_time_ms": execution_time_ms,
            "retrieved_columns": result.get('retrieved_columns'),
            "status": "SUCCESS"
        }

    except Exception as e:
        # Save failed query
        error_sql = result.get('sql', '') if 'result' in locals() else ''
        query = Query(
            id=query_id,
            dataset_id=request.dataset_id,
            nl_input=request.query,
            generated_sql=error_sql,
            status=QueryStatus.FAILED,
            error_message=str(e)
        )
        db.add(query)
        db.commit()

        # Log the error for debugging
        print(f"Query failed for dataset {request.dataset_id}")
        print(f"NL Query: {request.query}")
        print(f"Generated SQL: {error_sql}")
        print(f"Error: {str(e)}")

        error_msg = f"Query execution failed: {str(e)}"
        if error_sql:
            error_msg += f"\n\nGenerated SQL:\n{error_sql}"
        raise HTTPException(400, error_msg)


@router.post("/sql", response_model=QueryResponse)
async def execute_sql_query(
    request: SQLQueryRequest,
    db: Session = Depends(get_db)
):
    """Direct SQL execution"""
    # Verify dataset exists
    dataset = db.query(Dataset).filter(
        Dataset.id == request.dataset_id,
        Dataset.deleted_at.is_(None)
    ).first()

    if not dataset:
        raise HTTPException(404, "Dataset not found")

    duckdb_service = DuckDBService()
    query_id = str(uuid.uuid4())

    try:
        start_time = time.time()
        df = duckdb_service.execute_query(request.sql, request.dataset_id)
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Save query result
        storage = StorageService()
        result_path = storage.save_query_result(df, query_id)

        # Save query
        query = Query(
            id=query_id,
            dataset_id=request.dataset_id,
            nl_input=None,
            generated_sql=request.sql,
            execution_time_ms=execution_time_ms,
            result_rows=len(df),
            result_path=result_path,
            status=QueryStatus.SUCCESS
        )
        db.add(query)
        db.commit()

        return {
            "query_id": query_id,
            "sql": request.sql,
            "rows": df.head(1000).to_dict('records'),
            "total_rows": len(df),
            "execution_time_ms": execution_time_ms,
            "status": "SUCCESS"
        }

    except Exception as e:
        # Save failed query
        query = Query(
            id=query_id,
            dataset_id=request.dataset_id,
            nl_input=None,
            generated_sql=request.sql,
            status=QueryStatus.FAILED,
            error_message=str(e)
        )
        db.add(query)
        db.commit()

        raise HTTPException(400, f"Query execution failed: {str(e)}")


@router.get("/{query_id}", response_model=QueryResponse)
async def get_query(query_id: str, db: Session = Depends(get_db)):
    """Get query result"""
    query = db.query(Query).filter(Query.id == query_id).first()

    if not query:
        raise HTTPException(404, "Query not found")

    if query.status != QueryStatus.SUCCESS:
        return {
            "query_id": query.id,
            "sql": query.generated_sql,
            "rows": [],
            "total_rows": 0,
            "status": query.status.value,
            "execution_time_ms": query.execution_time_ms
        }

    # Load result from Parquet
    storage = StorageService()
    try:
        df = storage.load_query_result(query_id)
        return {
            "query_id": query.id,
            "sql": query.generated_sql,
            "rows": df.to_dict('records'),
            "total_rows": len(df),
            "execution_time_ms": query.execution_time_ms,
            "status": query.status.value
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to load query result: {str(e)}")
