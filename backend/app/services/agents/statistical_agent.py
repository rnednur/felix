"""
Statistical Analysis Agent - performs statistical analysis on data
"""
from typing import Dict, Any, List
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent import AgentConfig, AgentRequest, AgentResponse, AgentContext
from app.services.duckdb_service import DuckDBService
from app.services.storage_service import StorageService
import json


class StatisticalAgent(BaseAgent):
    """
    Statistical Analysis Agent - performs correlation, distribution, and statistical tests

    Handles: correlation analysis, outlier detection, hypothesis testing,
    distribution analysis, descriptive statistics
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.duckdb_service = DuckDBService()
        self.storage_service = StorageService()

    def can_handle(self, request: AgentRequest) -> float:
        """
        Calculate confidence for handling statistical analysis requests

        High confidence for queries like:
        - "Is X correlated with Y?"
        - "Find outliers in..."
        - "Test if there's a difference..."
        - "What's the distribution of..."
        - "Calculate statistics for..."
        """
        return self.calculate_confidence(
            request.query,
            self.config.intent_keywords
        )

    async def process(self, request: AgentRequest, context: AgentContext) -> AgentResponse:
        """
        Process statistical analysis request

        Args:
            request: Agent request with statistical analysis intent
            context: Execution context

        Returns:
            AgentResponse with statistical results
        """
        try:
            self.logger.info(f"Performing statistical analysis on dataset: {request.dataset_id}")

            # Get dataset info from database
            from app.core.database import get_db
            from app.models import Dataset

            db = next(get_db())
            dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
            if not dataset:
                raise Exception(f"Dataset {request.dataset_id} not found")

            # In DuckDB, table is always called "dataset"
            table_name = "dataset"

            # Get schema by querying information schema
            schema_query = """
                SELECT column_name, column_type
                FROM (DESCRIBE dataset)
            """
            schema_result = self.duckdb_service.execute_query(schema_query, dataset_id=dataset.id)

            # Convert to schema format
            schema_info = {
                'columns': [
                    {'name': row['column_name'], 'type': row['column_type']}
                    for _, row in schema_result.iterrows()
                ]
            }

            # Determine analysis type from query
            analysis_type = self._determine_analysis_type(request.query)

            # Perform analysis
            if analysis_type == 'correlation':
                results = self._analyze_correlation(table_name, schema_info, request.query, dataset.id)
            elif analysis_type == 'outliers':
                results = self._detect_outliers(table_name, schema_info, request.query, dataset.id)
            elif analysis_type == 'distribution':
                results = self._analyze_distribution(table_name, schema_info, request.query, dataset.id)
            elif analysis_type == 'descriptive':
                results = self._descriptive_statistics(table_name, schema_info, dataset.id)
            else:
                # Default to descriptive stats
                results = self._descriptive_statistics(table_name, schema_info, dataset.id)

            response_data = {
                'summary': results.get('summary', 'Statistical analysis complete'),
                'analysis_type': analysis_type,
                'results': results.get('results', {}),
                'insights': results.get('insights', []),
                'type': 'statistical_analysis'
            }

            response = AgentResponse(
                agent_name=self.config.name,
                success=True,
                data=response_data,
                metadata={
                    'analysis_type': analysis_type,
                    'columns_analyzed': results.get('columns_analyzed', [])
                }
            )

            self.log_execution(request, response)
            return response

        except Exception as e:
            self.logger.error(f"Statistical agent failed: {str(e)}", exc_info=True)

            error_response = AgentResponse(
                agent_name=self.config.name,
                success=False,
                data={},
                error=f"Statistical analysis failed: {str(e)}"
            )

            self.log_execution(request, error_response)
            return error_response

    def _determine_analysis_type(self, query: str) -> str:
        """Determine which type of statistical analysis to perform"""
        query_lower = query.lower()

        if any(word in query_lower for word in ['correlat', 'relationship', 'association']):
            return 'correlation'
        elif any(word in query_lower for word in ['outlier', 'anomal', 'unusual']):
            return 'outliers'
        elif any(word in query_lower for word in ['distribution', 'spread', 'histogram']):
            return 'distribution'
        else:
            return 'descriptive'

    def _analyze_correlation(self, table_name: str, schema: Dict[str, Any], query: str, dataset_id: str) -> Dict[str, Any]:
        """Analyze correlations between numeric columns"""
        # Get numeric columns
        numeric_cols = [c for c in schema.get('columns', [])
                       if c['type'] in ('INTEGER', 'DOUBLE', 'DECIMAL', 'BIGINT', 'FLOAT')]

        if len(numeric_cols) < 2:
            return {
                'summary': 'Not enough numeric columns for correlation analysis',
                'results': {},
                'insights': ['Need at least 2 numeric columns']
            }

        # Calculate correlations using SQL
        correlations = []
        insights = []

        for i, col1 in enumerate(numeric_cols):
            for col2 in numeric_cols[i+1:]:
                # Pearson correlation using SQL
                sql = f"""
                SELECT
                    CORR({col1['name']}, {col2['name']}) as correlation
                FROM {table_name}
                WHERE {col1['name']} IS NOT NULL AND {col2['name']} IS NOT NULL
                """
                result_df = self.duckdb_service.execute_query(sql, dataset_id=dataset_id)

                if not result_df.empty and result_df.iloc[0].get('correlation') is not None:
                    corr_value = float(result_df.iloc[0]['correlation'])
                    correlations.append({
                        'column_1': col1['name'],
                        'column_2': col2['name'],
                        'correlation': round(corr_value, 3)
                    })

                    # Generate insights for strong correlations
                    if abs(corr_value) > 0.7:
                        direction = 'positive' if corr_value > 0 else 'negative'
                        insights.append(
                            f"Strong {direction} correlation ({corr_value:.2f}) between {col1['name']} and {col2['name']}"
                        )

        # Sort by absolute correlation value
        correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)

        return {
            'summary': f"Analyzed correlations between {len(numeric_cols)} numeric columns",
            'results': {
                'correlations': correlations[:10],  # Top 10
                'columns_analyzed': [c['name'] for c in numeric_cols]
            },
            'insights': insights,
            'columns_analyzed': [c['name'] for c in numeric_cols]
        }

    def _detect_outliers(self, table_name: str, schema: Dict[str, Any], query: str, dataset_id: str) -> Dict[str, Any]:
        """Detect outliers using IQR method"""
        numeric_cols = [c for c in schema.get('columns', [])
                       if c['type'] in ('INTEGER', 'DOUBLE', 'DECIMAL', 'BIGINT', 'FLOAT')]

        if not numeric_cols:
            return {
                'summary': 'No numeric columns found for outlier detection',
                'results': {},
                'insights': []
            }

        outlier_results = []
        insights = []

        for col in numeric_cols[:5]:  # Limit to first 5 numeric columns
            # Calculate quartiles and IQR
            sql = f"""
            SELECT
                APPROX_QUANTILE({col['name']}, 0.25) as q1,
                APPROX_QUANTILE({col['name']}, 0.50) as median,
                APPROX_QUANTILE({col['name']}, 0.75) as q3,
                MIN({col['name']}) as min_val,
                MAX({col['name']}) as max_val
            FROM {table_name}
            WHERE {col['name']} IS NOT NULL
            """
            stats_df = self.duckdb_service.execute_query(sql, dataset_id=dataset_id)

            if not stats_df.empty:
                stats = stats_df.iloc[0]
                q1 = stats['q1']
                q3 = stats['q3']
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr

                # Count outliers
                outlier_sql = f"""
                SELECT COUNT(*) as outlier_count
                FROM {table_name}
                WHERE {col['name']} < {lower_bound} OR {col['name']} > {upper_bound}
                """
                outlier_count_df = self.duckdb_service.execute_query(outlier_sql, dataset_id=dataset_id)
                outlier_count = outlier_count_df.iloc[0]['outlier_count'] if not outlier_count_df.empty else 0

                outlier_results.append({
                    'column': col['name'],
                    'outlier_count': outlier_count,
                    'lower_bound': round(lower_bound, 2),
                    'upper_bound': round(upper_bound, 2),
                    'q1': round(q1, 2),
                    'median': round(stats['median'], 2),
                    'q3': round(q3, 2)
                })

                if outlier_count > 0:
                    insights.append(f"Found {outlier_count} outliers in {col['name']}")

        return {
            'summary': f"Outlier detection completed for {len(outlier_results)} columns",
            'results': {
                'outliers': outlier_results
            },
            'insights': insights,
            'columns_analyzed': [r['column'] for r in outlier_results]
        }

    def _analyze_distribution(self, table_name: str, schema: Dict[str, Any], query: str, dataset_id: str) -> Dict[str, Any]:
        """Analyze distribution of numeric columns"""
        numeric_cols = [c for c in schema.get('columns', [])
                       if c['type'] in ('INTEGER', 'DOUBLE', 'DECIMAL', 'BIGINT', 'FLOAT')]

        if not numeric_cols:
            return {
                'summary': 'No numeric columns found',
                'results': {},
                'insights': []
            }

        distributions = []
        insights = []

        for col in numeric_cols[:5]:
            sql = f"""
            SELECT
                AVG({col['name']}) as mean,
                STDDEV_POP({col['name']}) as std_dev,
                APPROX_QUANTILE({col['name']}, 0.25) as q1,
                APPROX_QUANTILE({col['name']}, 0.50) as median,
                APPROX_QUANTILE({col['name']}, 0.75) as q3,
                MIN({col['name']}) as min_val,
                MAX({col['name']}) as max_val
            FROM {table_name}
            WHERE {col['name']} IS NOT NULL
            """
            result_df = self.duckdb_service.execute_query(sql, dataset_id=dataset_id)

            if not result_df.empty:
                stats = result_df.iloc[0]
                mean = stats['mean']
                median = stats['median']

                distributions.append({
                    'column': col['name'],
                    'mean': round(mean, 2),
                    'median': round(median, 2),
                    'std_dev': round(stats['std_dev'], 2) if stats['std_dev'] else 0,
                    'min': round(stats['min_val'], 2),
                    'max': round(stats['max_val'], 2),
                    'range': round(stats['max_val'] - stats['min_val'], 2)
                })

                # Check for skewness
                if abs(mean - median) / (stats['std_dev'] or 1) > 0.5:
                    skew_direction = 'right' if mean > median else 'left'
                    insights.append(f"{col['name']} is skewed {skew_direction}")

        return {
            'summary': f"Distribution analysis for {len(distributions)} columns",
            'results': {
                'distributions': distributions
            },
            'insights': insights,
            'columns_analyzed': [d['column'] for d in distributions]
        }

    def _descriptive_statistics(self, table_name: str, schema: Dict[str, Any], dataset_id: str) -> Dict[str, Any]:
        """Calculate descriptive statistics for all numeric columns"""
        numeric_cols = [c for c in schema.get('columns', [])
                       if c['type'] in ('INTEGER', 'DOUBLE', 'DECIMAL', 'BIGINT', 'FLOAT')]

        if not numeric_cols:
            return {
                'summary': 'No numeric columns found',
                'results': {},
                'insights': []
            }

        stats_list = []

        for col in numeric_cols:
            sql = f"""
            SELECT
                COUNT({col['name']}) as count,
                AVG({col['name']}) as mean,
                MIN({col['name']}) as min,
                MAX({col['name']}) as max,
                STDDEV_POP({col['name']}) as std_dev
            FROM {table_name}
            WHERE {col['name']} IS NOT NULL
            """
            result_df = self.duckdb_service.execute_query(sql, dataset_id=dataset_id)

            if not result_df.empty:
                result = result_df.iloc[0]
                stats_list.append({
                    'column': col['name'],
                    **{k: round(v, 2) if v is not None else 0 for k, v in result.items()}
                })

        return {
            'summary': f"Descriptive statistics for {len(stats_list)} numeric columns",
            'results': {
                'statistics': stats_list
            },
            'insights': [f"Analyzed {len(stats_list)} numeric columns"],
            'columns_analyzed': [s['column'] for s in stats_list]
        }
