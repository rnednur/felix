"""
Dashboard Editor Agent - interprets annotations and generates dashboard modifications
"""
from typing import Dict, Any, Optional
import json
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent import AgentConfig, AgentRequest, AgentResponse, AgentContext
from app.schemas.annotation import AnnotationRequest, DashboardEdit, IntentAnalysis, ContextCreateRequest
from app.services.agents.llm_service import LLMService


class DashboardEditorAgent(BaseAgent):
    """
    Dashboard Editor Agent - processes user annotations and generates edits

    Interprets natural language feedback on dashboard elements and generates
    structured modification instructions.
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.llm_service = LLMService()

    def can_handle(self, request: AgentRequest) -> float:
        """
        Calculate confidence for handling annotation/edit requests

        High confidence for queries like:
        - "Change this chart to..."
        - "Make this KPI show..."
        - "Update the colors..."
        - "Remove this element"
        """
        return self.calculate_confidence(
            request.query,
            self.config.intent_keywords
        )

    async def process(self, request: AgentRequest, context: AgentContext) -> AgentResponse:
        """
        Process annotation request and generate edit instructions

        Args:
            request: Agent request containing annotation data
            context: Execution context

        Returns:
            AgentResponse with DashboardEdit
        """
        try:
            self.logger.info(f"Processing annotation for dataset: {request.dataset_id}")

            # Extract annotation from context if available
            annotation_data = context.metadata.get('annotation')
            if not annotation_data:
                # Try to parse from query if it contains annotation format
                annotation_data = self._parse_annotation_from_query(request.query)

            if not annotation_data:
                raise ValueError("No annotation data found in request")

            # Analyze user intent
            intent = await self._analyze_intent(annotation_data)

            # Generate edit based on intent
            edit = await self._generate_edit(annotation_data, intent)

            response_data = {
                'summary': f"Generated {edit.action} edit for {annotation_data.get('element_type', 'element')}",
                'edit': edit.model_dump(),
                'intent': intent.model_dump(),
                'type': 'dashboard_edit'
            }

            response = AgentResponse(
                agent_name=self.config.name,
                success=True,
                data=response_data,
                metadata={
                    'element_id': edit.element_id,
                    'action': edit.action,
                    'intent_type': intent.intent_type,
                    'confidence': intent.confidence
                }
            )

            self.log_execution(request, response)
            return response

        except Exception as e:
            self.logger.error(f"Dashboard editor agent failed: {str(e)}", exc_info=True)

            error_response = AgentResponse(
                agent_name=self.config.name,
                success=False,
                data={},
                error=f"Failed to process annotation: {str(e)}"
            )

            self.log_execution(request, error_response)
            return error_response

    async def process_annotation(self, annotation: AnnotationRequest) -> DashboardEdit:
        """
        Process a direct annotation request (not via AgentRequest)

        This is the main entry point for the annotation API endpoint.

        Args:
            annotation: AnnotationRequest with element info and user feedback

        Returns:
            DashboardEdit with modification instructions
        """
        self.logger.info(f"[DashboardEditorAgent] process_annotation called")
        self.logger.info(f"[DashboardEditorAgent] Element type: {annotation.element_type}")
        self.logger.info(f"[DashboardEditorAgent] Element selector: {annotation.element_selector}")
        self.logger.info(f"[DashboardEditorAgent] Feedback: {annotation.feedback}")

        # Analyze user intent
        annotation_data = {
            'element_selector': annotation.element_selector,
            'element_type': annotation.element_type,
            'element_config': annotation.element_config,
            'feedback': annotation.feedback
        }

        self.logger.info(f"[DashboardEditorAgent] Analyzing intent...")
        intent = await self._analyze_intent(annotation_data)
        self.logger.info(f"[DashboardEditorAgent] Intent: {intent.intent_type} (confidence: {intent.confidence})")

        self.logger.info(f"[DashboardEditorAgent] Generating edit...")
        edit = await self._generate_edit(annotation_data, intent)
        self.logger.info(f"[DashboardEditorAgent] Edit generated: {edit.action} on {edit.element_id}")

        return edit

    async def create_from_context(self, request: ContextCreateRequest) -> DashboardEdit:
        """
        Create a new element using full dashboard context

        This method has access to all KPIs, charts, and dataset information,
        enabling it to create meaningful new elements that reference existing data.

        Args:
            request: ContextCreateRequest with feedback and dashboard context

        Returns:
            DashboardEdit with action='add' and new element configuration
        """
        import uuid

        self.logger.info(f"[DashboardEditorAgent] create_from_context called")
        self.logger.info(f"[DashboardEditorAgent] Feedback: {request.feedback}")
        self.logger.info(f"[DashboardEditorAgent] Context - KPIs: {len(request.context.kpis)}, Charts: {len(request.context.charts)}")

        new_element_id = str(uuid.uuid4())
        feedback = request.feedback.lower()

        # Determine what type of element to create
        # Maps are a special type of chart
        if any(word in feedback for word in ['map', 'geospatial', 'geographic', 'choropleth', 'states', 'countries']):
            return await self._create_chart_from_context(new_element_id, request)
        elif any(word in feedback for word in ['chart', 'bar', 'line', 'pie', 'graph', 'plot', 'visual']):
            return await self._create_chart_from_context(new_element_id, request)
        elif any(word in feedback for word in ['kpi', 'metric', 'card', 'number', 'total', 'average']):
            return await self._create_kpi_from_context(new_element_id, request)
        elif any(word in feedback for word in ['insight', 'summary', 'note', 'analysis', 'takeaway']):
            return await self._create_insight_from_context(new_element_id, request)
        else:
            # Default to chart if KPIs are available, otherwise insight
            if request.context.kpis:
                return await self._create_chart_from_context(new_element_id, request)
            else:
                return await self._create_insight_from_context(new_element_id, request)

    async def _create_chart_from_context(
        self,
        new_element_id: str,
        request: ContextCreateRequest
    ) -> DashboardEdit:
        """Create a chart using all available KPIs and data"""
        context = request.context
        feedback_lower = request.feedback.lower()

        # Check if this is a map/geospatial request
        is_map_request = any(word in feedback_lower for word in [
            'map', 'geospatial', 'geographic', 'choropleth', 'states', 'countries', 'regions'
        ])

        # Prepare KPI data for the prompt
        kpi_data = []
        for kpi in context.kpis:
            kpi_data.append({
                "name": kpi.name,
                "value": kpi.value,
                "formattedValue": kpi.formatted_value,
                "trend": kpi.trend,
                "trendDirection": kpi.trend_direction
            })

        # Prepare chart summaries with data for maps
        chart_summaries = []
        chart_data_for_maps = []
        for chart in context.charts:
            chart_summaries.append({
                "type": chart.chart_type,
                "title": chart.title,
                "dataPoints": len(chart.data)
            })
            # Collect chart data for map creation (often has aggregated state/region data)
            if chart.data and is_map_request:
                chart_data_for_maps.extend(chart.data)

        # For maps, use ALL available data (not just 5 rows)
        # Priority: 1) sample_data (from tables), 2) chart data (aggregated)
        if is_map_request:
            all_data = context.sample_data if context.sample_data else chart_data_for_maps
            data_for_prompt = all_data  # Use ALL data for maps
            self.logger.info(f"[DashboardEditorAgent] Map request detected, using {len(data_for_prompt)} data rows")
        else:
            data_for_prompt = context.sample_data[:10] if context.sample_data else []

        # Build appropriate prompt based on request type
        if is_map_request:
            prompt = self._build_map_prompt(kpi_data, chart_summaries, context.columns, data_for_prompt, request.feedback)
        else:
            prompt = f"""Create a Vega-Lite chart based on this dashboard data and user request.

