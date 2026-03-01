"""
Dashboard Editor Agent - interprets annotations and generates dashboard modifications
"""
from typing import Dict, Any, Optional, List
import json
from app.services.agents.base_agent import BaseAgent
from app.schemas.agent import AgentConfig, AgentRequest, AgentResponse, AgentContext
from app.schemas.annotation import AnnotationRequest, DashboardEdit, IntentAnalysis, ContextCreateRequest
from app.services.agents.llm_service import LLMService
from app.services.duckdb_service import DuckDBService


# US State abbreviation to full name mapping for bridge transforms
US_STATE_ABBR_TO_NAME = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
    "PR": "Puerto Rico", "VI": "Virgin Islands", "GU": "Guam",
    "AS": "American Samoa", "MP": "Northern Mariana Islands"
}

# Canadian province abbreviation to full name mapping
CA_PROVINCE_ABBR_TO_NAME = {
    "AB": "Alberta", "BC": "British Columbia", "MB": "Manitoba",
    "NB": "New Brunswick", "NL": "Newfoundland and Labrador",
    "NS": "Nova Scotia", "NT": "Northwest Territories", "NU": "Nunavut",
    "ON": "Ontario", "PE": "Prince Edward Island", "QC": "Quebec",
    "SK": "Saskatchewan", "YT": "Yukon"
}

# Country abbreviation/code to full name mapping (ISO 3166-1 alpha-2/3)
COUNTRY_CODE_TO_NAME = {
    "US": "United States of America", "USA": "United States of America",
    "UK": "United Kingdom", "GB": "United Kingdom", "GBR": "United Kingdom",
    "CA": "Canada", "CAN": "Canada",
    "DE": "Germany", "DEU": "Germany",
    "FR": "France", "FRA": "France",
    "JP": "Japan", "JPN": "Japan",
    "CN": "China", "CHN": "China",
    "IN": "India", "IND": "India",
    "BR": "Brazil", "BRA": "Brazil",
    "AU": "Australia", "AUS": "Australia",
    "MX": "Mexico", "MEX": "Mexico",
    "RU": "Russian Federation", "RUS": "Russian Federation",
    "KR": "South Korea", "KOR": "South Korea",
    "IT": "Italy", "ITA": "Italy",
    "ES": "Spain", "ESP": "Spain",
    "NL": "Netherlands", "NLD": "Netherlands",
    # Add more as needed
}

# TopoJSON (Natural Earth) name → Common data name mapping
# Maps FROM the official TopoJSON/Natural Earth naming TO common names used in datasets
# This is ONE-TO-ONE: each TopoJSON name maps to exactly one common name
TOPOJSON_TO_COMMON_NAME = {
    # Americas
    "United States of America": "United States",
    "Bolivia, Plurinational State of": "Bolivia",
    "Venezuela, Bolivarian Republic of": "Venezuela",

    # Europe
    "Russian Federation": "Russia",
    "Czechia": "Czech Republic",
    "North Macedonia": "Macedonia",

    # Asia
    "Korea, Republic of": "South Korea",
    "Korea, Dem. People's Rep.": "North Korea",
    "Viet Nam": "Vietnam",
    "Iran, Islamic Rep.": "Iran",
    "Lao PDR": "Laos",
    "Syrian Arab Republic": "Syria",

    # Africa
    "Côte d'Ivoire": "Ivory Coast",
    "Congo, Dem. Rep.": "Democratic Republic of Congo",
    "Congo, Rep.": "Republic of Congo",
    "Tanzania, United Rep.": "Tanzania",
    "Cabo Verde": "Cape Verde",
    "Eswatini": "Swaziland",
}

# Common data name variations that might appear in datasets
# Used to DETECT if data needs normalization (maps data name → TopoJSON name for detection only)
COMMON_NAME_VARIATIONS = {
    # These are names that might appear in data that differ from TopoJSON
    "United States", "US", "USA", "U.S.", "U.S.A.", "America",
    "Russia", "UK", "Britain", "Great Britain", "England",
    "South Korea", "Korea", "North Korea", "DPRK",
    "Vietnam", "Iran", "Persia", "Czech Republic", "Czech",
    "Laos", "Syria", "Ivory Coast", "Burma", "Myanmar",
    "DRC", "Democratic Republic of Congo", "Republic of Congo",
    "Tanzania", "Cape Verde", "Swaziland", "Macedonia",
}


