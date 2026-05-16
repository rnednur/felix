"""
Data Profiling Tool - comprehensive EDA and data quality analysis
"""
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from scipy import stats
from app.tools.base_tool import BaseTool
from app.schemas.tool import (
    ToolSchema, ToolParameter, ToolParameterType, ToolResult, ToolCapability
)
from app.services.duckdb_service import DuckDBService


class DataProfilingTool(BaseTool):
    """Comprehensive data profiling and EDA tool"""

    def __init__(self):
        super().__init__()
        self.duckdb_service = DuckDBService()

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name="data_profiling",
            description="Perform comprehensive data profiling and exploratory data analysis",
            category="analysis",
            parameters=[
                ToolParameter(name="dataset_id", type=ToolParameterType.STRING,
                            description="Dataset ID", required=True),
                ToolParameter(name="include_correlations", type=ToolParameterType.BOOLEAN,
                            description="Include correlation analysis", required=False, default=True),
                ToolParameter(name="include_outliers", type=ToolParameterType.BOOLEAN,
                            description="Include outlier detection", required=False, default=True)
            ],
            returns={"type": "object"},
            requires_approval=False,
            is_destructive=False,
            estimated_duration_ms=3000
        )

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="Data Profiling",
            description="Comprehensive data quality and exploratory analysis",
            use_cases=[
                "Understand data quality and completeness",
                "Identify outliers and anomalies",
                "Analyze distributions and correlations",
                "Generate data quality reports"
            ],
            limitations=["Limited to 10000 rows for performance"]
        )

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute data profiling"""
        try:
            # Fetch data
            query = "SELECT * FROM dataset LIMIT 10000"
            data_df = self.duckdb_service.execute_query(query, dataset_id=parameters["dataset_id"])

            # Basic info
            profile = {
                "overview": self._get_overview(data_df),
                "columns": self._profile_columns(data_df),
                "data_quality": self._assess_quality(data_df),
                "insights": []
            }

            # Optional analyses
            if parameters.get("include_correlations", True):
                profile["correlations"] = self._analyze_correlations(data_df)

            if parameters.get("include_outliers", True):
                profile["outliers"] = self._detect_outliers(data_df)

            # Generate insights
            profile["insights"] = self._generate_insights(profile, data_df)

            return ToolResult(
                tool_name="data_profiling",
                success=True,
                data=profile,
                metadata={"num_insights": len(profile["insights"])}
            )

        except Exception as e:
            return ToolResult(
                tool_name="data_profiling",
                success=False,
                data={},
                error=f"Profiling failed: {str(e)}"
            )

    def _get_overview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get dataset overview"""
        return {
            "num_rows": len(df),
            "num_columns": len(df.columns),
            "memory_bytes": int(df.memory_usage(deep=True).sum()),
            "duplicates": int(df.duplicated().sum()),
            "duplicate_rate": float(df.duplicated().sum() / len(df))
        }

    def _profile_columns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Profile each column"""
        columns_profile = []

        for col in df.columns:
            col_type = str(df[col].dtype)
            missing = int(df[col].isna().sum())
            missing_rate = float(missing / len(df))

            col_prof = {
                "name": col,
                "type": col_type,
                "missing": missing,
                "missing_rate": missing_rate,
                "unique": int(df[col].nunique()),
                "cardinality": float(df[col].nunique() / len(df))
            }

            # Numeric columns
            if df[col].dtype in [np.float64, np.int64, np.float32, np.int32]:
                col_prof.update({
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "skewness": float(df[col].skew()),
                    "kurtosis": float(df[col].kurtosis())
                })

            # Categorical columns
            elif df[col].dtype == 'object':
                top_values = df[col].value_counts().head(5).to_dict()
                col_prof["top_values"] = {str(k): int(v) for k, v in top_values.items()}

            columns_profile.append(col_prof)

        return columns_profile

    def _assess_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data quality"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        quality = {
            "overall_missing_rate": float(df.isna().sum().sum() / (len(df) * len(df.columns))),
            "complete_rows": int((~df.isna().any(axis=1)).sum()),
            "complete_rate": float((~df.isna().any(axis=1)).sum() / len(df))
        }

        # Check for constant columns
        constant_cols = [col for col in df.columns if df[col].nunique() == 1]
        quality["constant_columns"] = constant_cols

        # Check for high cardinality
        high_card_cols = [col for col in df.columns
                         if df[col].dtype == 'object' and df[col].nunique() / len(df) > 0.95]
        quality["high_cardinality_columns"] = high_card_cols

        return quality

    def _analyze_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze correlations"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if len(numeric_cols) < 2:
            return {"message": "Not enough numeric columns"}

        corr_matrix = df[numeric_cols].corr()

        # Find strong correlations
        strong_corrs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.7:
                    strong_corrs.append({
                        "col1": corr_matrix.columns[i],
                        "col2": corr_matrix.columns[j],
                        "correlation": float(corr_val)
                    })

        return {
            "strong_correlations": strong_corrs,
            "num_strong": len(strong_corrs)
        }

    def _detect_outliers(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect outliers using IQR method"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        outliers_summary = {}

        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR

            outlier_count = int(((df[col] < lower) | (df[col] > upper)).sum())

            if outlier_count > 0:
                outliers_summary[col] = {
                    "count": outlier_count,
                    "rate": float(outlier_count / len(df)),
                    "lower_bound": float(lower),
                    "upper_bound": float(upper)
                }

        return outliers_summary

    def _generate_insights(self, profile: Dict[str, Any], df: pd.DataFrame) -> List[str]:
        """Generate actionable insights"""
        insights = []

        # Data quality insights
        if profile["overview"]["duplicate_rate"] > 0.05:
            insights.append(f"{profile['overview']['duplicate_rate']*100:.1f}% duplicate rows detected")

        if profile["data_quality"]["overall_missing_rate"] > 0.1:
            insights.append(f"{profile['data_quality']['overall_missing_rate']*100:.1f}% of data is missing")

        # Column insights
        for col_prof in profile["columns"]:
            if col_prof["missing_rate"] > 0.5:
                insights.append(f"{col_prof['name']} has {col_prof['missing_rate']*100:.1f}% missing values")

            if "skewness" in col_prof and abs(col_prof["skewness"]) > 2:
                insights.append(f"{col_prof['name']} is highly skewed (skewness: {col_prof['skewness']:.2f})")

        # Correlation insights
        if "correlations" in profile and profile["correlations"].get("strong_correlations"):
            insights.append(f"Found {len(profile['correlations']['strong_correlations'])} strong correlations")

        # Outlier insights
        if "outliers" in profile and profile["outliers"]:
            total_outliers = sum(v["count"] for v in profile["outliers"].values())
            insights.append(f"Detected {total_outliers} outliers across {len(profile['outliers'])} columns")

        return insights
