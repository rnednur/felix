import pandas as pd
import numpy as np
from typing import Dict, Any, List


class AnalysisService:
    """Generate dataset descriptions and insights"""

    def generate_dataset_description(self, df: pd.DataFrame, schema: dict) -> Dict[str, Any]:
        """Generate comprehensive dataset description"""

        description = {
            "overview": self._generate_overview(df, schema),
            "columns_analysis": self._analyze_columns(df, schema),
            "data_quality": self._assess_data_quality(df),
            "key_insights": self._generate_insights(df, schema),
            "suggestions": self._generate_suggestions(df, schema)
        }

        return description

    def _generate_overview(self, df: pd.DataFrame, schema: dict) -> Dict[str, Any]:
        """Generate high-level overview"""
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "numeric_columns": len(df.select_dtypes(include=[np.number]).columns),
            "categorical_columns": len(df.select_dtypes(include=['object', 'category']).columns),
            "datetime_columns": len(df.select_dtypes(include=['datetime64']).columns),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
        }

    def _analyze_columns(self, df: pd.DataFrame, schema: dict) -> List[Dict[str, Any]]:
        """Analyze each column"""
        columns_info = []

        for col in df.columns:
            col_data = df[col]
            col_info = {
                "name": col,
                "type": str(col_data.dtype),
                "missing_count": int(col_data.isnull().sum()),
                "missing_pct": round(col_data.isnull().mean() * 100, 2),
                "unique_count": int(col_data.nunique()),
                "cardinality": "high" if col_data.nunique() > len(df) * 0.9 else
                              ("medium" if col_data.nunique() > 10 else "low")
            }

            # Add type-specific info
            if pd.api.types.is_numeric_dtype(col_data):
                col_info["numeric_stats"] = {
                    "min": float(col_data.min()) if not col_data.empty else None,
                    "max": float(col_data.max()) if not col_data.empty else None,
                    "mean": float(col_data.mean()) if not col_data.empty else None,
                    "median": float(col_data.median()) if not col_data.empty else None,
                    "std": float(col_data.std()) if not col_data.empty else None
                }
            elif pd.api.types.is_string_dtype(col_data) or pd.api.types.is_object_dtype(col_data):
                top_values = col_data.value_counts().head(5)
                col_info["top_values"] = [
                    {"value": str(k), "count": int(v), "pct": round(v/len(df)*100, 2)}
                    for k, v in top_values.items()
                ]

            columns_info.append(col_info)

        return columns_info

    def _assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess overall data quality"""
        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()

        quality = {
            "completeness_pct": round((1 - missing_cells / total_cells) * 100, 2),
            "duplicate_rows": int(df.duplicated().sum()),
            "duplicate_rows_pct": round(df.duplicated().mean() * 100, 2),
            "columns_with_missing": df.columns[df.isnull().any()].tolist(),
            "high_cardinality_columns": [
                col for col in df.columns
                if df[col].nunique() > len(df) * 0.9
            ]
        }

        return quality

    def _generate_insights(self, df: pd.DataFrame, schema: dict) -> List[str]:
        """Generate key insights about the data"""
        insights = []

        # Dataset size insight
        if len(df) > 10000:
            insights.append(f"Large dataset with {len(df):,} rows - suitable for statistical analysis")
        elif len(df) < 100:
            insights.append(f"Small dataset with {len(df)} rows - limited for statistical inference")

        # Missing data insight
        missing_pct = (df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100
        if missing_pct > 20:
            insights.append(f"Significant missing data ({missing_pct:.1f}%) - consider data cleaning")
        elif missing_pct == 0:
            insights.append("Complete dataset with no missing values")

        # Numeric columns insight
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            insights.append(f"Contains {len(numeric_cols)} numeric columns suitable for aggregations and math operations")

        # Categorical columns insight
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            insights.append(f"Contains {len(categorical_cols)} categorical columns suitable for grouping and segmentation")

        # Datetime columns insight
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        if len(datetime_cols) > 0:
            insights.append(f"Contains {len(datetime_cols)} datetime columns suitable for time-series analysis")

        # Duplicate rows
        if df.duplicated().sum() > 0:
            insights.append(f"Found {df.duplicated().sum()} duplicate rows - consider deduplication")

        return insights

    def _generate_suggestions(self, df: pd.DataFrame, schema: dict) -> List[str]:
        """Generate actionable suggestions"""
        suggestions = []

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns

        # Analysis suggestions
        if len(numeric_cols) > 0 and len(categorical_cols) > 0:
            suggestions.append(f"Try: 'Summarize {numeric_cols[0]} by {categorical_cols[0]}'")

        if len(numeric_cols) > 0:
            suggestions.append(f"Try: 'What is the average {numeric_cols[0]}?'")
            if len(numeric_cols) > 1:
                suggestions.append(f"Try: 'Show correlation between {numeric_cols[0]} and {numeric_cols[1]}'")

        if len(categorical_cols) > 0:
            suggestions.append(f"Try: 'Show distribution of {categorical_cols[0]}'")

        # Data quality suggestions
        missing_cols = df.columns[df.isnull().any()].tolist()
        if missing_cols:
            suggestions.append(f"Consider handling missing values in: {', '.join(missing_cols[:3])}")

        return suggestions[:5]  # Limit to top 5

    def generate_natural_description(self, description: Dict[str, Any]) -> str:
        """Convert structured description to natural language"""
        overview = description['overview']
        quality = description['data_quality']
        insights = description['key_insights']

        text = f"""📊 **Dataset Overview**

This dataset contains **{overview['total_rows']:,} rows** and **{overview['total_columns']} columns**.

**Column Breakdown:**
• {overview['numeric_columns']} numeric columns (for calculations and aggregations)
• {overview['categorical_columns']} categorical columns (for grouping and filtering)
• {overview['datetime_columns']} datetime columns (for time-series analysis)

**Data Quality:**
• Completeness: **{quality['completeness_pct']}%**
• Duplicate rows: **{quality['duplicate_rows']}** ({quality['duplicate_rows_pct']}%)

**Key Insights:**
{chr(10).join(['• ' + insight for insight in insights[:5]])}

**Ready to explore?** Try asking questions about your data!"""

        return text