class DashboardEditorAgent(BaseAgent):
    """
    Dashboard Editor Agent - processes user annotations and generates edits

    Interprets natural language feedback on dashboard elements and generates
    structured modification instructions.
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.llm_service = LLMService()
        self.duckdb_service = DuckDBService()

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

        # For maps, we need comprehensive geographic data - always fetch from database
        # Context sample_data is typically limited (e.g., 20 rows) which is insufficient for maps
        if is_map_request:
            # First detect geo fields from context to understand the data structure
            context_data = context.sample_data if context.sample_data else chart_data_for_maps
            detected_fields = self._detect_geo_fields(context_data, context.columns)

            # Determine geo type hint from user feedback or detected fields
            geo_type_hint = detected_fields.get('geo_type')
            if not geo_type_hint:
                if any(word in feedback_lower for word in ['state', 'states', 'us ']):
                    geo_type_hint = 'state'
                elif any(word in feedback_lower for word in ['country', 'countries', 'world']):
                    geo_type_hint = 'country'
                elif any(word in feedback_lower for word in ['county', 'counties']):
                    geo_type_hint = 'county'
                elif any(word in feedback_lower for word in ['province', 'provinces', 'canada']):
                    geo_type_hint = 'province'

            # Always fetch from database for maps to get comprehensive data (up to 1000 rows)
            self.logger.info(f"[DashboardEditorAgent] Fetching map data from database (geo_type: {geo_type_hint})")
            geo_result = await self._fetch_geographic_data(
                dataset_id=context.dataset_id,
                all_columns=context.columns,
                feedback=request.feedback,
                geo_type_hint=geo_type_hint
            )

            if geo_result and geo_result.get('data'):
                all_data = geo_result['data']
                # Update detected fields with the fetched data info
                if geo_result.get('geo_field'):
                    detected_fields['geo_field'] = geo_result['geo_field']
                if geo_result.get('value_field'):
                    detected_fields['value_field'] = geo_result['value_field']
                if geo_result.get('geo_type'):
                    detected_fields['geo_type'] = geo_result['geo_type']
                self.logger.info(f"[DashboardEditorAgent] Using {len(all_data)} rows from database query")
            else:
                # Fallback to context data if database fetch fails
                all_data = context_data
                self.logger.warning(f"[DashboardEditorAgent] Database fetch failed, using {len(all_data)} context rows as fallback")

            total_data_rows = len(all_data)
            # Only pass 5 sample rows to prompt to avoid token limits
            # LLM will return "__DATA_PLACEHOLDER__" which we replace with actual data
            data_for_prompt = all_data[:5]
            self.logger.info(f"[DashboardEditorAgent] Map request detected, passing {len(data_for_prompt)} sample rows (total: {total_data_rows})")
        else:
            all_data = context.sample_data if context.sample_data else []
            total_data_rows = len(all_data)
            data_for_prompt = all_data[:10]

        # Build appropriate prompt based on request type
        if is_map_request:
            # Detect geo fields with abbreviation detection
            detected_fields = self._detect_geo_fields(all_data, context.columns)
            prompt = self._build_map_prompt(
                kpi_data, chart_summaries, context.columns, data_for_prompt,
                request.feedback, total_data_rows, detected_fields
            )
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
            # Use higher token limit for maps due to complex transform structures
            max_tokens = 16000 if is_map_request else 2000

            response = await self.llm_service.generate(
                prompt=prompt,
                response_format="json",
                temperature=0.3,
                max_tokens=max_tokens
            )

            chart_config = json.loads(response)
            self.logger.info(f"[DashboardEditorAgent] Created chart from context: {chart_config.get('title', 'Untitled')}")

            # Post-process: Replace placeholders with actual data
            if is_map_request:
                # Inject data and abbreviation lookup table if needed
                abbr_type = detected_fields.get('abbreviation_type') if detected_fields else None
                chart_config = self._inject_map_placeholders(chart_config, all_data, abbr_type)
                self.logger.info(f"[DashboardEditorAgent] Injected {len(all_data)} data rows into map spec")

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
        feedback: str,
        total_data_rows: int = None,
        detected_fields: dict = None
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

        # Use detected fields if provided, otherwise detect from data
        geo_field = detected_fields.get('geo_field') if detected_fields else None
        value_field = detected_fields.get('value_field') if detected_fields else None
        uses_abbreviations = detected_fields.get('uses_abbreviations', False) if detected_fields else False
        abbreviation_type = detected_fields.get('abbreviation_type') if detected_fields else None
        detected_geo_type = detected_fields.get('geo_type') if detected_fields else None

        # Use detected geo_type to infer map type when user doesn't specify
        # This ensures "country" fields result in world maps, not US state maps
        if detected_geo_type == 'country' and not is_us_states and not is_us_counties:
            is_world_map = True
        elif detected_geo_type == 'province' and not is_us_states and not is_us_counties:
            is_canada_map = True
            is_canada_provinces = True
        elif detected_geo_type == 'state' and not is_world_map and not is_us_counties:
            is_us_states = True
        elif detected_geo_type == 'county':
            is_us_counties = True

        # Fallback field detection if not provided
        if not geo_field and all_data and len(all_data) > 0:
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
            value_candidates = ['value', 'datavalue', 'data_value', 'total', 'count', 'amount',
                              'datavalue_total', 'sum', 'avg', 'average', 'casualties',
                              'deaths', 'injured', 'affected', 'damage', 'loss', 'population',
                              'rate', 'percent', 'percentage', 'income', 'gdp', 'sales',
                              'severity', 'index', 'score', 'risk', 'level', 'magnitude',
                              'intensity', 'frequency', 'cases', 'incidents']

            for key in first_row.keys():
                key_lower = key.lower()
                if is_us_counties and any(c in key_lower for c in county_candidates):
                    geo_field = key
                elif is_canada_map and any(p in key_lower for p in province_candidates):
                    geo_field = key
                elif (is_world_map or is_europe_map) and any(c in key_lower for c in country_candidates):
                    geo_field = key
                elif is_us_states and any(s in key_lower for s in state_candidates):
                    geo_field = key
                if not geo_field:
                    all_geo = county_candidates + country_candidates + state_candidates + province_candidates
                    if any(g in key_lower for g in all_geo):
                        geo_field = key
                if any(v in key_lower for v in value_candidates):
                    value_field = key

        # Determine map type and configuration
        if is_us_counties:
            map_type = "us_counties"
            topojson_url = "https://cdn.jsdelivr.net/npm/us-atlas@3/counties-10m.json"
            topojson_feature = "counties"
            projection = "albersUsa"
            geo_property = "id"
            geo_label = "County"
            lookup_note = "Counties use FIPS codes (5-digit: 2-digit state + 3-digit county)."
        elif is_canada_provinces:
            map_type = "canada_provinces"
            topojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/canada.geojson"
            topojson_feature = None
            projection = "conicConformal"
            geo_property = "properties.name"
            geo_label = "Province"
            lookup_note = "Use full province names (e.g., 'Ontario', 'British Columbia')."
        elif is_canada_map:
            map_type = "canada_provinces"
            topojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/canada.geojson"
            topojson_feature = None
            projection = "conicConformal"
            geo_property = "properties.name"
            geo_label = "Province/CMA"
            lookup_note = "For CMAs, aggregate to province level."
        elif is_europe_map:
            map_type = "europe"
            topojson_url = "https://raw.githubusercontent.com/leakyMirror/map-of-europe/master/TopoJSON/europe.topojson"
            topojson_feature = "europe"
            projection = "conicConformal"
            geo_property = "properties.NAME"
            geo_label = "Country"
            lookup_note = "Use English country names."
        elif is_world_map or (not is_us_states and not geo_field):
            map_type = "world"
            topojson_url = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json"
            topojson_feature = "countries"
            projection = "equalEarth"
            geo_property = "properties.name"
            geo_label = "Country"
            lookup_note = "Use Natural Earth naming: 'United States of America' (not 'USA')."
        else:
            map_type = "us_states"
            topojson_url = "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json"
            topojson_feature = "states"
            projection = "albersUsa"
            geo_property = "properties.name"
            geo_label = "State"
            lookup_note = "Use full state names (e.g., 'California', not 'CA')."

        self.logger.info(f"[DashboardEditorAgent] Map prompt - type: {map_type}, geo_field: {geo_field}, value_field: {value_field}, uses_abbr: {uses_abbreviations}")

        actual_total_rows = total_data_rows if total_data_rows is not None else len(all_data)
        self.logger.info(f"[DashboardEditorAgent] Map prompt - sample rows: {len(all_data)}, total rows: {actual_total_rows}")

        # Build format specification
        if topojson_feature:
            data_format = f'{{"type": "topojson", "feature": "{topojson_feature}"}}'
        else:
            data_format = '{"type": "json", "property": "features"}'

        map_type_descriptions = {
            "world": "WORLD/COUNTRIES",
            "us_states": "US STATES",
            "us_counties": "US COUNTIES",
            "canada_provinces": "CANADIAN PROVINCES",
            "europe": "EUROPEAN COUNTRIES"
        }
        map_description = map_type_descriptions.get(map_type, map_type.upper())

        # Build KPI context for the prompt
        kpi_context = ""
        if kpi_data:
            kpi_context = f"""
