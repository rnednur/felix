import os
import json
import pandas as pd
import numpy as np
import duckdb
from pathlib import Path
from app.core.config import settings
from app.services.profiling_service import ProfilingService
from app.services.embedding_service import EmbeddingService


class StorageService:
    """Manages Parquet + JSON + embeddings on filesystem"""

    def __init__(self):
        self.profiling_service = ProfilingService()
        self.embedding_service = EmbeddingService()

        # Ensure directories exist
        Path(settings.DATASETS_DIR).mkdir(parents=True, exist_ok=True)
        Path(settings.QUERIES_DIR).mkdir(parents=True, exist_ok=True)
        Path(settings.EMBEDDINGS_DIR).mkdir(parents=True, exist_ok=True)

    def save_dataset(self, df: pd.DataFrame, dataset_id: str) -> dict:
        """Save dataset to Parquet, generate schema and embeddings"""
        base_path = f"{settings.DATASETS_DIR}/{dataset_id}"
        os.makedirs(base_path, exist_ok=True)

        # Save Parquet
        parquet_path = f"{base_path}/data.parquet"
        df.to_parquet(parquet_path, engine='pyarrow', index=False)

        # Generate schema
        schema = self.profiling_service.generate_schema(df)
        schema_path = f"{base_path}/schema.json"
        with open(schema_path, 'w') as f:
            json.dump(schema, f, indent=2)

        # Generate embeddings
        embeddings = self.embedding_service.generate_column_embeddings(schema['columns'])
        embedding_path = f"{settings.EMBEDDINGS_DIR}/{dataset_id}_embeddings.bin"
        self.embedding_service.save_embeddings(embeddings, embedding_path)

        return {
            'parquet_path': parquet_path,
            'schema_path': schema_path,
            'embedding_path': embedding_path
        }

    def save_dataset_from_csv(self, csv_path: str, dataset_id: str) -> dict:
        """Save CSV directly to Parquet using DuckDB (memory efficient)"""
        base_path = f"{settings.DATASETS_DIR}/{dataset_id}"
        os.makedirs(base_path, exist_ok=True)

        # Convert CSV to Parquet using DuckDB (no pandas needed)
        parquet_path = f"{base_path}/data.parquet"
        print(f"[DEBUG] Converting CSV {csv_path} to Parquet {parquet_path}")
        conn = duckdb.connect()
        try:
            conn.execute(f"""
                COPY (SELECT * FROM read_csv_auto('{csv_path}'))
                TO '{parquet_path}' (FORMAT PARQUET)
            """)
            print(f"[DEBUG] Successfully created Parquet file")
        except Exception as e:
            print(f"[DEBUG] DuckDB error: {e}")
            raise
        finally:
            conn.close()

        # Extract schema from Parquet using DuckDB
        schema = self._generate_schema_from_parquet(parquet_path)
        schema_path = f"{base_path}/schema.json"
        with open(schema_path, 'w') as f:
            json.dump(schema, f, indent=2)

        # Generate embeddings
        embeddings = self.embedding_service.generate_column_embeddings(schema['columns'])
        embedding_path = f"{settings.EMBEDDINGS_DIR}/{dataset_id}_embeddings.bin"
        self.embedding_service.save_embeddings(embeddings, embedding_path)

        return {
            'parquet_path': parquet_path,
            'schema_path': schema_path,
            'embedding_path': embedding_path
        }

    def _generate_schema_from_parquet(self, parquet_path: str) -> dict:
        """Generate schema JSON from Parquet file using DuckDB"""
        conn = duckdb.connect()

        try:
            # Get total row count
            total_rows = conn.execute(f"SELECT COUNT(*) FROM parquet_scan('{parquet_path}')").fetchone()[0]

            columns = []
            # Get column metadata
            col_info = conn.execute(f"DESCRIBE SELECT * FROM parquet_scan('{parquet_path}')").fetchall()

            for i, col in enumerate(col_info):
                col_name = col[0]
                col_type = col[1]

                # Get basic stats
                stats_query = f"""
                    SELECT
                        COUNT(DISTINCT "{col_name}") as distinct_count,
                        SUM(CASE WHEN "{col_name}" IS NULL THEN 1 ELSE 0 END) as null_count
                    FROM parquet_scan('{parquet_path}')
                """
                distinct_count, null_count = conn.execute(stats_query).fetchone()
                null_pct = (null_count / total_rows * 100) if total_rows > 0 else 0

                col_data = {
                    'name': col_name,
                    'dtype': col_type,
                    'nullable': null_count > 0,
                    'stats': {
                        'distinct_count': int(distinct_count),
                        'null_count': int(null_count),
                        'null_pct': float(null_pct)
                    },
                    'tags': self._infer_tags_from_type(col_type),
                    'embedding_index': i
                }

                # Add type-specific stats
                if any(t in col_type.lower() for t in ['int', 'double', 'float', 'decimal', 'numeric']):
                    # Numeric stats
                    numeric_stats = conn.execute(f"""
                        SELECT
                            MIN("{col_name}") as min_val,
                            MAX("{col_name}") as max_val,
                            AVG("{col_name}") as mean_val,
                            STDDEV("{col_name}") as std_val,
                            QUANTILE_CONT("{col_name}", 0.25) as q25,
                            QUANTILE_CONT("{col_name}", 0.5) as q50,
                            QUANTILE_CONT("{col_name}", 0.75) as q75
                        FROM parquet_scan('{parquet_path}')
                    """).fetchone()

                    col_data['stats'].update({
                        'min': float(numeric_stats[0]) if numeric_stats[0] is not None else None,
                        'max': float(numeric_stats[1]) if numeric_stats[1] is not None else None,
                        'mean': float(numeric_stats[2]) if numeric_stats[2] is not None else None,
                        'std': float(numeric_stats[3]) if numeric_stats[3] is not None else None,
                        'quantiles': {
                            '0.25': float(numeric_stats[4]) if numeric_stats[4] is not None else None,
                            '0.5': float(numeric_stats[5]) if numeric_stats[5] is not None else None,
                            '0.75': float(numeric_stats[6]) if numeric_stats[6] is not None else None
                        }
                    })
                elif 'varchar' in col_type.lower() or 'string' in col_type.lower():
                    # String stats
                    top_values = conn.execute(f"""
                        SELECT "{col_name}", COUNT(*) as cnt
                        FROM parquet_scan('{parquet_path}')
                        WHERE "{col_name}" IS NOT NULL
                        GROUP BY "{col_name}"
                        ORDER BY cnt DESC
                        LIMIT 10
                    """).fetchall()

                    avg_length = conn.execute(f"""
                        SELECT AVG(LENGTH("{col_name}"))
                        FROM parquet_scan('{parquet_path}')
                        WHERE "{col_name}" IS NOT NULL
                    """).fetchone()[0]

                    col_data['stats'].update({
                        'top_values': [[str(v[0]), int(v[1])] for v in top_values],
                        'avg_length': float(avg_length) if avg_length is not None else None
                    })
                elif 'date' in col_type.lower() or 'timestamp' in col_type.lower():
                    # Date stats
                    date_stats = conn.execute(f"""
                        SELECT MIN("{col_name}"), MAX("{col_name}")
                        FROM parquet_scan('{parquet_path}')
                    """).fetchone()

                    col_data['stats'].update({
                        'min': str(date_stats[0]) if date_stats[0] is not None else None,
                        'max': str(date_stats[1]) if date_stats[1] is not None else None
                    })

                columns.append(col_data)

            from datetime import datetime
            return {
                'version': 1,
                'columns': columns,
                'computed_at': datetime.utcnow().isoformat(),
                'total_rows': int(total_rows)
            }
        finally:
            conn.close()

    def _infer_tags_from_type(self, dtype: str) -> list:
        """Infer semantic tags from DuckDB type"""
        tags = []
        dtype_lower = dtype.lower()

        if any(t in dtype_lower for t in ['int', 'double', 'float', 'decimal', 'numeric']):
            tags.append('numeric')
        elif 'varchar' in dtype_lower or 'string' in dtype_lower:
            tags.append('text')
        elif 'date' in dtype_lower or 'timestamp' in dtype_lower:
            tags.append('temporal')

        return tags

    def load_schema(self, dataset_id: str) -> dict:
        """Load schema JSON for a dataset"""
        schema_path = f"{settings.DATASETS_DIR}/{dataset_id}/schema.json"
        with open(schema_path, 'r') as f:
            return json.load(f)

    def load_dataset(self, dataset_id: str) -> pd.DataFrame:
        """Load dataset from Parquet"""
        parquet_path = f"{settings.DATASETS_DIR}/{dataset_id}/data.parquet"
        return pd.read_parquet(parquet_path)

    def save_query_result(self, df: pd.DataFrame, query_id: str) -> str:
        """Save query result to Parquet"""
        result_path = f"{settings.QUERIES_DIR}/{query_id}_result.parquet"
        df.to_parquet(result_path, engine='pyarrow', index=False)
        return result_path

    def load_query_result(self, query_id: str) -> pd.DataFrame:
        """Load query result from Parquet"""
        result_path = f"{settings.QUERIES_DIR}/{query_id}_result.parquet"
        return pd.read_parquet(result_path)
