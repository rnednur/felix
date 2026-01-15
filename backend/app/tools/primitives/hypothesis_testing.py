"""
Hypothesis Testing Tool - statistical hypothesis tests
"""
from typing import Dict, Any
import pandas as pd
import numpy as np
from scipy import stats
from app.tools.base_tool import BaseTool
from app.schemas.tool import (
    ToolSchema, ToolParameter, ToolParameterType, ToolResult, ToolCapability
)
from app.services.duckdb_service import DuckDBService


class HypothesisTestingTool(BaseTool):
    """Statistical hypothesis testing tool"""

    def __init__(self):
        super().__init__()
        self.duckdb_service = DuckDBService()

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name="hypothesis_testing",
            description="Perform statistical hypothesis tests",
            category="analysis",
            parameters=[
                ToolParameter(name="dataset_id", type=ToolParameterType.STRING,
                            description="Dataset ID", required=True),
                ToolParameter(name="test_type", type=ToolParameterType.STRING,
                            description="Type of test", required=True,
                            enum=["t_test", "anova", "chi_square", "mann_whitney",
                                 "kruskal_wallis", "normality", "correlation"]),
                ToolParameter(name="column", type=ToolParameterType.STRING,
                            description="Primary column", required=False),
                ToolParameter(name="column2", type=ToolParameterType.STRING,
                            description="Second column (for two-sample tests)", required=False),
                ToolParameter(name="group_column", type=ToolParameterType.STRING,
                            description="Grouping column", required=False),
                ToolParameter(name="alpha", type=ToolParameterType.NUMBER,
                            description="Significance level", required=False, default=0.05)
            ],
            returns={"type": "object"},
            requires_approval=False,
            is_destructive=False,
            estimated_duration_ms=1000
        )

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="Hypothesis Testing",
            description="Perform statistical hypothesis tests with interpretation",
            use_cases=[
                "Compare means between groups",
                "Test for normality",
                "Analyze categorical associations",
                "Non-parametric testing"
            ],
            limitations=["Requires appropriate data structure for each test"]
        )

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute hypothesis test"""
        try:
            test_type = parameters["test_type"]
            alpha = parameters.get("alpha", 0.05)

            # Fetch data
            data_df = await self._fetch_data(parameters)

            # Run appropriate test
            if test_type == "t_test":
                result = self._t_test(data_df, parameters, alpha)
            elif test_type == "anova":
                result = self._anova(data_df, parameters, alpha)
            elif test_type == "chi_square":
                result = self._chi_square(data_df, parameters, alpha)
            elif test_type == "mann_whitney":
                result = self._mann_whitney(data_df, parameters, alpha)
            elif test_type == "kruskal_wallis":
                result = self._kruskal_wallis(data_df, parameters, alpha)
            elif test_type == "normality":
                result = self._normality_test(data_df, parameters, alpha)
            elif test_type == "correlation":
                result = self._correlation_test(data_df, parameters, alpha)
            else:
                raise ValueError(f"Unknown test type: {test_type}")

            return ToolResult(
                tool_name="hypothesis_testing",
                success=True,
                data=result,
                metadata={"test_type": test_type}
            )

        except Exception as e:
            return ToolResult(
                tool_name="hypothesis_testing",
                success=False,
                data={},
                error=f"Hypothesis test failed: {str(e)}"
            )

    async def _fetch_data(self, parameters: Dict[str, Any]) -> pd.DataFrame:
        """Fetch relevant data"""
        cols = [c for c in [parameters.get("column"), parameters.get("column2"),
                           parameters.get("group_column")] if c]
        cols_str = ", ".join(set(cols)) if cols else "*"
        query = f"SELECT {cols_str} FROM dataset LIMIT 5000"
        return self.duckdb_service.execute_query(query, dataset_id=parameters["dataset_id"])

    def _t_test(self, df: pd.DataFrame, params: Dict[str, Any], alpha: float) -> Dict[str, Any]:
        """Independent t-test"""
        col = params.get("column")
        group_col = params.get("group_column")

        groups = df.groupby(group_col)[col].apply(list)
        if len(groups) != 2:
            raise ValueError("T-test requires exactly 2 groups")

        g1, g2 = list(groups.values())
        t_stat, p_value = stats.ttest_ind(g1, g2)

        return {
            "test": "Independent T-Test",
            "statistic": float(t_stat),
            "p_value": float(p_value),
            "significant": p_value < alpha,
            "interpretation": f"{'Significant' if p_value < alpha else 'No significant'} difference between groups (p={p_value:.4f})",
            "group_means": {str(k): float(np.mean(v)) for k, v in groups.items()},
            "effect_size_cohens_d": float((np.mean(g1) - np.mean(g2)) / np.sqrt((np.std(g1)**2 + np.std(g2)**2) / 2))
        }

    def _anova(self, df: pd.DataFrame, params: Dict[str, Any], alpha: float) -> Dict[str, Any]:
        """One-way ANOVA"""
        col = params.get("column")
        group_col = params.get("group_column")

        groups = [group[col].values for name, group in df.groupby(group_col)]
        f_stat, p_value = stats.f_oneway(*groups)

        return {
            "test": "One-Way ANOVA",
            "statistic": float(f_stat),
            "p_value": float(p_value),
            "significant": p_value < alpha,
            "interpretation": f"{'Significant' if p_value < alpha else 'No significant'} difference among groups (p={p_value:.4f})",
            "num_groups": len(groups)
        }

    def _chi_square(self, df: pd.DataFrame, params: Dict[str, Any], alpha: float) -> Dict[str, Any]:
        """Chi-square test of independence"""
        col1 = params.get("column")
        col2 = params.get("column2")

        contingency = pd.crosstab(df[col1], df[col2])
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

        return {
            "test": "Chi-Square Test",
            "statistic": float(chi2),
            "p_value": float(p_value),
            "degrees_of_freedom": int(dof),
            "significant": p_value < alpha,
            "interpretation": f"Variables are {'associated' if p_value < alpha else 'independent'} (p={p_value:.4f})"
        }

    def _mann_whitney(self, df: pd.DataFrame, params: Dict[str, Any], alpha: float) -> Dict[str, Any]:
        """Mann-Whitney U test (non-parametric)"""
        col = params.get("column")
        group_col = params.get("group_column")

        groups = df.groupby(group_col)[col].apply(list)
        if len(groups) != 2:
            raise ValueError("Mann-Whitney requires exactly 2 groups")

        g1, g2 = list(groups.values())
        u_stat, p_value = stats.mannwhitneyu(g1, g2)

        return {
            "test": "Mann-Whitney U Test",
            "statistic": float(u_stat),
            "p_value": float(p_value),
            "significant": p_value < alpha,
            "interpretation": f"{'Significant' if p_value < alpha else 'No significant'} difference in distributions (p={p_value:.4f})"
        }

    def _kruskal_wallis(self, df: pd.DataFrame, params: Dict[str, Any], alpha: float) -> Dict[str, Any]:
        """Kruskal-Wallis H test"""
        col = params.get("column")
        group_col = params.get("group_column")

        groups = [group[col].values for name, group in df.groupby(group_col)]
        h_stat, p_value = stats.kruskal(*groups)

        return {
            "test": "Kruskal-Wallis H Test",
            "statistic": float(h_stat),
            "p_value": float(p_value),
            "significant": p_value < alpha,
            "interpretation": f"{'Significant' if p_value < alpha else 'No significant'} difference among groups (p={p_value:.4f})"
        }

    def _normality_test(self, df: pd.DataFrame, params: Dict[str, Any], alpha: float) -> Dict[str, Any]:
        """Test for normality (Shapiro-Wilk and Kolmogorov-Smirnov)"""
        col = params.get("column")
        data = df[col].dropna()

        shapiro_stat, shapiro_p = stats.shapiro(data[:5000])
        ks_stat, ks_p = stats.kstest(data, 'norm', args=(data.mean(), data.std()))

        return {
            "test": "Normality Tests",
            "shapiro_wilk": {
                "statistic": float(shapiro_stat),
                "p_value": float(shapiro_p),
                "normal": shapiro_p > alpha
            },
            "kolmogorov_smirnov": {
                "statistic": float(ks_stat),
                "p_value": float(ks_p),
                "normal": ks_p > alpha
            },
            "interpretation": f"Data is {'normally' if shapiro_p > alpha else 'not normally'} distributed (Shapiro-Wilk p={shapiro_p:.4f})",
            "skewness": float(data.skew()),
            "kurtosis": float(data.kurtosis())
        }

    def _correlation_test(self, df: pd.DataFrame, params: Dict[str, Any], alpha: float) -> Dict[str, Any]:
        """Correlation test with significance"""
        col1 = params.get("column")
        col2 = params.get("column2")

        clean_df = df[[col1, col2]].dropna()

        pearson_r, pearson_p = stats.pearsonr(clean_df[col1], clean_df[col2])
        spearman_r, spearman_p = stats.spearmanr(clean_df[col1], clean_df[col2])

        return {
            "test": "Correlation Tests",
            "pearson": {
                "correlation": float(pearson_r),
                "p_value": float(pearson_p),
                "significant": pearson_p < alpha
            },
            "spearman": {
                "correlation": float(spearman_r),
                "p_value": float(spearman_p),
                "significant": spearman_p < alpha
            },
            "interpretation": f"{'Significant' if pearson_p < alpha else 'No significant'} correlation (Pearson r={pearson_r:.3f}, p={pearson_p:.4f})"
        }