AVAILABLE KPIs ({len(kpi_data)} total):
{json.dumps(kpi_data, indent=2)}
"""

        # Build abbreviation/normalization handling instructions
        abbr_instructions = ""
        bridge_transform_example = ""

        if uses_abbreviations and abbreviation_type:
            # All lookups use consistent field names: map_name (TopoJSON) and clean_name (data)
            abbr_instructions = f"""
CRITICAL - DATA NAMES DON'T MATCH TOPOJSON:
Your data uses names like 'United States' but the TopoJSON uses 'United States of America'.

You MUST use a THREE-STEP BRIDGE TRANSFORM with a fallback for countries not in the mapping.
The mapping table uses: "map_name" (TopoJSON name) and "clean_name" (your data's name).
"""

            bridge_transform_example = f"""
REQUIRED TRANSFORM PATTERN (Three-Step Bridge with Fallback):
"transform": [
    {{
        "lookup": "properties.name",
        "from": {{
            "data": {{"values": "__ABBR_LOOKUP_PLACEHOLDER__"}},
            "key": "map_name",
            "fields": ["clean_name"]
        }}
    }},
    {{
        "calculate": "datum.clean_name || datum.properties.name",
        "as": "lookup_key"
    }},
    {{
        "lookup": "lookup_key",
        "from": {{
            "data": {{"values": "__DATA_PLACEHOLDER__"}},
            "key": "{geo_field}",
            "fields": ["{value_field or 'value'}"]
        }}
    }}
]

EXPLANATION:
1. First lookup: Match TopoJSON's "properties.name" (e.g., "United States of America") against
   "map_name" in the mapping table, and pull in "clean_name" (e.g., "United States").
   Countries NOT in the mapping table will have null for "clean_name".

2. Calculate (CRITICAL FALLBACK): Creates "lookup_key" using "clean_name" if it exists,
   otherwise falls back to "properties.name". This ensures countries like "Brazil" that
   don't need mapping still work (Brazil → Brazil).

3. Second lookup: Match "lookup_key" against your data's "{geo_field}" field to get values.

The mapping table format is:
[
    {{"map_name": "United States of America", "clean_name": "United States"}},
    {{"map_name": "Russian Federation", "clean_name": "Russia"}},
    ...
]
"""

        return f"""Create a Vega-Lite GEOSPATIAL CHOROPLETH MAP based on this data.

IMPORTANT: This is a {map_description} MAP request.
{kpi_context}
SAMPLE DATA (showing {len(all_data)} of {actual_total_rows} total rows):
{json.dumps(all_data, indent=2)}

DETECTED FIELDS:
- Geographic field: {geo_field or 'Not detected - check data keys'}
- Value field for coloring: {value_field or 'Not detected - check data keys'}
- Uses abbreviations: {uses_abbreviations}
- Abbreviation type: {abbreviation_type or 'N/A'}

AVAILABLE COLUMNS: {columns if columns else list(all_data[0].keys()) if all_data else 'None'}

USER REQUEST: "{feedback}"
{abbr_instructions}
MAP CONFIGURATION:
- Map Type: {map_description}
- Geographic Data URL: {topojson_url}
- Feature: {topojson_feature or 'GeoJSON features'}
- Projection: {projection}
- Geographic Property for lookup: {geo_property}
- LOOKUP NOTE: {lookup_note}
{bridge_transform_example}
Create a Vega-Lite choropleth map specification. You MUST:
1. Use the geographic data from: "{topojson_url}"
2. Use the placeholder "__DATA_PLACEHOLDER__" for the data values (will be injected post-processing)
3. {"Use '__ABBR_LOOKUP_PLACEHOLDER__' for the abbreviation lookup table (will be injected)" if uses_abbreviations else "Use the correct geographic field to join with the TopoJSON"}
4. Color-code regions based on the value field
5. Place "projection" at the TOP LEVEL of the spec (not inside encoding)

Return a JSON object:
{{
    "chartType": "map",
    "title": "<descriptive title for the map>",
    "vegaSpec": {{
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "width": 800,
        "height": 500,
        "projection": {{"type": "{projection}"}},
        "data": {{
            "url": "{topojson_url}",
            "format": {data_format}
        }},
        "transform": [
            {"... bridge transform if using abbreviations ..." if uses_abbreviations else "... lookup transform ..."}
        ],
        "mark": {{"type": "geoshape", "stroke": "white", "strokeWidth": 0.5}},
        "encoding": {{
            "color": {{
                "field": "{value_field or '<value field>'}",
                "type": "quantitative",
                "scale": {{"scheme": "blues"}},
                "legend": {{"title": "<value description>"}}
            }},
            "tooltip": [
                {{"field": "{'name' if uses_abbreviations else geo_property}", "type": "nominal", "title": "{geo_label}"}},
                {{"field": "{value_field or '<value field>'}", "type": "quantitative", "title": "Value", "format": ",.0f"}}
            ]
        }}
    }}
}}

CRITICAL REQUIREMENTS:
1. {lookup_note}
2. Use "__DATA_PLACEHOLDER__" for the values array - the actual {actual_total_rows} rows will be injected
3. {"Use '__ABBR_LOOKUP_PLACEHOLDER__' for the abbreviation-to-name lookup table" if uses_abbreviations else "Match your data's geographic field to " + geo_property}
4. projection MUST be at the TOP LEVEL of vegaSpec (NOT inside encoding)
5. Include all relevant value fields in the lookup transform's "fields" array

Return ONLY the JSON object."""

    def _inject_data_placeholder(self, chart_config: dict, actual_data: list) -> dict:
        """
        Replace __DATA_PLACEHOLDER__ in the chart config with actual data.

        This is used to avoid token limits by having the LLM return a placeholder
        instead of all data rows, then injecting the actual data post-processing.
        """
        import copy
        result = copy.deepcopy(chart_config)

        def replace_placeholder(obj):
            """Recursively find and replace __DATA_PLACEHOLDER__ in nested structure"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if value == "__DATA_PLACEHOLDER__":
                        obj[key] = actual_data
                    elif isinstance(value, (dict, list)):
                        replace_placeholder(value)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if item == "__DATA_PLACEHOLDER__":
                        obj[i] = actual_data
                    elif isinstance(item, (dict, list)):
                        replace_placeholder(item)

        replace_placeholder(result)
        return result

    def _inject_map_placeholders(
        self,
        chart_config: dict,
        actual_data: list,
        abbreviation_type: Optional[str] = None
    ) -> dict:
        """
        Replace map placeholders in the chart config with actual data.

        Handles both __DATA_PLACEHOLDER__ and __ABBR_LOOKUP_PLACEHOLDER__.

        Args:
            chart_config: The Vega-Lite chart configuration with placeholders
            actual_data: The actual data rows to inject
            abbreviation_type: Type of abbreviation lookup to inject (us_state, ca_province, country)

        Returns:
            Chart config with placeholders replaced
        """
        import copy
        result = copy.deepcopy(chart_config)

        # Get abbreviation lookup data if needed
        abbr_lookup_data = []
        if abbreviation_type:
            abbr_lookup_data = self._get_abbreviation_lookup_data(abbreviation_type)
            self.logger.info(f"[DashboardEditorAgent] Injecting {len(abbr_lookup_data)} abbreviation lookup entries")

        def replace_placeholders(obj):
            """Recursively find and replace placeholders in nested structure"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if value == "__DATA_PLACEHOLDER__":
                        obj[key] = actual_data
                    elif value == "__ABBR_LOOKUP_PLACEHOLDER__":
                        obj[key] = abbr_lookup_data
                    elif isinstance(value, (dict, list)):
                        replace_placeholders(value)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if item == "__DATA_PLACEHOLDER__":
                        obj[i] = actual_data
                    elif item == "__ABBR_LOOKUP_PLACEHOLDER__":
                        obj[i] = abbr_lookup_data
                    elif isinstance(item, (dict, list)):
                        replace_placeholders(item)

        replace_placeholders(result)

        # Ensure projection is at top level of vegaSpec (fix common LLM mistake)
        if 'vegaSpec' in result:
            vega_spec = result['vegaSpec']
            self._ensure_projection_at_top_level(vega_spec)

        return result

    def _ensure_projection_at_top_level(self, vega_spec: dict) -> None:
        """
        Ensure projection is defined at the top level of the Vega-Lite spec.

        LLMs sometimes incorrectly place projection inside encoding or other nested structures.
        This method moves it to the top level where it belongs for geoshape marks.
        """
        # Check if projection exists at top level
        if 'projection' in vega_spec:
            return

        # Check common wrong locations and move to top level
        projection = None

        # Check in encoding
        if 'encoding' in vega_spec and isinstance(vega_spec['encoding'], dict):
            if 'projection' in vega_spec['encoding']:
                projection = vega_spec['encoding'].pop('projection')

        # Check in mark
        if 'mark' in vega_spec and isinstance(vega_spec['mark'], dict):
            if 'projection' in vega_spec['mark']:
                projection = vega_spec['mark'].pop('projection')

        # If found, move to top level
        if projection:
            vega_spec['projection'] = projection
            self.logger.info(f"[DashboardEditorAgent] Moved projection to top level: {projection}")

        # If still no projection and this is a geoshape, add default
        mark = vega_spec.get('mark', {})
        mark_type = mark.get('type') if isinstance(mark, dict) else mark
        if mark_type == 'geoshape' and 'projection' not in vega_spec:
            # Detect appropriate projection from data URL
            data_url = vega_spec.get('data', {}).get('url', '')
            if 'us-atlas' in data_url:
                vega_spec['projection'] = {"type": "albersUsa"}
            elif 'world-atlas' in data_url:
                vega_spec['projection'] = {"type": "equalEarth"}
            else:
                vega_spec['projection'] = {"type": "mercator"}
            self.logger.info(f"[DashboardEditorAgent] Added default projection: {vega_spec['projection']}")

    def _detect_geo_fields(self, data: List[Dict[str, Any]], columns: List[str]) -> Dict[str, Optional[str]]:
        """
        Detect geographic fields in the data or column list.

        Returns a dict with detected field names:
        {
            'geo_field': <field name or None>,
            'geo_type': <'state'|'country'|'county'|'province'|None>,
            'value_field': <field name or None>,
            'uses_abbreviations': <True|False>,
            'abbreviation_type': <'us_state'|'ca_province'|'country'|None>
        }
        """
        # Geographic field candidates by type - ordered by specificity
        # Fields containing 'abbr' strongly indicate abbreviations
        geo_candidates = {
            'state': {
                'abbr_fields': ['locationabbr', 'state_abbr', 'stateabbr', 'stabbr',
                               'st_abbr', 'state_code', 'statecode'],
                'name_fields': ['state', 'statename', 'state_name', 'locationdesc',
                               'us_state', 'statedesc']
            },
            'country': {
                'abbr_fields': ['iso', 'iso2', 'iso3', 'iso_code', 'country_code',
                               'countrycode', 'country_abbr'],
                'name_fields': ['country', 'country_name', 'countryname', 'nation',
                               'territory']
            },
            'county': {
                'abbr_fields': ['fips', 'fips_code', 'county_fips', 'geoid', 'fipscode'],
                'name_fields': ['county', 'county_name', 'countyname']
            },
            'province': {
                'abbr_fields': ['prov_abbr', 'province_code', 'provcode'],
                'name_fields': ['province', 'province_name', 'prov', 'cma', 'cma_name',
                               'region', 'canadian_province']
            }
        }

        # Value field candidates - include index, score, severity for map-friendly fields
        value_candidates = ['value', 'datavalue', 'data_value', 'total', 'count', 'amount',
                           'sum', 'avg', 'average', 'casualties', 'deaths', 'injured',
                           'affected', 'damage', 'loss', 'population', 'rate', 'percent',
                           'percentage', 'income', 'gdp', 'sales', 'revenue', 'quantity',
                           'severity', 'index', 'score', 'severity_index', 'risk', 'level',
                           'magnitude', 'intensity', 'frequency', 'cases', 'incidents']

        result = {
            'geo_field': None,
            'geo_type': None,
            'value_field': None,
            'uses_abbreviations': False,
            'abbreviation_type': None
        }

        # Get all available field names
        field_names = set(columns) if columns else set()
        if data and len(data) > 0:
            field_names.update(data[0].keys())

        field_names_lower = {f.lower(): f for f in field_names}

        # Check for geographic fields - prioritize abbreviation fields first
        for geo_type, field_types in geo_candidates.items():
            # First check abbreviation fields
            for candidate in field_types['abbr_fields']:
                if candidate in field_names_lower:
                    result['geo_field'] = field_names_lower[candidate]
                    result['geo_type'] = geo_type
                    result['uses_abbreviations'] = True
                    if geo_type == 'state':
                        result['abbreviation_type'] = 'us_state'
                    elif geo_type == 'province':
                        result['abbreviation_type'] = 'ca_province'
                    elif geo_type == 'country':
                        result['abbreviation_type'] = 'country'
                    break
            if result['geo_field']:
                break

            # Then check name fields
            for candidate in field_types['name_fields']:
                if candidate in field_names_lower:
                    result['geo_field'] = field_names_lower[candidate]
                    result['geo_type'] = geo_type
                    break
            if result['geo_field']:
                break

        # If we found a geo field but haven't determined if it uses abbreviations,
        # check the actual data values
        if result['geo_field'] and not result['uses_abbreviations'] and data:
            result['uses_abbreviations'], result['abbreviation_type'] = self._check_data_for_abbreviations(
                data, result['geo_field'], result['geo_type']
            )

        # Check for value fields using substring matching
        for field_lower, field_original in field_names_lower.items():
            if any(v in field_lower for v in value_candidates):
                result['value_field'] = field_original
                break

        self.logger.info(f"[DashboardEditorAgent] Detected geo fields: {result}")
        return result

    def _check_data_for_abbreviations(
        self,
        data: List[Dict[str, Any]],
        geo_field: str,
        geo_type: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check actual data values to determine if they are abbreviations or need normalization.

        Returns (needs_transform, transform_type) where transform_type can be:
        - 'us_state': US state abbreviations (e.g., 'TN' -> 'Tennessee')
        - 'ca_province': Canadian province abbreviations
        - 'country': Country codes (e.g., 'US' -> 'United States of America')
        - 'country_names': Country name variations (e.g., 'United States' -> 'United States of America')
        """
        if not data or not geo_field:
            return False, None

        # Sample values from data (preserve original case for name matching)
        sample_values_original = set()
        sample_values_upper = set()
        for row in data[:50]:  # Check first 50 rows
            val = row.get(geo_field)
            if val and isinstance(val, str):
                sample_values_original.add(val.strip())
                sample_values_upper.add(val.strip().upper())

        if not sample_values_original:
            return False, None

        # Check if values match US state abbreviations
        if geo_type in ('state', None):
            us_abbr_matches = sum(1 for v in sample_values_upper if v in US_STATE_ABBR_TO_NAME)
            if us_abbr_matches >= len(sample_values_upper) * 0.5:  # >50% match
                self.logger.info(f"[DashboardEditorAgent] Data uses US state abbreviations ({us_abbr_matches}/{len(sample_values_upper)} match)")
                return True, 'us_state'

        # Check if values match Canadian province abbreviations
        if geo_type in ('province', None):
            ca_abbr_matches = sum(1 for v in sample_values_upper if v in CA_PROVINCE_ABBR_TO_NAME)
            if ca_abbr_matches >= len(sample_values_upper) * 0.5:
                self.logger.info(f"[DashboardEditorAgent] Data uses Canadian province abbreviations ({ca_abbr_matches}/{len(sample_values_upper)} match)")
                return True, 'ca_province'

        # Check if values match country codes (short codes like US, UK, DE)
        if geo_type in ('country', None):
            country_code_matches = sum(1 for v in sample_values_upper if v in COUNTRY_CODE_TO_NAME)
            if country_code_matches >= len(sample_values_upper) * 0.3:
                self.logger.info(f"[DashboardEditorAgent] Data uses country codes ({country_code_matches}/{len(sample_values_upper)} match)")
                return True, 'country'

        # Check if values are country names that need normalization
        if geo_type in ('country', None):
            # Check against common name variations (case-insensitive)
            common_names_upper = {n.upper() for n in COMMON_NAME_VARIATIONS}
            name_norm_matches = sum(1 for v in sample_values_upper if v in common_names_upper)
            if name_norm_matches >= 1:  # Even one match suggests we need normalization
                self.logger.info(f"[DashboardEditorAgent] Data uses country names needing normalization ({name_norm_matches}/{len(sample_values_upper)} match)")
                return True, 'country_names'

        # Check value lengths - short values (2-3 chars) likely abbreviations
        avg_len = sum(len(v) for v in sample_values_original) / len(sample_values_original)
        if avg_len <= 3:
            self.logger.info(f"[DashboardEditorAgent] Data appears to use abbreviations (avg length: {avg_len:.1f})")
            if geo_type == 'state':
                return True, 'us_state'
            elif geo_type == 'province':
                return True, 'ca_province'
            elif geo_type == 'country':
                return True, 'country'
            return True, 'us_state'  # Default to US state

        return False, None

    def _get_abbreviation_lookup_data(self, abbreviation_type: str) -> List[Dict[str, str]]:
        """
        Get the lookup table data for converting between naming conventions.

        Returns a list of dicts for use in Vega lookup transforms.
        Each entry has: {"map_name": "TopoJSON Name", "clean_name": "Data Name"}
        MUST be one-to-one on map_name to avoid Vega-Lite lookup conflicts.
        """
        if abbreviation_type == 'us_state':
            # Reverse mapping: full name (TopoJSON) → abbreviation (data)
            # US_STATE_ABBR_TO_NAME is already one-to-one (each abbr → unique name)
            return [{"map_name": v, "clean_name": k} for k, v in US_STATE_ABBR_TO_NAME.items()]
        elif abbreviation_type == 'ca_province':
            return [{"map_name": v, "clean_name": k} for k, v in CA_PROVINCE_ABBR_TO_NAME.items()]
        elif abbreviation_type == 'country':
            # Reverse mapping: full name (TopoJSON) → code (data)
            # COUNTRY_CODE_TO_NAME has duplicates (US, USA → same name) so deduplicate by map_name
            # Keep the shortest code as the canonical one (e.g., "US" over "USA")
            seen = {}
            for code, name in COUNTRY_CODE_TO_NAME.items():
                if name not in seen or len(code) < len(seen[name]):
                    seen[name] = code
            return [{"map_name": name, "clean_name": code} for name, code in seen.items()]
        elif abbreviation_type == 'country_names':
            # TopoJSON name → common data name (already one-to-one, correct direction)
            return [{"map_name": k, "clean_name": v} for k, v in TOPOJSON_TO_COMMON_NAME.items()]
        return []

    async def _fetch_geographic_data(
        self,
        dataset_id: str,
        all_columns: List[str],
        feedback: str,
        geo_type_hint: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch geographic data from the database when context data lacks geo fields.

        Uses LLM to generate appropriate aggregation query based on user request
        and available columns in the dataset.

        Args:
            dataset_id: The dataset ID to query
            all_columns: List of all available columns in the dataset
            feedback: User's request (e.g., "show value by state")
            geo_type_hint: Optional hint for geographic type from user request

        Returns:
            List of dicts with geographic data, or None if failed
        """
        if not dataset_id:
            self.logger.warning("[DashboardEditorAgent] No dataset_id provided for geographic data fetch")
            return None

        self.logger.info(f"[DashboardEditorAgent] Fetching geographic data for dataset: {dataset_id}")
        self.logger.info(f"[DashboardEditorAgent] Available columns: {all_columns}")

        # Use LLM to generate the appropriate aggregation query
        prompt = f"""Generate a SQL query to aggregate data by geographic region for a map visualization.

AVAILABLE COLUMNS in the 'dataset' table:
{json.dumps(all_columns, indent=2)}

USER REQUEST: "{feedback}"

GEOGRAPHIC TYPE HINT: {geo_type_hint or 'Detect from columns or user request'}

Generate a SQL query that:
1. Identifies the geographic column (state, country, county, province, etc.)
2. Aggregates numeric values appropriately (SUM, AVG, COUNT, etc.)
3. Groups by the geographic column
4. Returns results suitable for a choropleth map

IMPORTANT:
- The table is named 'dataset'
- Return ONLY rows with non-null geographic values
- Use LIMIT 1000 to get comprehensive geographic coverage

Return a JSON object:
{{
    "sql": "<the SQL query>",
    "geo_field": "<name of geographic column in result>",
    "value_field": "<name of value column in result>",
    "geo_type": "<state|country|county|province>"
}}

Return ONLY the JSON object."""

        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                response_format="json",
                temperature=0.2,
                max_tokens=500
            )

            query_config = json.loads(response)
            sql = query_config.get('sql', '')

            if not sql:
                self.logger.warning("[DashboardEditorAgent] LLM did not generate a valid SQL query")
                return None

            self.logger.info(f"[DashboardEditorAgent] Generated SQL for geographic data: {sql}")

            # Execute the query
            result_df = self.duckdb_service.execute_query(sql, dataset_id=dataset_id)

            if result_df.empty:
                self.logger.warning("[DashboardEditorAgent] Geographic query returned no results")
                return None

            # Convert to list of dicts
            geo_data = result_df.to_dict('records')
            self.logger.info(f"[DashboardEditorAgent] Fetched {len(geo_data)} geographic data rows")

            # Attach metadata for later use
            return {
                'data': geo_data,
                'geo_field': query_config.get('geo_field'),
                'value_field': query_config.get('value_field'),
                'geo_type': query_config.get('geo_type', 'state')
            }

        except Exception as e:
            self.logger.error(f"[DashboardEditorAgent] Failed to fetch geographic data: {e}")
            return None

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
