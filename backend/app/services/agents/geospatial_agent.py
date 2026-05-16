"""
Geospatial Agent - handles location-based queries and map visualizations
"""
from typing import Dict, Any, List, Optional
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent import AgentConfig, AgentRequest, AgentResponse, AgentContext
from app.services.duckdb_service import DuckDBService
from app.services.storage_service import StorageService


class GeospatialAgent(BaseAgent):
    """
    Geospatial Agent - handles location data and map visualizations

    Detects spatial columns, creates map configs, handles geographic queries
    Integrates with existing Kepler.gl map functionality
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.duckdb_service = DuckDBService()
        self.storage_service = StorageService()

    def can_handle(self, request: AgentRequest) -> float:
        """
        Calculate confidence for handling geospatial requests

        High confidence for queries like:
        - "Map customer locations"
        - "Show on a map"
        - "Find nearest..."
        - "Calculate distance"
        - "Geographic distribution"
        """
        return self.calculate_confidence(
            request.query,
            self.config.intent_keywords
        )

    async def process(self, request: AgentRequest, context: AgentContext) -> AgentResponse:
        """
        Process geospatial request

        Args:
            request: Agent request with spatial intent
            context: Execution context

        Returns:
            AgentResponse with map config and spatial analysis
        """
        try:
            self.logger.info(f"Processing geospatial query for dataset: {request.dataset_id}")

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

            # Detect spatial columns
            spatial_columns = self._detect_spatial_columns(schema_info)

            if not spatial_columns:
                return AgentResponse(
                    agent_name=self.config.name,
                    success=False,
                    data={},
                    error="No spatial columns detected. Need latitude/longitude or address columns."
                )

            # Determine spatial task
            task_type = self._determine_spatial_task(request.query)

            # Generate map configuration
            map_config = self._generate_map_config(
                spatial_columns=spatial_columns,
                task_type=task_type
            )

            # Sample data for preview
            sample_query = f"SELECT * FROM {table_name} LIMIT 100"
            sample_data_df = self.duckdb_service.execute_query(sample_query, dataset_id=dataset.id)
            sample_data = sample_data_df.to_dict('records')

            # Generate insights
            insights = self._generate_spatial_insights(
                table_name=table_name,
                spatial_columns=spatial_columns,
                schema=schema_info,
                dataset_id=dataset.id
            )

            response_data = {
                'summary': f"Detected {len(spatial_columns)} spatial column(s)",
                'spatial_columns': spatial_columns,
                'map_config': map_config,
                'task_type': task_type,
                'sample_data': sample_data[:50],
                'insights': insights,
                'type': 'geospatial'
            }

            response = AgentResponse(
                agent_name=self.config.name,
                success=True,
                data=response_data,
                metadata={
                    'spatial_columns': [c['name'] for c in spatial_columns],
                    'task_type': task_type,
                    'has_coordinates': any(c['type'] == 'coordinates' for c in spatial_columns)
                }
            )

            self.log_execution(request, response)
            return response

        except Exception as e:
            self.logger.error(f"Geospatial agent failed: {str(e)}", exc_info=True)

            error_response = AgentResponse(
                agent_name=self.config.name,
                success=False,
                data={},
                error=f"Geospatial analysis failed: {str(e)}"
            )

            self.log_execution(request, error_response)
            return error_response

    def _detect_spatial_columns(self, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect spatial columns (lat/lon, addresses, etc.)
        """
        columns = schema.get('columns', [])
        spatial_cols = []

        # Look for coordinate pairs
        lat_col = None
        lon_col = None

        for col in columns:
            col_name_lower = col['name'].lower()

            # Latitude detection
            if any(name in col_name_lower for name in ['lat', 'latitude', 'y_coord']):
                lat_col = col

            # Longitude detection
            if any(name in col_name_lower for name in ['lon', 'long', 'longitude', 'x_coord', 'lng']):
                lon_col = col

        # If we found a lat/lon pair
        if lat_col and lon_col:
            spatial_cols.append({
                'name': 'coordinates',
                'type': 'coordinates',
                'lat_column': lat_col['name'],
                'lon_column': lon_col['name']
            })

        # Look for address columns
        for col in columns:
            col_name_lower = col['name'].lower()
            if any(name in col_name_lower for name in ['address', 'location', 'city', 'country', 'zipcode', 'postal']):
                spatial_cols.append({
                    'name': col['name'],
                    'type': 'address',
                    'column': col['name']
                })

        return spatial_cols

    def _determine_spatial_task(self, query: str) -> str:
        """Determine what type of spatial analysis to perform"""
        query_lower = query.lower()

        if any(word in query_lower for word in ['map', 'visualize', 'show', 'plot']):
            return 'map_visualization'
        elif any(word in query_lower for word in ['distance', 'nearest', 'proximity', 'close']):
            return 'distance_analysis'
        elif any(word in query_lower for word in ['cluster', 'hotspot', 'concentration']):
            return 'spatial_clustering'
        elif any(word in query_lower for word in ['distribute', 'spread', 'geographic']):
            return 'distribution_analysis'
        else:
            return 'map_visualization'

    def _generate_map_config(
        self,
        spatial_columns: List[Dict[str, Any]],
        task_type: str
    ) -> Dict[str, Any]:
        """
        Generate Kepler.gl map configuration
        """
        # Get coordinate columns if available
        coord_col = next((c for c in spatial_columns if c['type'] == 'coordinates'), None)

        if not coord_col:
            return {
                'message': 'Address geocoding required',
                'requires_geocoding': True
            }

        config = {
            'version': 'v1',
            'config': {
                'visState': {
                    'layers': [
                        {
                            'type': 'point',
                            'config': {
                                'dataId': 'data',
                                'label': 'Points',
                                'columns': {
                                    'lat': coord_col['lat_column'],
                                    'lng': coord_col['lon_column']
                                },
                                'isVisible': True,
                                'visConfig': {
                                    'radius': 10,
                                    'opacity': 0.8,
                                    'colorRange': {
                                        'name': 'Global Warming',
                                        'type': 'sequential',
                                        'category': 'Uber'
                                    }
                                }
                            }
                        }
                    ]
                },
                'mapState': {
                    'latitude': 37.7749,
                    'longitude': -122.4194,
                    'zoom': 8
                }
            }
        }

        # Adjust config based on task type
        if task_type == 'spatial_clustering':
            config['config']['visState']['layers'][0]['type'] = 'hexagon'
            config['config']['visState']['layers'][0]['config']['visConfig']['radius'] = 1000

        return config

    def _generate_spatial_insights(
        self,
        table_name: str,
        spatial_columns: List[Dict[str, Any]],
        schema: Dict[str, Any],
        dataset_id: str
    ) -> List[str]:
        """Generate insights about spatial data"""
        insights = []

        # Get coordinate column
        coord_col = next((c for c in spatial_columns if c['type'] == 'coordinates'), None)

        if coord_col:
            # Count total points
            count_sql = f"SELECT COUNT(*) as total FROM {table_name}"
            result_df = self.duckdb_service.execute_query(count_sql, dataset_id=dataset_id)
            if not result_df.empty:
                total = result_df.iloc[0]['total']
                insights.append(f"Dataset contains {total:,} geographic points")

            # Check for null coordinates
            null_sql = f"""
            SELECT COUNT(*) as null_count
            FROM {table_name}
            WHERE {coord_col['lat_column']} IS NULL OR {coord_col['lon_column']} IS NULL
            """
            null_result_df = self.duckdb_service.execute_query(null_sql, dataset_id=dataset_id)
            if not null_result_df.empty and null_result_df.iloc[0]['null_count'] > 0:
                null_count = null_result_df.iloc[0]['null_count']
                insights.append(f"Warning: {null_count} records have missing coordinates")

            # Geographic bounds
            bounds_sql = f"""
            SELECT
                MIN({coord_col['lat_column']}) as min_lat,
                MAX({coord_col['lat_column']}) as max_lat,
                MIN({coord_col['lon_column']}) as min_lon,
                MAX({coord_col['lon_column']}) as max_lon
            FROM {table_name}
            WHERE {coord_col['lat_column']} IS NOT NULL
            """
            bounds_df = self.duckdb_service.execute_query(bounds_sql, dataset_id=dataset_id)
            if not bounds_df.empty:
                b = bounds_df.iloc[0]
                insights.append(
                    f"Geographic bounds: Lat [{b['min_lat']:.2f}, {b['max_lat']:.2f}], "
                    f"Lon [{b['min_lon']:.2f}, {b['max_lon']:.2f}]"
                )

        # Address columns
        address_cols = [c for c in spatial_columns if c['type'] == 'address']
        if address_cols:
            insights.append(f"Found {len(address_cols)} address/location column(s)")
            insights.append("Note: Geocoding may be required to display addresses on map")

        return insights
