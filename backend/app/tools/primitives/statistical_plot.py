"""
Statistical Plot Tool - creates statistical analysis visualizations
"""
import io
import base64
from typing import Dict, Any, List, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from scipy import stats
from app.tools.base_tool import BaseTool
from app.schemas.tool import (
    ToolSchema,
    ToolParameter,
    ToolParameterType,
    ToolResult,
    ToolCapability
)
from app.services.duckdb_service import DuckDBService


class StatisticalPlotTool(BaseTool):
    """
    Statistical plot tool for analysis visualizations

    Creates statistical diagnostic plots including:
    - Q-Q plots for normality testing
    - Residual plots for regression diagnostics
    - Probability plots
    - Statistical test visualizations
    """

    def __init__(self):
        super().__init__()
        self.duckdb_service = DuckDBService()
        sns.set_style("whitegrid")

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name="statistical_plot",
            description="Create statistical diagnostic and analysis plots",
            category="visualization",
            parameters=[
                ToolParameter(
                    name="plot_type",
                    type=ToolParameterType.STRING,
                    description="Type of statistical plot",
                    required=True,
                    enum=[
                        "qq_plot", "residual_plot", "probability_plot",
                        "bland_altman", "roc_curve", "statistical_comparison",
                        "effect_size", "confidence_intervals"
                    ]
                ),
                ToolParameter(
                    name="dataset_id",
                    type=ToolParameterType.STRING,
                    description="Dataset ID",
                    required=True
                ),
                ToolParameter(
                    name="column",
                    type=ToolParameterType.STRING,
                    description="Primary column for analysis",
                    required=False
                ),
                ToolParameter(
                    name="x_column",
                    type=ToolParameterType.STRING,
                    description="X column (for 2-variable plots)",
                    required=False
                ),
                ToolParameter(
                    name="y_column",
                    type=ToolParameterType.STRING,
                    description="Y column (for 2-variable plots)",
                    required=False
                ),
                ToolParameter(
                    name="group_column",
                    type=ToolParameterType.STRING,
                    description="Column for grouping/comparison",
                    required=False
                ),
                ToolParameter(
                    name="title",
                    type=ToolParameterType.STRING,
                    description="Plot title",
                    required=False
                ),
                ToolParameter(
                    name="dpi",
                    type=ToolParameterType.NUMBER,
                    description="DPI for output",
                    required=False,
                    default=150
                )
            ],
            returns={
                "type": "object",
                "properties": {
                    "image": {"type": "string"},
                    "statistical_summary": {"type": "object"},
                    "interpretation": {"type": "array"}
                }
            },
            examples=[
                {
                    "parameters": {
                        "plot_type": "qq_plot",
                        "dataset_id": "abc123",
                        "column": "sales"
                    }
                }
            ],
            requires_approval=False,
            is_destructive=False,
            estimated_duration_ms=1500
        )

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="Statistical Plotting",
            description="Create statistical diagnostic and analysis visualizations",
            use_cases=[
                "Test data normality with Q-Q plots",
                "Diagnose regression models with residual plots",
                "Compare groups with statistical visualizations",
                "Visualize confidence intervals and effect sizes",
                "Create probability plots for distribution fitting"
            ],
            limitations=[
                "Requires numerical data for most plots",
                "Some plots need specific data structures",
                "Limited to common statistical tests"
            ]
        )

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute statistical plot generation"""
        plot_type = parameters["plot_type"]
        dataset_id = parameters["dataset_id"]
        dpi = parameters.get("dpi", 150)

        try:
            # Fetch data
            data_df = await self._fetch_data(dataset_id, parameters)

            # Generate plot based on type
            if plot_type == "qq_plot":
                fig, stats_summary, interpretation = self._create_qq_plot(data_df, parameters)
            elif plot_type == "residual_plot":
                fig, stats_summary, interpretation = self._create_residual_plot(data_df, parameters)
            elif plot_type == "probability_plot":
                fig, stats_summary, interpretation = self._create_probability_plot(data_df, parameters)
            elif plot_type == "bland_altman":
                fig, stats_summary, interpretation = self._create_bland_altman(data_df, parameters)
            elif plot_type == "statistical_comparison":
                fig, stats_summary, interpretation = self._create_statistical_comparison(data_df, parameters)
            elif plot_type == "effect_size":
                fig, stats_summary, interpretation = self._create_effect_size_plot(data_df, parameters)
            elif plot_type == "confidence_intervals":
                fig, stats_summary, interpretation = self._create_confidence_intervals(data_df, parameters)
            else:
                raise ValueError(f"Unsupported plot_type: {plot_type}")

            # Convert to base64
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            buffer.close()
            plt.close(fig)

            return ToolResult(
                tool_name="statistical_plot",
                success=True,
                data={
                    "image": image_base64,
                    "format": "png",
                    "plot_type": plot_type,
                    "statistical_summary": stats_summary,
                    "interpretation": interpretation
                },
                metadata={
                    "plot_type": plot_type,
                    "num_interpretations": len(interpretation)
                }
            )

        except Exception as e:
            return ToolResult(
                tool_name="statistical_plot",
                success=False,
                data={},
                error=f"Statistical plot failed: {str(e)}"
            )

    async def _fetch_data(self, dataset_id: str, parameters: Dict[str, Any]) -> pd.DataFrame:
        """Fetch relevant data"""
        columns = []
        if parameters.get("column"):
            columns.append(parameters["column"])
        if parameters.get("x_column"):
            columns.append(parameters["x_column"])
        if parameters.get("y_column"):
            columns.append(parameters["y_column"])
        if parameters.get("group_column"):
            columns.append(parameters["group_column"])

        if columns:
            cols_str = ", ".join(set(columns))
            query = f"SELECT {cols_str} FROM dataset LIMIT 5000"
        else:
            query = "SELECT * FROM dataset LIMIT 5000"

        return self.duckdb_service.execute_query(query, dataset_id=dataset_id)

    def _create_qq_plot(self, data_df: pd.DataFrame, parameters: Dict[str, Any]):
        """Create Q-Q plot for normality testing"""
        column = parameters.get("column")
        if not column:
            # Use first numeric column
            numeric_cols = data_df.select_dtypes(include=[np.number]).columns
            column = numeric_cols[0] if len(numeric_cols) > 0 else None

        if not column:
            raise ValueError("No numeric column found for Q-Q plot")

        data = data_df[column].dropna()

        fig, ax = plt.subplots(figsize=(8, 8))
        stats.probplot(data, dist="norm", plot=ax)

        title = parameters.get("title", f"Q-Q Plot: {column}")
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        # Statistical tests
        shapiro_stat, shapiro_p = stats.shapiro(data[:5000])  # Shapiro limited to 5000
        ks_stat, ks_p = stats.kstest(data, 'norm', args=(data.mean(), data.std()))

        stats_summary = {
            "shapiro_test": {
                "statistic": float(shapiro_stat),
                "p_value": float(shapiro_p),
                "normal": shapiro_p > 0.05
            },
            "ks_test": {
                "statistic": float(ks_stat),
                "p_value": float(ks_p),
                "normal": ks_p > 0.05
            },
            "skewness": float(data.skew()),
            "kurtosis": float(data.kurtosis())
        }

        interpretation = []
        if shapiro_p > 0.05:
            interpretation.append(f"Data appears normally distributed (Shapiro-Wilk p={shapiro_p:.4f})")
        else:
            interpretation.append(f"Data deviates from normality (Shapiro-Wilk p={shapiro_p:.4f})")

        skew = data.skew()
        if abs(skew) < 0.5:
            interpretation.append("Distribution is approximately symmetric")
        elif skew > 0:
            interpretation.append(f"Distribution is right-skewed (skewness={skew:.2f})")
        else:
            interpretation.append(f"Distribution is left-skewed (skewness={skew:.2f})")

        return fig, stats_summary, interpretation

    def _create_residual_plot(self, data_df: pd.DataFrame, parameters: Dict[str, Any]):
        """Create residual plot for regression diagnostics"""
        x_col = parameters.get("x_column")
        y_col = parameters.get("y_column")

        if not x_col or not y_col:
            raise ValueError("Both x_column and y_column required for residual plot")

        # Clean data
        clean_df = data_df[[x_col, y_col]].dropna()
        X = clean_df[x_col].values
        y = clean_df[y_col].values

        # Fit linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)
        y_pred = slope * X + intercept
        residuals = y - y_pred

        # Create 2x2 plot
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))

        # 1. Residuals vs Fitted
        axes[0, 0].scatter(y_pred, residuals, alpha=0.5)
        axes[0, 0].axhline(y=0, color='red', linestyle='--')
        axes[0, 0].set_xlabel('Fitted Values')
        axes[0, 0].set_ylabel('Residuals')
        axes[0, 0].set_title('Residuals vs Fitted')
        axes[0, 0].grid(True, alpha=0.3)

        # 2. Q-Q plot of residuals
        stats.probplot(residuals, dist="norm", plot=axes[0, 1])
        axes[0, 1].set_title('Normal Q-Q Plot')

        # 3. Scale-Location plot
        standardized_residuals = residuals / np.std(residuals)
        axes[1, 0].scatter(y_pred, np.sqrt(np.abs(standardized_residuals)), alpha=0.5)
        axes[1, 0].set_xlabel('Fitted Values')
        axes[1, 0].set_ylabel('√|Standardized Residuals|')
        axes[1, 0].set_title('Scale-Location Plot')
        axes[1, 0].grid(True, alpha=0.3)

        # 4. Residual histogram
        axes[1, 1].hist(residuals, bins=30, edgecolor='black', alpha=0.7)
        axes[1, 1].set_xlabel('Residuals')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].set_title('Residual Distribution')
        axes[1, 1].grid(True, alpha=0.3)

        title = parameters.get("title", "Regression Diagnostics")
        fig.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()

        stats_summary = {
            "r_squared": float(r_value ** 2),
            "p_value": float(p_value),
            "std_error": float(std_err),
            "residual_mean": float(np.mean(residuals)),
            "residual_std": float(np.std(residuals))
        }

        interpretation = []
        interpretation.append(f"R² = {r_value**2:.4f} - {self._interpret_r_squared(r_value**2)}")

        if abs(np.mean(residuals)) < 0.1 * np.std(residuals):
            interpretation.append("Residuals are centered around zero (good)")
        else:
            interpretation.append("Residuals are not centered around zero (potential bias)")

        # Durbin-Watson test for autocorrelation
        dw = self._durbin_watson(residuals)
        if 1.5 < dw < 2.5:
            interpretation.append(f"No strong autocorrelation detected (DW={dw:.2f})")
        else:
            interpretation.append(f"Possible autocorrelation in residuals (DW={dw:.2f})")

        return fig, stats_summary, interpretation

    def _create_probability_plot(self, data_df: pd.DataFrame, parameters: Dict[str, Any]):
        """Create probability plot for distribution testing"""
        column = parameters.get("column")
        if not column:
            numeric_cols = data_df.select_dtypes(include=[np.number]).columns
            column = numeric_cols[0]

        data = data_df[column].dropna()

        # Test multiple distributions
        distributions = ['norm', 'expon', 'lognorm', 'gamma']
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.flatten()

        fit_results = {}

        for idx, dist_name in enumerate(distributions):
            ax = axes[idx]
            stats.probplot(data, dist=dist_name, plot=ax)
            ax.set_title(f'{dist_name.capitalize()} Probability Plot')
            ax.grid(True, alpha=0.3)

            # KS test
            if dist_name == 'norm':
                ks_stat, ks_p = stats.kstest(data, dist_name, args=(data.mean(), data.std()))
            else:
                try:
                    params = getattr(stats, dist_name).fit(data)
                    ks_stat, ks_p = stats.kstest(data, dist_name, args=params)
                except:
                    ks_stat, ks_p = np.nan, np.nan

            fit_results[dist_name] = {"ks_stat": float(ks_stat), "p_value": float(ks_p)}

        title = parameters.get("title", f"Probability Plots: {column}")
        fig.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()

        stats_summary = {"distribution_fits": fit_results}

        interpretation = []
        best_fit = max(fit_results.items(), key=lambda x: x[1].get('p_value', 0))
        interpretation.append(f"Best fit distribution: {best_fit[0]} (p={best_fit[1]['p_value']:.4f})")

        return fig, stats_summary, interpretation

    def _create_bland_altman(self, data_df: pd.DataFrame, parameters: Dict[str, Any]):
        """Create Bland-Altman plot for method comparison"""
        x_col = parameters.get("x_column")
        y_col = parameters.get("y_column")

        if not x_col or not y_col:
            raise ValueError("Both x_column and y_column required")

        clean_df = data_df[[x_col, y_col]].dropna()
        method1 = clean_df[x_col].values
        method2 = clean_df[y_col].values

        mean = (method1 + method2) / 2
        diff = method1 - method2

        mean_diff = np.mean(diff)
        std_diff = np.std(diff)

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(mean, diff, alpha=0.5)
        ax.axhline(mean_diff, color='red', linestyle='-', label=f'Mean: {mean_diff:.2f}')
        ax.axhline(mean_diff + 1.96*std_diff, color='red', linestyle='--',
                  label=f'+1.96 SD: {mean_diff + 1.96*std_diff:.2f}')
        ax.axhline(mean_diff - 1.96*std_diff, color='red', linestyle='--',
                  label=f'-1.96 SD: {mean_diff - 1.96*std_diff:.2f}')

        ax.set_xlabel('Mean of Methods')
        ax.set_ylabel('Difference (Method 1 - Method 2)')
        title = parameters.get("title", "Bland-Altman Plot")
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        stats_summary = {
            "mean_difference": float(mean_diff),
            "std_difference": float(std_diff),
            "upper_limit": float(mean_diff + 1.96*std_diff),
            "lower_limit": float(mean_diff - 1.96*std_diff)
        }

        interpretation = []
        if abs(mean_diff) < 0.1 * std_diff:
            interpretation.append("Methods have good agreement (low bias)")
        else:
            interpretation.append(f"Methods show systematic bias: {mean_diff:.2f}")

        outliers = np.sum((diff < mean_diff - 1.96*std_diff) | (diff > mean_diff + 1.96*std_diff))
        interpretation.append(f"{outliers} measurements ({outliers/len(diff)*100:.1f}%) outside 95% limits")

        return fig, stats_summary, interpretation

    def _create_statistical_comparison(self, data_df: pd.DataFrame, parameters: Dict[str, Any]):
        """Create statistical comparison visualization"""
        y_col = parameters.get("y_column")
        group_col = parameters.get("group_column")

        if not y_col or not group_col:
            raise ValueError("Both y_column and group_column required")

        fig, axes = plt.subplots(1, 2, figsize=(14, 6))

        # Box plot comparison
        sns.boxplot(data=data_df, x=group_col, y=y_col, ax=axes[0])
        axes[0].set_title('Group Comparison (Box Plot)')
        axes[0].tick_params(axis='x', rotation=45)

        # Violin plot
        sns.violinplot(data=data_df, x=group_col, y=y_col, ax=axes[1])
        axes[1].set_title('Group Comparison (Violin Plot)')
        axes[1].tick_params(axis='x', rotation=45)

        title = parameters.get("title", f"Statistical Comparison: {y_col} by {group_col}")
        fig.suptitle(title, fontsize=14, fontweight='bold')
        plt.tight_layout()

        # Statistical tests
        groups = [group[y_col].values for name, group in data_df.groupby(group_col)]
        if len(groups) == 2:
            t_stat, p_value = stats.ttest_ind(groups[0], groups[1])
            test_name = "t-test"
        else:
            t_stat, p_value = stats.f_oneway(*groups)
            test_name = "ANOVA"

        stats_summary = {
            "test": test_name,
            "statistic": float(t_stat),
            "p_value": float(p_value),
            "significant": p_value < 0.05,
            "group_means": {name: float(group[y_col].mean())
                          for name, group in data_df.groupby(group_col)}
        }

        interpretation = []
        if p_value < 0.05:
            interpretation.append(f"Significant difference found ({test_name} p={p_value:.4f})")
        else:
            interpretation.append(f"No significant difference ({test_name} p={p_value:.4f})")

        return fig, stats_summary, interpretation

    def _create_effect_size_plot(self, data_df: pd.DataFrame, parameters: Dict[str, Any]):
        """Create effect size visualization"""
        y_col = parameters.get("y_column")
        group_col = parameters.get("group_column")

        if not y_col or not group_col:
            raise ValueError("Both y_column and group_column required")

        groups = data_df.groupby(group_col)[y_col]
        group_names = list(groups.groups.keys())

        # Calculate Cohen's d for pairwise comparisons
        effect_sizes = []
        comparisons = []

        for i in range(len(group_names)):
            for j in range(i+1, len(group_names)):
                g1 = groups.get_group(group_names[i])
                g2 = groups.get_group(group_names[j])

                cohens_d = (g1.mean() - g2.mean()) / np.sqrt((g1.std()**2 + g2.std()**2) / 2)
                effect_sizes.append(cohens_d)
                comparisons.append(f"{group_names[i]} vs {group_names[j]}")

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['green' if abs(es) < 0.5 else 'orange' if abs(es) < 0.8 else 'red'
                 for es in effect_sizes]
        ax.barh(comparisons, effect_sizes, color=colors, alpha=0.7)
        ax.axvline(0, color='black', linestyle='-', linewidth=0.8)
        ax.axvline(0.5, color='gray', linestyle='--', alpha=0.5, label='Medium effect')
        ax.axvline(-0.5, color='gray', linestyle='--', alpha=0.5)
        ax.axvline(0.8, color='gray', linestyle=':', alpha=0.5, label='Large effect')
        ax.axvline(-0.8, color='gray', linestyle=':', alpha=0.5)

        ax.set_xlabel("Cohen's d")
        ax.set_ylabel("Comparison")
        title = parameters.get("title", "Effect Sizes (Cohen's d)")
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='x')

        stats_summary = {
            "comparisons": {comp: float(es) for comp, es in zip(comparisons, effect_sizes)}
        }

        interpretation = []
        for comp, es in zip(comparisons, effect_sizes):
            magnitude = "small" if abs(es) < 0.5 else "medium" if abs(es) < 0.8 else "large"
            interpretation.append(f"{comp}: {magnitude} effect (d={es:.2f})")

        return fig, stats_summary, interpretation

    def _create_confidence_intervals(self, data_df: pd.DataFrame, parameters: Dict[str, Any]):
        """Create confidence interval visualization"""
        y_col = parameters.get("y_column")
        group_col = parameters.get("group_column")

        if not y_col or not group_col:
            raise ValueError("Both y_column and group_column required")

        groups = data_df.groupby(group_col)[y_col]
        group_names = []
        means = []
        cis_lower = []
        cis_upper = []

        for name, group in groups:
            group_names.append(name)
            mean = group.mean()
            sem = stats.sem(group)
            ci = stats.t.interval(0.95, len(group)-1, loc=mean, scale=sem)

            means.append(mean)
            cis_lower.append(ci[0])
            cis_upper.append(ci[1])

        fig, ax = plt.subplots(figsize=(10, 6))
        y_pos = np.arange(len(group_names))

        ax.barh(y_pos, means, xerr=[np.array(means) - np.array(cis_lower),
                                    np.array(cis_upper) - np.array(means)],
               alpha=0.7, capsize=5, error_kw={'linewidth': 2})
        ax.set_yticks(y_pos)
        ax.set_yticklabels(group_names)
        ax.set_xlabel(y_col)
        ax.set_ylabel(group_col)

        title = parameters.get("title", "Group Means with 95% Confidence Intervals")
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')

        stats_summary = {
            "groups": {
                name: {
                    "mean": float(mean),
                    "ci_lower": float(ci_l),
                    "ci_upper": float(ci_u)
                }
                for name, mean, ci_l, ci_u in zip(group_names, means, cis_lower, cis_upper)
            }
        }

        interpretation = []
        # Check for overlapping CIs
        for i in range(len(group_names)):
            for j in range(i+1, len(group_names)):
                if cis_lower[i] > cis_upper[j] or cis_lower[j] > cis_upper[i]:
                    interpretation.append(
                        f"{group_names[i]} and {group_names[j]} have non-overlapping CIs (likely significant)"
                    )

        return fig, stats_summary, interpretation

    def _interpret_r_squared(self, r2: float) -> str:
        """Interpret R² value"""
        if r2 > 0.9:
            return "Excellent fit"
        elif r2 > 0.7:
            return "Strong fit"
        elif r2 > 0.5:
            return "Moderate fit"
        elif r2 > 0.3:
            return "Weak fit"
        else:
            return "Very weak fit"

    def _durbin_watson(self, residuals: np.ndarray) -> float:
        """Calculate Durbin-Watson statistic"""
        diff_residuals = np.diff(residuals)
        dw = np.sum(diff_residuals**2) / np.sum(residuals**2)
        return dw
