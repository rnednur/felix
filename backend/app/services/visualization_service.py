import pandas as pd
import numpy as np
from typing import List, Dict, Any


class VizService:
    """Generate chart suggestions and Vega-Lite specs"""

    def suggest_charts(self, df: pd.DataFrame, nl_query: str = None) -> List[Dict[str, Any]]:
        """Suggest appropriate chart types based on data shape"""
        suggestions = []

        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()

        # Bar chart: 1 categorical + 1 numeric
        if len(cat_cols) >= 1 and len(num_cols) >= 1:
            suggestions.append({
                'type': 'bar',
                'spec': self.generate_vega_bar(df, cat_cols[0], num_cols[0])
            })

        # Line chart: time series
        if len(date_cols) >= 1 and len(num_cols) >= 1:
            suggestions.append({
                'type': 'line',
                'spec': self.generate_vega_line(df, date_cols[0], num_cols[0])
            })

        # Scatter: 2 numeric
        if len(num_cols) >= 2:
            suggestions.append({
                'type': 'scatter',
                'spec': self.generate_vega_scatter(df, num_cols[0], num_cols[1])
            })

        # Heatmap: categorical x categorical with numeric
        if len(cat_cols) >= 2 and len(num_cols) >= 1:
            suggestions.append({
                'type': 'heatmap',
                'spec': self.generate_vega_heatmap(df, cat_cols[0], cat_cols[1], num_cols[0])
            })

        return suggestions[:5]  # Return top 5

    def generate_vega_bar(self, df: pd.DataFrame, x_col: str, y_col: str) -> Dict[str, Any]:
        """Generate Vega-Lite spec for bar chart"""
        # Aggregate and prepare data
        data = df.groupby(x_col)[y_col].sum().reset_index()
        data = data.nlargest(20, y_col)  # Top 20
        data_dict = data.to_dict('records')

        return {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "data": {"values": data_dict},
            "mark": "bar",
            "encoding": {
                "x": {
                    "field": x_col,
                    "type": "nominal",
                    "sort": "-y",
                    "axis": {"labelAngle": -45}
                },
                "y": {
                    "field": y_col,
                    "type": "quantitative",
                    "axis": {"title": y_col}
                }
            },
            "width": 600,
            "height": 400
        }

    def generate_vega_line(self, df: pd.DataFrame, x_col: str, y_col: str) -> Dict[str, Any]:
        """Generate Vega-Lite spec for line chart"""
        data = df[[x_col, y_col]].sort_values(x_col)
        data_dict = data.head(1000).to_dict('records')

        return {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "data": {"values": data_dict},
            "mark": {"type": "line", "point": True},
            "encoding": {
                "x": {
                    "field": x_col,
                    "type": "temporal",
                    "axis": {"title": x_col}
                },
                "y": {
                    "field": y_col,
                    "type": "quantitative",
                    "axis": {"title": y_col}
                }
            },
            "width": 600,
            "height": 400
        }

    def generate_vega_scatter(self, df: pd.DataFrame, x_col: str, y_col: str) -> Dict[str, Any]:
        """Generate Vega-Lite spec for scatter plot"""
        data = df[[x_col, y_col]].dropna()
        data_dict = data.head(1000).to_dict('records')

        return {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "data": {"values": data_dict},
            "mark": "point",
            "encoding": {
                "x": {
                    "field": x_col,
                    "type": "quantitative",
                    "axis": {"title": x_col}
                },
                "y": {
                    "field": y_col,
                    "type": "quantitative",
                    "axis": {"title": y_col}
                }
            },
            "width": 600,
            "height": 400
        }

    def generate_vega_heatmap(self, df: pd.DataFrame, x_col: str, y_col: str,
                             value_col: str) -> Dict[str, Any]:
        """Generate Vega-Lite spec for heatmap"""
        data = df.groupby([x_col, y_col])[value_col].sum().reset_index()
        data_dict = data.to_dict('records')

        return {
            "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
            "data": {"values": data_dict},
            "mark": "rect",
            "encoding": {
                "x": {
                    "field": x_col,
                    "type": "nominal"
                },
                "y": {
                    "field": y_col,
                    "type": "nominal"
                },
                "color": {
                    "field": value_col,
                    "type": "quantitative"
                }
            },
            "width": 600,
            "height": 400
        }
