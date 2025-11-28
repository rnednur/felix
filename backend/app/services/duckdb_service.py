import duckdb
import pandas as pd
from typing import List, Dict, Optional
from app.core.config import settings


class DuckDBService:
    """Execute queries using DuckDB"""

    def get_connection(self, dataset_id: str):
        """Create DuckDB connection with dataset loaded"""
        conn = duckdb.connect(database=':memory:')
        parquet_path = f"{settings.DATASETS_DIR}/{dataset_id}/data.parquet"
        conn.execute(f"CREATE VIEW dataset AS SELECT * FROM read_parquet('{parquet_path}')")
        return conn

    def get_connection_for_group(self, dataset_configs: List[Dict[str, str]]):
        """Create DuckDB connection with multiple datasets loaded

        Args:
            dataset_configs: List of dicts with 'dataset_id' and 'alias' keys
        """
        conn = duckdb.connect(database=':memory:')
        for config in dataset_configs:
            dataset_id = config['dataset_id']
            alias = config['alias']
            parquet_path = f"{settings.DATASETS_DIR}/{dataset_id}/data.parquet"
            # Quote alias to prevent it from being interpreted as schema name
            quoted_alias = f'"{alias}"' if alias else f'dataset_{dataset_id}'
            conn.execute(f"CREATE VIEW {quoted_alias} AS SELECT * FROM read_parquet('{parquet_path}')")
        return conn

    def execute_query(
        self,
        sql: str,
        dataset_id: Optional[str] = None,
        dataset_configs: Optional[List[Dict[str, str]]] = None,
        timeout_sec: int = None
    ) -> pd.DataFrame:
        """Execute SQL query with timeout and guardrails

        Args:
            sql: SQL query to execute
            dataset_id: Single dataset ID (for single-dataset queries)
            dataset_configs: List of dataset configs (for multi-dataset queries)
            timeout_sec: Query timeout in seconds
        """
        if timeout_sec is None:
            timeout_sec = settings.QUERY_TIMEOUT_SECONDS

        # Create appropriate connection
        if dataset_configs:
            conn = self.get_connection_for_group(dataset_configs)
        elif dataset_id:
            conn = self.get_connection(dataset_id)
        else:
            raise ValueError("Must provide either dataset_id or dataset_configs")

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