AVAILABLE KPIs ({len(kpi_data)} total):
{json.dumps(kpi_data, indent=2)}

EXISTING CHARTS ({len(chart_summaries)} total):
{json.dumps(chart_summaries, indent=2)}

AVAILABLE COLUMNS: {context.columns if context.columns else 'Not specified'}

SAMPLE DATA (if available):
{json.dumps(data_for_prompt[:10] if data_for_prompt else [], indent=2)}

USER REQUEST: "{request.feedback}"

Create a Vega-Lite chart that best represents the user's request. If the user wants to compare KPIs, create a bar chart with KPI names on one axis and values on the other.

Return a JSON object:
{{
    "chartType": "<bar/line/pie/area>",
    "title": "<descriptive title>",
    "vegaSpec": {{
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "data": {{"values": [... data for the chart ...]}},
        "mark": "<bar/line/arc/area>",
        "encoding": {{ ... appropriate encodings ... }}
    }}
}}

For comparing KPIs, use this data structure:
"data": {{"values": [
    {{"name": "KPI Name 1", "value": 123}},
    {{"name": "KPI Name 2", "value": 456}}
]}}

Return ONLY the JSON object."""

        try:
            # Use higher token limit for maps since they include all data rows
            max_tokens = 8000 if is_map_request else 2000

            response = await self.llm_service.generate(
                prompt=prompt,
                response_format="json",
                temperature=0.3,
                max_tokens=max_tokens
            )

            chart_config = json.loads(response)
            self.logger.info(f"[DashboardEditorAgent] Created chart from context: {chart_config.get('title', 'Untitled')}")

            return DashboardEdit(
                element_id=new_element_id,
                action='add',
                changes={
                    'type': 'chart',
                    'content': {
                        'chartType': chart_config.get('chartType', 'bar'),
                        'title': chart_config.get('title', 'New Chart'),
                        'vegaSpec': chart_config.get('vegaSpec', {}),
                        'data': chart_config.get('vegaSpec', {}).get('data', {}).get('values', [])
                    }
                },
                reasoning=f"Created chart from dashboard context: {request.feedback[:100]}"
            )

        except Exception as e:
            self.logger.error(f"Failed to create chart from context: {e}")
            # Fallback: Create a simple bar chart from KPIs
            kpi_values = [{"name": kpi.name, "value": kpi.value or 0} for kpi in context.kpis]

            return DashboardEdit(
                element_id=new_element_id,
                action='add',
                changes={
                    'type': 'chart',
                    'content': {
                        'chartType': 'bar',
                        'title': 'KPI Comparison',
                        'vegaSpec': {
                            '$schema': 'https://vega.github.io/schema/vega-lite/v5.json',
                            'data': {'values': kpi_values},
                            'mark': 'bar',
                            'encoding': {
                                'x': {'field': 'value', 'type': 'quantitative'},
                                'y': {'field': 'name', 'type': 'nominal', 'sort': '-x'}
                            }
                        },
                        'data': kpi_values
                    }
                },
                reasoning=f"Created fallback KPI comparison chart (LLM failed: {str(e)})"
            )

    def _build_map_prompt(
        self,
        kpi_data: list,
        chart_summaries: list,
        columns: list,
        all_data: list,
        feedback: str
    ) -> str:
        """Build a specialized prompt for map/geospatial chart creation"""
        feedback_lower = feedback.lower()

        # Detect geographic level from keywords (order matters - more specific first)
        # US Counties
        is_us_counties = any(word in feedback_lower for word in [
            'county', 'counties', 'fips'
        ])
        # Canadian regions
        is_canada_map = any(word in feedback_lower for word in [
            'canada', 'canadian', 'cma', 'census metropolitan', 'province', 'provinces'
        ])
        is_canada_provinces = any(word in feedback_lower for word in [
            'province', 'provinces'
        ]) and is_canada_map
        # European regions
        is_europe_map = any(word in feedback_lower for word in [
            'europe', 'european', 'eu '
        ])
        # World/Countries
        is_world_map = any(word in feedback_lower for word in [
            'country', 'countries', 'world', 'global', 'nation', 'international'
        ])
        # US States
        is_us_states = any(word in feedback_lower for word in [
            'state', 'states', 'us ', 'usa', 'united states', 'america'
        ]) and not is_us_counties and not is_world_map

        # Detect geographic and value fields in data
        geo_field = None
        value_field = None

        if all_data and len(all_data) > 0:
            first_row = all_data[0]

            # Field candidates by geographic level
            county_candidates = ['county', 'county_name', 'countyname', 'fips', 'fips_code',
                               'county_fips', 'geoid']
            country_candidates = ['country', 'country_name', 'countryname', 'nation', 'location',
                                 'geo', 'geography', 'territory', 'iso', 'iso3', 'iso_code']
            state_candidates = ['state', 'statename', 'state_name', 'locationdesc',
                              'locationabbr', 'state_abbr']
            province_candidates = ['province', 'province_name', 'prov', 'territory',
                                  'cma', 'cma_name', 'region']
            # Value field candidates
            value_candidates = ['value', 'datavalue', 'data_value', 'total', 'count', 'amount',
                              'datavalue_total', 'sum', 'avg', 'average', 'casualties',
                              'deaths', 'injured', 'affected', 'damage', 'loss', 'population',
                              'rate', 'percent', 'percentage', 'income', 'gdp', 'sales']

            for key in first_row.keys():
                key_lower = key.lower()
                # Check for geographic fields based on detected map type
                if is_us_counties:
                    if any(c in key_lower for c in county_candidates):
                        geo_field = key
                elif is_canada_map:
                    if any(p in key_lower for p in province_candidates):
                        geo_field = key
                elif is_world_map or is_europe_map:
                    if any(c in key_lower for c in country_candidates):
                        geo_field = key
                elif is_us_states:
                    if any(s in key_lower for s in state_candidates):
                        geo_field = key
                # Fallback: check all geographic candidates
                if not geo_field:
                    all_geo = county_candidates + country_candidates + state_candidates + province_candidates
                    if any(g in key_lower for g in all_geo):
                        geo_field = key
                # Check for value fields
                if any(v in key_lower for v in value_candidates):
                    value_field = key

        # Determine map type and configuration
        # Available TopoJSON sources:
        # - World: https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json
        # - US States: https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json
        # - US Counties: https://cdn.jsdelivr.net/npm/us-atlas@3/counties-10m.json
        # - Canada Provinces: https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/canada.geojson
        # - Europe: https://raw.githubusercontent.com/leakyMirror/map-of-europe/master/TopoJSON/europe.topojson

        if is_us_counties:
            map_type = "us_counties"
            topojson_url = "https://cdn.jsdelivr.net/npm/us-atlas@3/counties-10m.json"
            topojson_feature = "counties"
            projection = "albersUsa"
            geo_property = "id"  # FIPS code for counties
            geo_label = "County"
            lookup_note = "Counties use FIPS codes (5-digit: 2-digit state + 3-digit county). The 'id' field contains the FIPS code."
        elif is_canada_provinces:
            map_type = "canada_provinces"
            topojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/canada.geojson"
            topojson_feature = None  # GeoJSON, not TopoJSON
            projection = "conicConformal"
            geo_property = "properties.name"
            geo_label = "Province"
            lookup_note = "Use full province names (e.g., 'Ontario', 'British Columbia')."
        elif is_canada_map:
            # CMA or general Canada - use provinces as fallback
            map_type = "canada_provinces"
            topojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/canada.geojson"
            topojson_feature = None
            projection = "conicConformal"
            geo_property = "properties.name"
            geo_label = "Province/CMA"
            lookup_note = "For CMAs, you may need to aggregate to province level or provide custom GeoJSON."
        elif is_europe_map:
            map_type = "europe"
            topojson_url = "https://raw.githubusercontent.com/leakyMirror/map-of-europe/master/TopoJSON/europe.topojson"
            topojson_feature = "europe"
            projection = "conicConformal"
            geo_property = "properties.NAME"
            geo_label = "Country"
            lookup_note = "Use English country names (e.g., 'Germany', 'France')."
        elif is_world_map or (not is_us_states and not geo_field):
            map_type = "world"
            topojson_url = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json"
            topojson_feature = "countries"
            projection = "equalEarth"
            geo_property = "properties.name"
            geo_label = "Country"
            lookup_note = "Use Natural Earth naming: 'United States of America' (not 'USA'), 'United Kingdom' (not 'UK')."
        else:
            map_type = "us_states"
            topojson_url = "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json"
            topojson_feature = "states"
            projection = "albersUsa"
            geo_property = "properties.name"
            geo_label = "State"
            lookup_note = "Use full state names (e.g., 'California', not 'CA')."

        self.logger.info(f"[DashboardEditorAgent] Map prompt - type: {map_type}, geo_field: {geo_field}, value_field: {value_field}")
        self.logger.info(f"[DashboardEditorAgent] Map prompt - total data rows: {len(all_data)}")

        # Build format specification based on map type
        if topojson_feature:
            data_format = f'{{"type": "topojson", "feature": "{topojson_feature}"}}'
        else:
            data_format = '{"type": "json", "property": "features"}'  # GeoJSON format

        # Map type descriptions
        map_type_descriptions = {
            "world": "WORLD/COUNTRIES",
            "us_states": "US STATES",
            "us_counties": "US COUNTIES",
            "canada_provinces": "CANADIAN PROVINCES",
            "europe": "EUROPEAN COUNTRIES"
        }
        map_description = map_type_descriptions.get(map_type, map_type.upper())

        return f"""Create a Vega-Lite GEOSPATIAL CHOROPLETH MAP based on this data.

