"""
Advanced Visualization Tool - creates publication-quality visualizations
"""
import io
import base64
from typing import Dict, Any, List, Optional
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from app.tools.base_tool import BaseTool
from app.schemas.tool import (
    ToolSchema,
    ToolParameter,
    ToolParameterType,
    ToolResult,
    ToolCapability
)
from app.services.duckdb_service import DuckDBService


class AdvancedVisualizationTool(BaseTool):
    """
    Advanced visualization tool using matplotlib and seaborn

    Creates publication-quality, sophisticated visualizations including:
    - Multi-panel plots
    - Statistical visualizations
    - Distribution analyses
    - Correlation matrices
    - Time series plots
    """

    def __init__(self):
        super().__init__()
        self.duckdb_service = DuckDBService()

        # Set seaborn style for better aesthetics
        sns.set_style("whitegrid")
        sns.set_palette("husl")

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name="advanced_visualization",
            description="Create publication-quality visualizations using matplotlib/seaborn",
            category="visualization",
            parameters=[
                ToolParameter(
                    name="viz_type",
                    type=ToolParameterType.STRING,
                    description="Type of visualization",
                    required=True,
                    enum=[
                        "distribution", "correlation_matrix", "box_plot",
                        "violin_plot", "pair_plot", "heatmap", "time_series",
                        "regression_plot", "categorical_plot", "facet_grid"
                    ]
                ),
                ToolParameter(
                    name="dataset_id",
                    type=ToolParameterType.STRING,
                    description="Dataset ID to visualize",
                    required=True
                ),
                ToolParameter(
                    name="columns",
                    type=ToolParameterType.ARRAY,
                    description="Columns to visualize",
                    required=False
                ),
                ToolParameter(
                    name="x_column",
                    type=ToolParameterType.STRING,
                    description="Column for X axis",
                    required=False
                ),
                ToolParameter(
                    name="y_column",
                    type=ToolParameterType.STRING,
                    description="Column for Y axis",
                    required=False
                ),
                ToolParameter(
                    name="hue_column",
                    type=ToolParameterType.STRING,
                    description="Column for color grouping",
                    required=False
                ),
                ToolParameter(
                    name="title",
                    type=ToolParameterType.STRING,
                    description="Chart title",
                    required=False
                ),
                ToolParameter(
                    name="style",
                    type=ToolParameterType.STRING,
                    description="Visualization style",
                    required=False,
                    enum=["publication", "presentation", "web", "minimal"],
                    default="publication"
                ),
                ToolParameter(
                    name="dpi",
                    type=ToolParameterType.NUMBER,
                    description="DPI for output image",
                    required=False,
                    default=150
                )
            ],
            returns={
                "type": "object",
                "properties": {
                    "image": {"type": "string", "description": "Base64 encoded image"},
                    "format": {"type": "string"},
                    "viz_type": {"type": "string"},
                    "insights": {"type": "array"}
                }
            },
            examples=[
                {
                    "parameters": {
                        "viz_type": "correlation_matrix",
                        "dataset_id": "abc123",
                        "style": "publication"
                    }
                }
            ],
            requires_approval=False,
            is_destructive=False,
            estimated_duration_ms=2000
        )

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="Advanced Visualization",
            description="Create sophisticated, publication-quality visualizations",
            use_cases=[
                "Generate correlation matrices with significance markers",
                "Create multi-panel distribution plots",
                "Build violin and box plots for comparisons",
                "Generate pair plots for multivariate analysis",
                "Create time series visualizations with trends"
            ],
            limitations=[
                "Requires dataset to be loaded in DuckDB",
                "Large datasets may take time to process",
                "Limited to 2D visualizations"
            ]
        )

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute visualization generation

        Args:
            parameters: Tool parameters

        Returns:
            ToolResult with base64 encoded image and insights
        """
        viz_type = parameters["viz_type"]
        dataset_id = parameters["dataset_id"]
        style = parameters.get("style", "publication")
        dpi = parameters.get("dpi", 150)

        try:
            # Apply style
            self._apply_style(style)

            # Get data from DuckDB
            data_df = await self._fetch_data(dataset_id, parameters)

            # Generate visualization based on type
            if viz_type == "distribution":
                fig, insights = self._create_distribution_plot(data_df, parameters)
            elif viz_type == "correlation_matrix":
                fig, insights = self._create_correlation_matrix(data_df, parameters)
            elif viz_type == "box_plot":
                fig, insights = self._create_box_plot(data_df, parameters)
            elif viz_type == "violin_plot":
                fig, insights = self._create_violin_plot(data_df, parameters)
            elif viz_type == "pair_plot":
                fig, insights = self._create_pair_plot(data_df, parameters)
            elif viz_type == "heatmap":
                fig, insights = self._create_heatmap(data_df, parameters)
            elif viz_type == "time_series":
                fig, insights = self._create_time_series(data_df, parameters)
            elif viz_type == "regression_plot":
                fig, insights = self._create_regression_plot(data_df, parameters)
            elif viz_type == "categorical_plot":
                fig, insights = self._create_categorical_plot(data_df, parameters)
            elif viz_type == "facet_grid":
                fig, insights = self._create_facet_grid(data_df, parameters)
            else:
                raise ValueError(f"Unsupported viz_type: {viz_type}")

            # Convert to base64 image
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=dpi, bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            buffer.close()
            plt.close(fig)

            return ToolResult(
                tool_name="advanced_visualization",
                success=True,
                data={
                    "image": image_base64,
                    "format": "png",
                    "viz_type": viz_type,
                    "insights": insights,
                    "style": style,
                    "dpi": dpi
                },
                metadata={
                    "viz_type": viz_type,
                    "num_insights": len(insights),
                    "columns_used": parameters.get("columns", [])
                }
            )

        except Exception as e:
            return ToolResult(
                tool_name="advanced_visualization",
                success=False,
                data={},
                error=f"Visualization failed: {str(e)}"
            )

    def _apply_style(self, style: str):
        """Apply visualization style"""
        if style == "publication":
            sns.set_context("paper", font_scale=1.2)
            sns.set_style("whitegrid")
        elif style == "presentation":
            sns.set_context("talk", font_scale=1.3)
            sns.set_style("darkgrid")
        elif style == "web":
            sns.set_context("notebook", font_scale=1.1)
            sns.set_style("white")
        elif style == "minimal":
            sns.set_context("paper", font_scale=1.0)
            sns.set_style("ticks")

    async def _fetch_data(self, dataset_id: str, parameters: Dict[str, Any]) -> pd.DataFrame:
        """Fetch data from DuckDB"""
        columns = parameters.get("columns")

        if columns:
            cols_str = ", ".join(columns)
            query = f"SELECT {cols_str} FROM dataset LIMIT 5000"
        else:
            query = "SELECT * FROM dataset LIMIT 5000"

        return self.duckdb_service.execute_query(query, dataset_id=dataset_id)

    def _create_distribution_plot(self, data_df: pd.DataFrame, parameters: Dict[str, Any]):
        """Create distribution plots for numeric columns"""
        numeric_cols = data_df.select_dtypes(include=[np.number]).columns
        columns = parameters.get("columns", numeric_cols[:4])  # Max 4 columns

        n_cols = len(columns)
        fig, axes = plt.subplots(n_cols, 2, figsize=(12, 4 * n_cols))
        if n_cols == 1:
            axes = axes.reshape(1, -1)

        insights = []

        for idx, col in enumerate(columns):
            if col not in data_df.columns:
                continue

            # Histogram
            ax1 = axes[idx, 0]
            data_df[col].hist(bins=30, ax=ax1, edgecolor='black', alpha=0.7)
            ax1.set_title(f'{col} - Distribution')
            ax1.set_xlabel(col)
            ax1.set_ylabel('Frequency')

            # Box plot
            ax2 = axes[idx, 1]
            data_df.boxplot(column=col, ax=ax2)
            ax2.set_title(f'{col} - Box Plot')
            ax2.set_ylabel(col)

            # Generate insights
            skewness = data_df[col].skew()
            if abs(skewness) > 1:
                direction = "right" if skewness > 0 else "left"
                insights.append(f"{col} is highly skewed {direction} (skewness: {skewness:.2f})")

            # Check for outliers
            Q1 = data_df[col].quantile(0.25)
            Q3 = data_df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = data_df[(data_df[col] < Q1 - 1.5*IQR) | (data_df[col] > Q3 + 1.5*IQR)]
            if len(outliers) > 0:
                insights.append(f"{col} has {len(outliers)} outliers ({len(outliers)/len(data_df)*100:.1f}%)")

        title = parameters.get("title", "Distribution Analysis")
        fig.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()

        return fig, insights

    def _create_correlation_matrix(self, data_df: pd.DataFrame, parameters: Dict[str, Any]):
        """Create correlation matrix heatmap"""
        numeric_cols = data_df.select_dtypes(include=[np.number]).columns
        corr_matrix = data_df[numeric_cols].corr()

        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(
            corr_matrix,
            annot=True,
            fmt='.2f',
            cmap='coolwarm',
            center=0,
            square=True,
            linewidths=1,
            cbar_kws={"shrink": 0.8},
            ax=ax
        )

        title = parameters.get("title", "Correlation Matrix")
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

        # Generate insights
        insights = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.7:
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    direction = "positive" if corr_val > 0 else "negative"
                    insights.append(f"Strong {direction} correlation between {col1} and {col2}: {corr_val:.2f}")

        return fig, insights

    def _create_box_plot(self, data_df: pd.DataFrame, parameters: Dict[str, Any]):
        """Create box plot for comparing groups"""
        x_col = parameters.get("x_column")
        y_col = parameters.get("y_column")
        hue_col = parameters.get("hue_column")

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.boxplot(data=data_df, x=x_col, y=y_col, hue=hue_col, ax=ax)

        title = parameters.get("title", f"{y_col} by {x_col}")
        ax.set_title(title, fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')

        # Generate insights
        insights = []
        if x_col and y_col:
            group_stats = data_df.groupby(x_col)[y_col].agg(['mean', 'median', 'std'])
            max_group = group_stats['mean'].idxmax()
            min_group = group_stats['mean'].idxmin()
            insights.append(f"Highest average {y_col}: {max_group} ({group_stats.loc[max_group, 'mean']:.2f})")
            insights.append(f"Lowest average {y_col}: {min_group} ({group_stats.loc[min_group, 'mean']:.2f})")

        return fig, insights

    def _create_violin_plot(self, data_df: pd.DataFrame, parameters: Dict[str, Any]):
        """Create violin plot"""
        x_col = parameters.get("x_column")
        y_col = parameters.get("y_column")
        hue_col = parameters.get("hue_column")

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.violinplot(data=data_df, x=x_col, y=y_col, hue=hue_col, ax=ax)

        title = parameters.get("title", f"{y_col} Distribution by {x_col}")
        ax.set_title(title, fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')

        insights = ["Violin plots show full distribution shapes for each group"]

        return fig, insights

    def _create_pair_plot(self, data_df: pd.DataFrame, parameters: Dict[str, Any]):
        """Create pair plot for multivariate analysis"""
        numeric_cols = data_df.select_dtypes(include=[np.number]).columns
        columns = parameters.get("columns", numeric_cols[:4])  # Max 4 for readability
        hue_col = parameters.get("hue_column")

        subset_df = data_df[list(columns) + ([hue_col] if hue_col else [])]

        pair_grid = sns.pairplot(subset_df, hue=hue_col, diag_kind='kde', corner=True)
        fig = pair_grid.fig

        title = parameters.get("title", "Pairwise Relationships")
        fig.suptitle(title, y=1.02, fontsize=14, fontweight='bold')

        insights = [f"Analyzing relationships between {len(columns)} variables"]

        return fig, insights

    def _create_heatmap(self, data_df: pd.DataFrame, parameters: Dict[str, Any]):
        """Create heatmap for 2D data"""
        x_col = parameters.get("x_column")
        y_col = parameters.get("y_column")
        columns = parameters.get("columns", [])

        if x_col and y_col and len(columns) > 2:
            # Pivot table heatmap
            pivot_data = data_df.pivot_table(
                values=columns[2],
                index=y_col,
                columns=x_col,
                aggfunc='mean'
            )
        else:
            # Numeric columns heatmap
            numeric_cols = data_df.select_dtypes(include=[np.number]).columns
            pivot_data = data_df[numeric_cols].head(50)

        fig, ax = plt.subplots(figsize=(12, 8))
        sns.heatmap(pivot_data, annot=False, cmap='YlOrRd', ax=ax, cbar_kws={"shrink": 0.8})

        title = parameters.get("title", "Heatmap")
        ax.set_title(title, fontsize=14, fontweight='bold')

        insights = ["Heatmap shows intensity patterns across dimensions"]

        return fig, insights

    def _create_time_series(self, data_df: pd.DataFrame, parameters: Dict[str, Any]):
        """Create time series plot"""
        x_col = parameters.get("x_column")  # Should be date/time column
        y_col = parameters.get("y_column")

        # Try to convert x_col to datetime
        if x_col:
            data_df[x_col] = pd.to_datetime(data_df[x_col], errors='coerce')
            data_df = data_df.sort_values(x_col)

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(data_df[x_col], data_df[y_col], linewidth=2, marker='o', markersize=3)

        # Add trend line
        if len(data_df) > 1:
            z = np.polyfit(range(len(data_df)), data_df[y_col].values, 1)
            p = np.poly1d(z)
            ax.plot(data_df[x_col], p(range(len(data_df))),
                   linestyle='--', color='red', alpha=0.7, label='Trend')

        title = parameters.get("title", f"{y_col} Over Time")
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.legend()
        plt.xticks(rotation=45, ha='right')

        # Generate insights
        insights = []
        if len(data_df) > 1:
            slope = z[0]
            if abs(slope) > 0.01:
                direction = "increasing" if slope > 0 else "decreasing"
                insights.append(f"{y_col} is {direction} over time (slope: {slope:.4f})")

        return fig, insights

    def _create_regression_plot(self, data_df: pd.DataFrame, parameters: Dict[str, Any]):
        """Create regression plot with confidence interval"""
        x_col = parameters.get("x_column")
        y_col = parameters.get("y_column")

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.regplot(data=data_df, x=x_col, y=y_col, ax=ax, scatter_kws={'alpha':0.5})

        title = parameters.get("title", f"{y_col} vs {x_col} (with regression)")
        ax.set_title(title, fontsize=14, fontweight='bold')

        # Calculate R²
        from scipy.stats import pearsonr
        corr, p_value = pearsonr(data_df[x_col].dropna(), data_df[y_col].dropna())
        r_squared = corr ** 2

        insights = [
            f"R² = {r_squared:.3f}",
            f"Correlation: {corr:.3f} (p-value: {p_value:.4f})"
        ]

        return fig, insights

    def _create_categorical_plot(self, data_df: pd.DataFrame, parameters: Dict[str, Any]):
        """Create categorical plot"""
        x_col = parameters.get("x_column")
        y_col = parameters.get("y_column")
        hue_col = parameters.get("hue_column")

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(data=data_df, x=x_col, y=y_col, hue=hue_col, ax=ax, ci=95)

        title = parameters.get("title", f"{y_col} by {x_col}")
        ax.set_title(title, fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')

        insights = ["Bar heights show mean values with 95% confidence intervals"]

        return fig, insights

    def _create_facet_grid(self, data_df: pd.DataFrame, parameters: Dict[str, Any]):
        """Create facet grid for multi-dimensional analysis"""
        x_col = parameters.get("x_column")
        y_col = parameters.get("y_column")
        hue_col = parameters.get("hue_column")

        # Use first categorical column for faceting
        cat_cols = data_df.select_dtypes(include=['object', 'category']).columns
        row_col = cat_cols[0] if len(cat_cols) > 0 else None

        if row_col:
            g = sns.FacetGrid(data_df, row=row_col, hue=hue_col, height=4, aspect=1.5)
            g.map(sns.scatterplot, x_col, y_col, alpha=0.6)
            g.add_legend()
            fig = g.fig
        else:
            # Fallback to regular scatter
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.scatterplot(data=data_df, x=x_col, y=y_col, hue=hue_col, ax=ax)

        title = parameters.get("title", "Faceted Analysis")
        fig.suptitle(title, y=1.02, fontsize=14, fontweight='bold')

        insights = ["Facet grid shows relationships across different subgroups"]

        return fig, insights
