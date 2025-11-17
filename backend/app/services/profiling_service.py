import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List


class ProfilingService:
    """Compute statistics and generate schema"""

    def generate_schema(self, df: pd.DataFrame) -> dict:
        """Generate schema with column statistics"""
        columns = []
        for col in df.columns:
            col_stats = self.compute_column_stats(df[col])
            columns.append({
                'name': col,
                'dtype': str(df[col].dtype),
                'nullable': bool(df[col].isnull().any()),
                'stats': col_stats,
                'tags': self.infer_tags(df[col]),
                'embedding_index': len(columns)
            })

        return {
            'version': 1,
            'columns': columns,
            'computed_at': datetime.utcnow().isoformat(),
            'total_rows': len(df)
        }

    def compute_column_stats(self, series: pd.Series) -> Dict[str, Any]:
        """Compute statistics for a single column"""
        stats = {
            'distinct_count': int(series.nunique()),
            'null_count': int(series.isnull().sum()),
            'null_pct': float(series.isnull().mean() * 100)
        }

        if pd.api.types.is_numeric_dtype(series):
            # Numeric statistics
            stats.update({
                'min': float(series.min()) if not series.empty else None,
                'max': float(series.max()) if not series.empty else None,
                'mean': float(series.mean()) if not series.empty else None,
                'std': float(series.std()) if not series.empty else None,
                'quantiles': {
                    '0.25': float(series.quantile(0.25)) if not series.empty else None,
                    '0.5': float(series.quantile(0.5)) if not series.empty else None,
                    '0.75': float(series.quantile(0.75)) if not series.empty else None
                }
            })
        elif pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
            # String statistics
            value_counts = series.value_counts().head(10)
            stats.update({
                'top_values': [[str(k), int(v)] for k, v in value_counts.items()],
                'avg_length': float(series.astype(str).str.len().mean()) if not series.empty else None
            })
        elif pd.api.types.is_datetime64_any_dtype(series):
            # Date statistics
            stats.update({
                'min': series.min().isoformat() if not series.empty else None,
                'max': series.max().isoformat() if not series.empty else None
            })

        return stats

    def infer_tags(self, series: pd.Series) -> List[str]:
        """Infer semantic tags for a column"""
        tags = []

        if pd.api.types.is_numeric_dtype(series):
            tags.append('numeric')
            if series.nunique() == len(series):
                tags.append('unique')
        elif pd.api.types.is_string_dtype(series) or pd.api.types.is_object_dtype(series):
            tags.append('text')
            if series.nunique() == len(series):
                tags.append('unique')
        elif pd.api.types.is_datetime64_any_dtype(series):
            tags.append('temporal')

        return tags