IMPORTANT: This is a {map_description} MAP request.

AVAILABLE DATA ({len(all_data)} rows total):
{json.dumps(all_data, indent=2)}

DETECTED FIELDS:
- Geographic field: {geo_field or 'Not detected - check data keys'}
- Value field for coloring: {value_field or 'Not detected - check data keys'}

AVAILABLE COLUMNS: {columns if columns else list(all_data[0].keys()) if all_data else 'None'}

USER REQUEST: "{feedback}"

MAP CONFIGURATION:
- Map Type: {map_description}
- Geographic Data URL: {topojson_url}
- Feature: {topojson_feature or 'GeoJSON features'}
- Projection: {projection}
- Geographic Property for lookup: {geo_property}
- LOOKUP NOTE: {lookup_note}

Create a Vega-Lite choropleth map specification. You MUST:
1. Use the geographic data from: "{topojson_url}"
2. Include ALL {len(all_data)} data rows in the lookup transform
3. Use the correct geographic field to join with "{geo_property}"
4. Color-code regions based on the value field

Return a JSON object:
{{
    "chartType": "map",
    "title": "<descriptive title for the map>",
    "vegaSpec": {{
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "width": 800,
        "height": 500,
        "data": {{
            "url": "{topojson_url}",
            "format": {data_format}
        }},
        "transform": [{{
            "lookup": "{geo_property}",
            "from": {{
                "data": {{"values": [... ALL {len(all_data)} rows ...]}},
                "key": "<your geographic field that matches {geo_property}>",
                "fields": ["<value field for coloring>"]
            }}
        }}],
        "projection": {{"type": "{projection}"}},
        "mark": {{"type": "geoshape", "stroke": "white", "strokeWidth": 0.5}},
        "encoding": {{
            "color": {{
                "field": "<value field>",
                "type": "quantitative",
                "scale": {{"scheme": "reds"}},
                "legend": {{"title": "<value description>"}}
            }},
            "tooltip": [
                {{"field": "{geo_property}", "type": "nominal", "title": "{geo_label}"}},
                {{"field": "<value field>", "type": "quantitative", "title": "Value", "format": ",.0f"}}
            ]
        }}
    }}
}}

