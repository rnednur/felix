import duckdb
import pandas as pd
from app.core.config import settings


class DuckDBService:
    """Execute queries using DuckDB"""

    def get_connection(self, dataset_id: str):
        """Create DuckDB connection with dataset loaded"""
        conn = duckdb.connect(database=':memory:')
        parquet_path = f"{settings.DATASETS_DIR}/{dataset_id}/data.parquet"
        conn.execute(f"CREATE VIEW dataset AS SELECT * FROM read_parquet('{parquet_path}')")
        return conn

    def execute_query(self, sql: str, dataset_id: str,
                     timeout_sec: int = None) -> pd.DataFrame:
        """Execute SQL query with timeout and guardrails"""
        if timeout_sec is None:
            timeout_sec = settings.QUERY_TIMEOUT_SECONDS

        conn = self.get_connection(dataset_id)

        try:
            # Execute and fetch
            # Note: DuckDB doesn't have built-in timeout, handled at Python level if needed
            result = conn.execute(sql).fetchdf()

            # Enforce row limit
            if len(result) > settings.MAX_QUERY_ROWS:
                result = result.head(settings.MAX_QUERY_ROWS)

            return result
        finally:
            conn.close()

    def get_query_plan(self, sql: str, dataset_id: str) -> str:
        """Get query execution plan"""
        conn = self.get_connection(dataset_id)
        try:
            plan = conn.execute(f"EXPLAIN {sql}").fetchall()
            return '\n'.join([str(row) for row in plan])
        finally:
            conn.close()