CRITICAL NOTES:
- {lookup_note}
- Include ALL data rows in the values array, not just a sample
- The lookup key field in your data must match the format expected by {geo_property}

COMMON NAME MAPPINGS:
- World: "USA" -> "United States of America", "UK" -> "United Kingdom", "Russia" -> "Russian Federation"
- US Counties: Use 5-digit FIPS codes (e.g., "06037" for Los Angeles County)
- Canada: Use full province names (e.g., "Ontario", "Quebec", "British Columbia")

Return ONLY the JSON object."""

    async def _create_kpi_from_context(
        self,
        new_element_id: str,
        request: ContextCreateRequest
    ) -> DashboardEdit:
        """Create a KPI using dashboard context"""
        context = request.context

        # Prepare existing KPIs for reference
        existing_kpis = [{"name": kpi.name, "value": kpi.value} for kpi in context.kpis]

        prompt = f"""Create a new KPI card based on this dashboard context and user request.

EXISTING KPIs:
{json.dumps(existing_kpis, indent=2)}

SAMPLE DATA:
{json.dumps(context.sample_data[:10] if context.sample_data else [], indent=2)}

AVAILABLE COLUMNS: {context.columns if context.columns else 'Not specified'}

USER REQUEST: "{request.feedback}"

Create a meaningful KPI. If the user asks for a calculated metric (like average, total, etc.), calculate it from the data if possible.

Return a JSON object:
{{
    "name": "<KPI name>",
    "value": <numeric value>,
    "formattedValue": "<formatted string like '$1.2M' or '85%'>",
    "trend": <percentage change, or null>,
    "trendDirection": "<up/down/flat or null>",
    "comparisonLabel": "<e.g., 'vs last month' or null>"
}}

Return ONLY the JSON object."""

        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                response_format="json",
                temperature=0.3,
                max_tokens=500
            )

            kpi_config = json.loads(response)
            self.logger.info(f"[DashboardEditorAgent] Created KPI from context: {kpi_config.get('name', 'Untitled')}")

            return DashboardEdit(
                element_id=new_element_id,
                action='add',
                changes={
                    'type': 'kpi-card',
                    'content': {
                        'id': new_element_id,
                        'name': kpi_config.get('name', 'New KPI'),
                        'value': kpi_config.get('value', 0),
                        'formattedValue': kpi_config.get('formattedValue', '0'),
                        'trend': kpi_config.get('trend'),
                        'trendDirection': kpi_config.get('trendDirection', 'flat'),
                        'comparisonLabel': kpi_config.get('comparisonLabel', '')
                    }
                },
                reasoning=f"Created KPI from dashboard context: {request.feedback[:100]}"
            )

        except Exception as e:
            self.logger.error(f"Failed to create KPI from context: {e}")
            return DashboardEdit(
                element_id=new_element_id,
                action='add',
                changes={
                    'type': 'kpi-card',
                    'content': {
                        'id': new_element_id,
                        'name': 'New Metric',
                        'value': 0,
                        'formattedValue': '0',
                        'trendDirection': 'flat'
                    }
                },
                reasoning=f"Created placeholder KPI (LLM failed: {str(e)})"
            )

    async def _create_insight_from_context(
        self,
        new_element_id: str,
        request: ContextCreateRequest
    ) -> DashboardEdit:
        """Create an insight summarizing dashboard data"""
        context = request.context

        # Prepare KPI summaries
        kpi_summaries = [
            f"- {kpi.name}: {kpi.formatted_value}" +
            (f" ({kpi.trend_direction} {kpi.trend}%)" if kpi.trend else "")
            for kpi in context.kpis
        ]

        # Prepare chart summaries
        chart_summaries = [
            f"- {chart.title or 'Untitled'} ({chart.chart_type} chart)"
            for chart in context.charts
        ]

        prompt = f"""Create an insight note summarizing this dashboard data.

DASHBOARD KPIs:
{chr(10).join(kpi_summaries) if kpi_summaries else 'No KPIs available'}

DASHBOARD CHARTS:
{chr(10).join(chart_summaries) if chart_summaries else 'No charts available'}

USER REQUEST: "{request.feedback}"

Generate insightful markdown content that summarizes the data and provides actionable takeaways.

Return a JSON object:
{{
    "content": "<markdown content with bullet points and key insights>"
}}

Guidelines:
- Highlight key metrics and their significance
- Note any trends (up/down) and what they might mean
- Keep it concise but informative
- Use bullet points for clarity

Return ONLY the JSON object."""

        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                response_format="json",
                temperature=0.4,
                max_tokens=1000
            )

            insight_config = json.loads(response)
            self.logger.info(f"[DashboardEditorAgent] Created insight from context")

            return DashboardEdit(
                element_id=new_element_id,
                action='add',
                changes={
                    'type': 'insight-note',
                    'content': {
                        'content': insight_config.get('content', 'Dashboard summary'),
                        'aiGenerated': True,
                        'tags': ['ai-generated', 'dashboard-summary']
                    }
                },
                reasoning=f"Created insight from dashboard context: {request.feedback[:100]}"
            )

        except Exception as e:
            self.logger.error(f"Failed to create insight from context: {e}")
            # Fallback: Create basic summary
            summary_lines = ["## Dashboard Summary\n"]
            if context.kpis:
                summary_lines.append("### Key Metrics")
                for kpi in context.kpis[:5]:
                    summary_lines.append(f"- **{kpi.name}**: {kpi.formatted_value}")

            return DashboardEdit(
                element_id=new_element_id,
                action='add',
                changes={
                    'type': 'insight-note',
                    'content': {
                        'content': '\n'.join(summary_lines),
                        'aiGenerated': True,
                        'tags': ['ai-generated']
                    }
                },
                reasoning=f"Created fallback insight (LLM failed: {str(e)})"
            )

    def _parse_annotation_from_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Try to parse annotation data from a query string

        This handles cases where annotation data is embedded in the query
        (e.g., from copy/paste workflow)
        """
        # Look for common annotation patterns
        if '[data-felix-id=' in query or 'element:' in query.lower():
            # Try to extract structured data
            # This is a fallback for non-standard input
            return {
                'element_selector': 'unknown',
                'element_type': 'unknown',
                'element_config': {},
                'feedback': query
            }
        return None

    async def _analyze_intent(self, annotation_data: Dict[str, Any]) -> IntentAnalysis:
        """
        Use LLM to analyze the user's intent from their feedback

        Returns structured intent analysis
        """
        element_type = annotation_data.get('element_type', 'unknown')
        element_config = annotation_data.get('element_config', {})
        feedback = annotation_data.get('feedback', '')

        prompt = f"""Analyze this dashboard edit request and identify the user's intent.

Element Type: {element_type}
Current Configuration: {json.dumps(element_config, indent=2)}
User Feedback: "{feedback}"

Classify the intent into one of these categories:
- change_chart_type: User wants to change the visualization type (e.g., bar to line chart)
- modify_styling: User wants to change colors, fonts, sizes, or visual appearance
- update_data: User wants to change the data being displayed (filters, aggregations, etc.)
- reword_insight: User wants to change text content (for insights/notes)
- remove_element: User wants to remove this element from the dashboard
- resize_element: User wants to make the element larger or smaller
- reposition_element: User wants to move the element
- add_element: User wants to ADD/CREATE a NEW element based on or related to this one (e.g., "add a pie chart", "create a KPI", "add an insight")

Return a JSON object with:
{{
    "intent_type": "<one of the categories above>",
    "target_element": "<element type>",
    "specific_changes": {{
        // Specific changes the user wants, based on their feedback
        // For chart changes: "new_chart_type": "line", etc.
        // For styling: "colors": [...], "font_size": 14, etc.
        // For data: "filter": {{...}}, "aggregation": "avg", etc.
        // For text: "new_content": "...", etc.
    }},
    "confidence": <0.0 to 1.0>
}}

Respond ONLY with the JSON object, no explanation."""

        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                response_format="json",
                temperature=0.2,
                max_tokens=500
            )

            result = json.loads(response)
            return IntentAnalysis(
                intent_type=result.get('intent_type', 'unknown'),
                target_element=result.get('target_element', element_type),
                specific_changes=result.get('specific_changes', {}),
                confidence=result.get('confidence', 0.5)
            )

        except Exception as e:
            self.logger.warning(f"Intent analysis failed, using fallback: {e}")
            # Fallback to simple keyword matching
            return self._fallback_intent_analysis(feedback, element_type)

    def _fallback_intent_analysis(self, feedback: str, element_type: str) -> IntentAnalysis:
        """
        Fallback intent analysis using keyword matching
        """
        feedback_lower = feedback.lower()

        # Check for chart type changes
        chart_types = ['bar', 'line', 'pie', 'scatter', 'area', 'histogram']
        for chart_type in chart_types:
            if chart_type in feedback_lower:
                return IntentAnalysis(
                    intent_type='change_chart_type',
                    target_element=element_type,
                    specific_changes={'new_chart_type': chart_type},
                    confidence=0.7
                )

        # Check for removal intent
        if any(word in feedback_lower for word in ['remove', 'delete', 'hide']):
            return IntentAnalysis(
                intent_type='remove_element',
                target_element=element_type,
                specific_changes={},
                confidence=0.8
            )

        # Check for styling intent
        if any(word in feedback_lower for word in ['color', 'style', 'font', 'size', 'bigger', 'smaller']):
            return IntentAnalysis(
                intent_type='modify_styling',
                target_element=element_type,
                specific_changes={'requested': feedback},
                confidence=0.6
            )

        # Check for text changes (for insights)
        if any(word in feedback_lower for word in ['reword', 'change text', 'update text', 'say']):
            return IntentAnalysis(
                intent_type='reword_insight',
                target_element=element_type,
                specific_changes={'requested': feedback},
                confidence=0.6
            )

        # Check for add/create intent
        if any(word in feedback_lower for word in ['add', 'create', 'new', 'also show', 'include']):
            # Determine what type of element to add
            new_element_type = 'chart'  # default
            if 'kpi' in feedback_lower or 'metric' in feedback_lower:
                new_element_type = 'kpi'
            elif 'insight' in feedback_lower or 'summary' in feedback_lower or 'note' in feedback_lower:
                new_element_type = 'insight'
            elif 'pie' in feedback_lower:
                new_element_type = 'pie_chart'
            elif 'line' in feedback_lower:
                new_element_type = 'line_chart'
            elif 'bar' in feedback_lower:
                new_element_type = 'bar_chart'
            elif 'table' in feedback_lower:
                new_element_type = 'table'

            return IntentAnalysis(
                intent_type='add_element',
                target_element=new_element_type,
                specific_changes={'requested': feedback, 'source_element': element_type},
                confidence=0.7
            )

        # Default to modify styling
        return IntentAnalysis(
            intent_type='modify_styling',
            target_element=element_type,
            specific_changes={'requested': feedback},
            confidence=0.3
        )

    async def _generate_edit(
        self,
        annotation_data: Dict[str, Any],
        intent: IntentAnalysis
    ) -> DashboardEdit:
        """
        Generate specific edit instructions based on intent analysis
        """
        element_selector = annotation_data.get('element_selector', '')
        element_type = annotation_data.get('element_type', 'unknown')
        element_config = annotation_data.get('element_config', {})
        feedback = annotation_data.get('feedback', '')

        # Extract element ID from selector
        element_id = self._extract_element_id(element_selector, element_config)

        # Handle removal
        if intent.intent_type == 'remove_element':
            return DashboardEdit(
                element_id=element_id,
                action='remove',
                changes={},
                reasoning=f"User requested to remove this {element_type} element"
            )

        # Handle adding new elements
        if intent.intent_type == 'add_element':
            return await self._generate_new_element(element_id, element_type, element_config, feedback, intent)

        # Handle resizing elements
        if intent.intent_type == 'resize_element':
            return self._generate_resize_edit(element_id, element_type, feedback, intent)

        # Use specialized handlers for different element types
        if element_type == 'chart':
            return await self._generate_chart_edit(element_id, element_config, feedback, intent)
        elif element_type == 'kpi':
            return await self._generate_kpi_edit(element_id, element_config, feedback, intent)
        elif element_type == 'insight':
            return await self._generate_insight_edit(element_id, element_config, feedback, intent)
        else:
            return await self._generate_generic_edit(element_id, element_type, element_config, feedback, intent)

    def _generate_resize_edit(
        self,
        element_id: str,
        element_type: str,
        feedback: str,
        intent: IntentAnalysis
    ) -> DashboardEdit:
        """
        Generate resize edit based on user feedback

        Maps natural language size requests to displaySize values:
        - small: "smaller", "compact", "mini"
        - medium: "medium", "normal", "default"
        - large: "larger", "bigger", "expand", "2 columns"
        - full: "full width", "full", "maximize", "entire width", "all columns"
        """
        feedback_lower = feedback.lower()

        # Determine target size from feedback
        if any(word in feedback_lower for word in ['full width', 'full', 'maximize', 'entire width', 'all columns', 'whole width']):
            new_size = 'full'
            size_description = 'full width'
        elif any(word in feedback_lower for word in ['larger', 'bigger', 'expand', '2 column', 'two column', 'double']):
            new_size = 'large'
            size_description = 'large (2 columns)'
        elif any(word in feedback_lower for word in ['smaller', 'compact', 'mini', 'reduce', 'shrink']):
            new_size = 'small'
            size_description = 'small (1 column)'
        elif any(word in feedback_lower for word in ['medium', 'normal', 'default', 'reset']):
            new_size = 'medium'
            size_description = 'medium (default)'
        else:
            # Default to large if just "make bigger" or similar
            new_size = 'large'
            size_description = 'large (2 columns)'

        self.logger.info(f"[DashboardEditorAgent] Resize request: '{feedback}' -> {new_size}")

        return DashboardEdit(
            element_id=element_id,
            action='modify',
            changes={
                'displaySize': new_size
            },
            reasoning=f"Resized {element_type} to {size_description} based on request: {feedback}"
        )

    async def _generate_chart_edit(
        self,
        element_id: str,
        element_config: Dict[str, Any],
        feedback: str,
        intent: IntentAnalysis
    ) -> DashboardEdit:
        """
        Generate chart-specific edits with full Vega-Lite spec modification
        """
        self.logger.info(f"[DashboardEditorAgent] Generating chart edit with Vega spec")

        # Extract current Vega spec if available
        current_vega_spec = element_config.get('vegaSpec', element_config.get('spec', {}))
        chart_type = element_config.get('chartType', 'bar')
        title = element_config.get('title', '')

        prompt = f"""You are a Vega-Lite expert. Modify this chart based on the user's request.

CURRENT CHART:
- Type: {chart_type}
- Title: {title}
- Vega-Lite Spec: {json.dumps(current_vega_spec, indent=2)}

USER REQUEST: "{feedback}"

ANALYZED INTENT: {intent.intent_type}

Generate the MODIFIED Vega-Lite spec that fulfills the user's request. Return a JSON object with:
{{
    "vegaSpec": {{ ... the complete modified Vega-Lite spec ... }},
    "chartType": "<new chart type if changed, e.g., bar, line, pie, area, point>",
    "title": "<new title if changed>"
}}

IMPORTANT GUIDELINES:
1. For chart type changes: Update the "mark" property (use "bar", "line", "area", "point", "arc" for pie)
2. For sorting: Add "sort" to the categorical axis encoding (use "-x" or "-y" for descending)
3. For colors: Add "color" encoding or update mark properties
4. For pie charts: Use "arc" mark with "theta" encoding for values and "color" for categories
5. Preserve the existing data and basic structure
6. Only include fields that are changing

EXAMPLE - Change bar to line chart:
{{"vegaSpec": {{"mark": "line", ...rest of spec}}, "chartType": "line"}}

EXAMPLE - Sort descending:
{{"vegaSpec": {{"encoding": {{"y": {{"sort": "-x", ...}}}}, ...}}, "chartType": "{chart_type}"}}

EXAMPLE - Change color to blue:
{{"vegaSpec": {{"mark": {{"type": "{chart_type}", "color": "#3b82f6"}}, ...}}, "chartType": "{chart_type}"}}

Return ONLY the JSON object, no explanation."""

        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                response_format="json",
                temperature=0.2,
                max_tokens=2000  # Larger for full spec
            )

            changes = json.loads(response)
            self.logger.info(f"[DashboardEditorAgent] Chart changes generated: {list(changes.keys())}")

            return DashboardEdit(
                element_id=element_id,
                action='modify',
                changes=changes,
                reasoning=f"Modified chart based on: {feedback[:100]}"
            )

        except Exception as e:
            self.logger.warning(f"Chart edit generation failed: {e}")
            # Fallback to simple changes
            return self._fallback_chart_edit(element_id, feedback, intent)

    def _fallback_chart_edit(
        self,
        element_id: str,
        feedback: str,
        intent: IntentAnalysis
    ) -> DashboardEdit:
        """Fallback chart edit using keyword matching"""
        feedback_lower = feedback.lower()
        changes = {}

        # Chart type changes
        chart_type_map = {
            'line': 'line',
            'bar': 'bar',
            'pie': 'arc',
            'area': 'area',
            'scatter': 'point',
            'point': 'point',
            'donut': 'arc',
        }
        for keyword, mark_type in chart_type_map.items():
            if keyword in feedback_lower:
                changes['chartType'] = keyword
                changes['vegaSpec'] = {'mark': mark_type if mark_type != 'arc' else {'type': 'arc', 'innerRadius': 50 if 'donut' in feedback_lower else 0}}
                break

        # Sorting
        if 'descending' in feedback_lower or 'desc' in feedback_lower:
            changes['sortOrder'] = 'descending'
        elif 'ascending' in feedback_lower or 'asc' in feedback_lower:
            changes['sortOrder'] = 'ascending'

        # Colors
        color_map = {
            'blue': '#3b82f6',
            'red': '#ef4444',
            'green': '#22c55e',
            'purple': '#a855f7',
            'orange': '#f97316',
            'yellow': '#eab308',
            'pink': '#ec4899',
            'teal': '#14b8a6',
            'indigo': '#6366f1',
        }
        for color_name, hex_value in color_map.items():
            if color_name in feedback_lower:
                changes['color'] = hex_value
                break

        return DashboardEdit(
            element_id=element_id,
            action='modify',
            changes=changes,
            reasoning=f"Fallback chart edit for: {feedback[:50]}"
        )

    async def _generate_kpi_edit(
        self,
        element_id: str,
        element_config: Dict[str, Any],
        feedback: str,
        intent: IntentAnalysis
    ) -> DashboardEdit:
        """Generate KPI-specific edits"""
        current_name = element_config.get('name', '')
        current_value = element_config.get('formattedValue', element_config.get('value', ''))

        prompt = f"""Modify this KPI card based on the user's request.

CURRENT KPI:
- Name: {current_name}
- Value: {current_value}
- Full config: {json.dumps(element_config, indent=2)}

USER REQUEST: "{feedback}"

Generate a JSON object with the changes to apply:
{{
    "name": "<new name if changing>",
    "formattedValue": "<new formatted value if changing>",
    "trendDirection": "<up/down/flat if changing>",
    "comparisonLabel": "<new comparison text if changing>"
}}

Only include fields that need to change. Return ONLY the JSON object."""

        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                response_format="json",
                temperature=0.3,
                max_tokens=500
            )

            changes = json.loads(response)

            return DashboardEdit(
                element_id=element_id,
                action='modify',
                changes=changes,
                reasoning=f"Modified KPI based on: {feedback[:100]}"
            )

        except Exception as e:
            self.logger.warning(f"KPI edit generation failed: {e}")
            return DashboardEdit(
                element_id=element_id,
                action='modify',
                changes=intent.specific_changes,
                reasoning=f"Fallback KPI edit: {str(e)}"
            )

    async def _generate_insight_edit(
        self,
        element_id: str,
        element_config: Dict[str, Any],
        feedback: str,
        intent: IntentAnalysis
    ) -> DashboardEdit:
        """Generate insight/note-specific edits"""
        current_content = element_config.get('content', '')

        prompt = f"""Modify this insight/note based on the user's request.

CURRENT CONTENT:
{current_content}

USER REQUEST: "{feedback}"

Generate the new content as markdown. Return a JSON object:
{{
    "content": "<new markdown content>"
}}

Guidelines:
- If user wants it shorter, make it concise
- If user wants bullet points, use markdown lists
- If user wants more detail, expand on the current content
- Keep the core message unless user wants something completely different

Return ONLY the JSON object."""

        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                response_format="json",
                temperature=0.4,
                max_tokens=1000
            )

            changes = json.loads(response)

            return DashboardEdit(
                element_id=element_id,
                action='modify',
                changes=changes,
                reasoning=f"Modified insight based on: {feedback[:100]}"
            )

        except Exception as e:
            self.logger.warning(f"Insight edit generation failed: {e}")
            return DashboardEdit(
                element_id=element_id,
                action='modify',
                changes={'content': feedback},  # Use feedback as new content
                reasoning=f"Fallback insight edit: {str(e)}"
            )

    async def _generate_generic_edit(
        self,
        element_id: str,
        element_type: str,
        element_config: Dict[str, Any],
        feedback: str,
        intent: IntentAnalysis
    ) -> DashboardEdit:
        """Generate edits for other element types"""
        prompt = f"""Generate changes for this dashboard element based on the user's request.

Element Type: {element_type}
Current Configuration: {json.dumps(element_config, indent=2)}
User Request: "{feedback}"
Intent: {intent.intent_type}

Generate a JSON object with the specific property changes to apply.
Return ONLY the JSON object, no explanation."""

        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                response_format="json",
                temperature=0.3,
                max_tokens=500
            )

            changes = json.loads(response)

            return DashboardEdit(
                element_id=element_id,
                action='modify',
                changes=changes,
                reasoning=f"Applied {intent.intent_type} based on: {feedback[:100]}"
            )

        except Exception as e:
            self.logger.warning(f"Generic edit generation failed: {e}")
            return DashboardEdit(
                element_id=element_id,
                action='modify',
                changes=intent.specific_changes,
                reasoning=f"Fallback edit for {intent.intent_type}: {str(e)}"
            )

    async def _generate_new_element(
        self,
        source_element_id: str,
        source_element_type: str,
        source_element_config: Dict[str, Any],
        feedback: str,
        intent: IntentAnalysis
    ) -> DashboardEdit:
        """Generate a new element based on an existing element"""
        import uuid

        new_element_id = str(uuid.uuid4())
        target_type = intent.target_element

        self.logger.info(f"[DashboardEditorAgent] Generating new {target_type} element")

        # Determine what type of element to create
        if target_type in ['pie_chart', 'line_chart', 'bar_chart', 'chart']:
            return await self._generate_new_chart(
                new_element_id, source_element_config, feedback, target_type
            )
        elif target_type == 'kpi':
            return await self._generate_new_kpi(
                new_element_id, source_element_config, feedback
            )
        elif target_type == 'insight':
            return await self._generate_new_insight(
                new_element_id, source_element_config, feedback
            )
        else:
            # Default to creating a chart
            return await self._generate_new_chart(
                new_element_id, source_element_config, feedback, 'chart'
            )

    async def _generate_new_chart(
        self,
        new_element_id: str,
        source_config: Dict[str, Any],
        feedback: str,
        chart_type_hint: str
    ) -> DashboardEdit:
        """Generate a new chart based on source element data"""
        # Get data from source if available
        source_vega_spec = source_config.get('vegaSpec', source_config.get('spec', {}))
        source_data = source_vega_spec.get('data', {}).get('values', [])
        source_title = source_config.get('title', '')

        # Determine the chart type
        chart_type_map = {
            'pie_chart': 'arc',
            'line_chart': 'line',
            'bar_chart': 'bar',
            'chart': 'bar'
        }
        mark_type = chart_type_map.get(chart_type_hint, 'bar')
        display_type = chart_type_hint.replace('_chart', '') if '_chart' in chart_type_hint else chart_type_hint

        prompt = f"""Create a new Vega-Lite chart specification based on this request.

SOURCE ELEMENT DATA (if available):
{json.dumps(source_data[:5] if source_data else [], indent=2)}
(showing first 5 rows of {len(source_data) if source_data else 0} total)

SOURCE VEGA SPEC (for reference):
{json.dumps(source_vega_spec, indent=2) if source_vega_spec else 'None'}

USER REQUEST: "{feedback}"

REQUESTED CHART TYPE: {display_type}

Generate a complete Vega-Lite specification for the new chart. Return a JSON object:
{{
    "type": "chart",
    "chartType": "{display_type}",
    "title": "<descriptive title for the new chart>",
    "vegaSpec": {{
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "mark": "{mark_type}" or {{"type": "arc"}} for pie charts,
        "encoding": {{ ... appropriate encodings ... }},
        "data": {{"values": [... use source data if applicable ...]}}
    }}
}}

Guidelines:
- For pie charts: use "arc" mark with "theta" for values and "color" for categories
- For line charts: use "line" mark with "x" for time/category and "y" for values
- For bar charts: use "bar" mark with appropriate x/y encodings
- Reuse data from the source element if it makes sense
- Create a meaningful title based on the user's request

Return ONLY the JSON object."""

        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                response_format="json",
                temperature=0.3,
                max_tokens=2000
            )

            new_element = json.loads(response)
            self.logger.info(f"[DashboardEditorAgent] Generated new chart: {new_element.get('title', 'Untitled')}")

            return DashboardEdit(
                element_id=new_element_id,
                action='add',
                changes={
                    'type': 'chart',
                    'content': {
                        'chartType': new_element.get('chartType', display_type),
                        'title': new_element.get('title', f'New {display_type} Chart'),
                        'vegaSpec': new_element.get('vegaSpec', {}),
                        'data': source_data if source_data else []
                    }
                },
                reasoning=f"Created new {display_type} chart based on: {feedback[:100]}"
            )

        except Exception as e:
            self.logger.warning(f"New chart generation failed: {e}")
            # Return a basic chart template
            return DashboardEdit(
                element_id=new_element_id,
                action='add',
                changes={
                    'type': 'chart',
                    'content': {
                        'chartType': display_type,
                        'title': f'New {display_type.title()} Chart',
                        'vegaSpec': {
                            '$schema': 'https://vega.github.io/schema/vega-lite/v5.json',
                            'mark': mark_type if mark_type != 'arc' else {'type': 'arc'},
                            'data': {'values': source_data if source_data else []},
                            'encoding': {}
                        },
                        'data': source_data if source_data else []
                    }
                },
                reasoning=f"Created basic {display_type} chart (LLM generation failed: {str(e)})"
            )

    async def _generate_new_kpi(
        self,
        new_element_id: str,
        source_config: Dict[str, Any],
        feedback: str
    ) -> DashboardEdit:
        """Generate a new KPI card based on source element data"""
        # Try to get data from source
        source_vega_spec = source_config.get('vegaSpec', source_config.get('spec', {}))
        source_data = source_vega_spec.get('data', {}).get('values', [])

        prompt = f"""Create a new KPI card based on this request.

SOURCE DATA (if available):
{json.dumps(source_data[:10] if source_data else [], indent=2)}

USER REQUEST: "{feedback}"

Generate a KPI card configuration. Return a JSON object:
{{
    "name": "<KPI name, e.g., 'Total Revenue', 'Average Score'>",
    "value": <numeric value or calculated from data>,
    "formattedValue": "<formatted string, e.g., '$1.2M', '85%', '1,234'>",
    "trend": <percentage change as number, e.g., 12.5 or -3.2>,
    "trendDirection": "<up/down/flat>",
    "comparisonLabel": "<e.g., 'vs last month', 'YoY'>"
}}

If data is available, calculate a meaningful metric. Otherwise, use placeholder values.

Return ONLY the JSON object."""

        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                response_format="json",
                temperature=0.3,
                max_tokens=500
            )

            kpi_config = json.loads(response)
            self.logger.info(f"[DashboardEditorAgent] Generated new KPI: {kpi_config.get('name', 'Untitled')}")

            return DashboardEdit(
                element_id=new_element_id,
                action='add',
                changes={
                    'type': 'kpi-card',
                    'content': {
                        'id': new_element_id,
                        'name': kpi_config.get('name', 'New KPI'),
                        'value': kpi_config.get('value', 0),
                        'formattedValue': kpi_config.get('formattedValue', '0'),
                        'trend': kpi_config.get('trend'),
                        'trendDirection': kpi_config.get('trendDirection', 'flat'),
                        'comparisonLabel': kpi_config.get('comparisonLabel', '')
                    }
                },
                reasoning=f"Created new KPI based on: {feedback[:100]}"
            )

        except Exception as e:
            self.logger.warning(f"New KPI generation failed: {e}")
            return DashboardEdit(
                element_id=new_element_id,
                action='add',
                changes={
                    'type': 'kpi-card',
                    'content': {
                        'id': new_element_id,
                        'name': 'New KPI',
                        'value': 0,
                        'formattedValue': '0',
                        'trendDirection': 'flat'
                    }
                },
                reasoning=f"Created basic KPI (LLM generation failed: {str(e)})"
            )

    async def _generate_new_insight(
        self,
        new_element_id: str,
        source_config: Dict[str, Any],
        feedback: str
    ) -> DashboardEdit:
        """Generate a new insight/note based on source element"""
        # Get context from source
        source_title = source_config.get('title', '')
        source_vega_spec = source_config.get('vegaSpec', source_config.get('spec', {}))
        source_data = source_vega_spec.get('data', {}).get('values', [])
        source_content = source_config.get('content', '')

        prompt = f"""Create a new insight/note based on this dashboard element.

SOURCE ELEMENT:
- Title: {source_title}
- Data sample: {json.dumps(source_data[:5] if source_data else [], indent=2)}
- Existing content: {source_content[:500] if source_content else 'None'}

USER REQUEST: "{feedback}"

Generate insightful content as markdown. Return a JSON object:
{{
    "content": "<markdown content with key insights, bullet points, or summary>"
}}

Guidelines:
- If summarizing a chart, highlight key trends and notable values
- Use bullet points for clarity
- Keep it concise but informative
- Make it actionable if possible

Return ONLY the JSON object."""

        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                response_format="json",
                temperature=0.4,
                max_tokens=1000
            )

            insight_config = json.loads(response)
            self.logger.info(f"[DashboardEditorAgent] Generated new insight")

            return DashboardEdit(
                element_id=new_element_id,
                action='add',
                changes={
                    'type': 'insight-note',
                    'content': {
                        'content': insight_config.get('content', 'New insight'),
                        'aiGenerated': True,
                        'tags': ['ai-generated']
                    }
                },
                reasoning=f"Created new insight based on: {feedback[:100]}"
            )

        except Exception as e:
            self.logger.warning(f"New insight generation failed: {e}")
            return DashboardEdit(
                element_id=new_element_id,
                action='add',
                changes={
                    'type': 'insight-note',
                    'content': {
                        'content': f'New insight based on: {feedback}',
                        'aiGenerated': True,
                        'tags': ['ai-generated']
                    }
                },
                reasoning=f"Created basic insight (LLM generation failed: {str(e)})"
            )

    def _extract_element_id(
        self,
        selector: str,
        config: Dict[str, Any]
    ) -> str:
        """
        Extract element ID from selector or config
        """
        # Try to extract from selector like [data-felix-id="abc123"]
        if 'data-felix-id=' in selector:
            start = selector.find('data-felix-id="') + len('data-felix-id="')
            end = selector.find('"', start)
            if start > 0 and end > start:
                return selector[start:end]

        # Try to get from config
        if 'id' in config:
            return config['id']

        # Fallback - this shouldn't happen in normal operation
        return 'unknown'
