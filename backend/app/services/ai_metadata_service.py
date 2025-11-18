"""AI-powered metadata and query rule generation"""
import json
import httpx
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.column_metadata import ColumnMetadata, QueryRule
from app.services.storage_service import StorageService


class AIMetadataService:
    """Use AI to generate column metadata and query rules from natural language"""

    def __init__(self, db: Session):
        self.db = db
        self.storage_service = StorageService()

    async def generate_metadata_updates(
        self,
        dataset_id: str,
        instruction: str
    ) -> Dict[str, Any]:
        """
        Use AI to interpret instructions and generate metadata updates

        Examples:
        - "Mark email and phone columns as PII"
        - "Set revenue and sales columns to use SUM aggregation"
        - "Add business definitions for all customer columns"
        """
        # Load schema to understand available columns
        schema = self.storage_service.load_schema(dataset_id)

        # Build prompt for AI
        prompt = self._build_metadata_prompt(schema, instruction)

        # Call AI
        response = await self._call_ai(prompt)

        # Parse AI response to extract metadata updates
        updates = self._parse_metadata_response(response)

        return updates

    async def generate_query_rules(
        self,
        dataset_id: str,
        instruction: str
    ) -> List[Dict[str, Any]]:
        """
        Use AI to generate query rules from natural language

        Examples:
        - "Only show active customers"
        - "Filter out cancelled orders"
        - "Always exclude SSN column"
        - "Only show data from 2024"
        """
        # Load schema
        schema = self.storage_service.load_schema(dataset_id)

        # Build prompt
        prompt = self._build_rules_prompt(schema, instruction)

        # Call AI
        response = await self._call_ai(prompt)

        # Parse response
        rules = self._parse_rules_response(response)

        return rules

    async def apply_metadata_updates(
        self,
        dataset_id: str,
        updates: Dict[str, Any]
    ) -> List[str]:
        """Apply metadata updates to database"""
        updated_columns = []

        for column_name, metadata in updates.items():
            # Get or create metadata record
            existing = self.db.query(ColumnMetadata).filter(
                ColumnMetadata.dataset_id == dataset_id,
                ColumnMetadata.column_name == column_name
            ).first()

            if not existing:
                existing = ColumnMetadata(
                    dataset_id=dataset_id,
                    column_name=column_name
                )
                self.db.add(existing)

            # Update fields
            for field, value in metadata.items():
                if hasattr(existing, field):
                    setattr(existing, field, value)

            updated_columns.append(column_name)

        self.db.commit()
        return updated_columns

    async def apply_query_rules(
        self,
        dataset_id: str,
        rules: List[Dict[str, Any]]
    ) -> List[str]:
        """Create query rules in database"""
        created_rules = []

        for rule_data in rules:
            rule = QueryRule(
                dataset_id=dataset_id,
                **rule_data
            )
            self.db.add(rule)
            created_rules.append(rule_data['name'])

        self.db.commit()
        return created_rules

    def _build_metadata_prompt(self, schema: dict, instruction: str) -> str:
        """Build prompt for metadata generation"""
        columns_info = []
        for col in schema['columns']:
            col_info = f"- {col['name']} ({col['dtype']})"
            if 'stats' in col and 'top_values' in col['stats']:
                examples = [str(v[0]) for v in col['stats']['top_values'][:3]]
                col_info += f" - examples: {examples}"
            columns_info.append(col_info)

        return f"""You are a data analyst helping to add metadata to dataset columns.

Available columns:
{chr(10).join(columns_info)}

User instruction: {instruction}

Based on the instruction, generate metadata updates for the relevant columns.

Output ONLY a JSON object where keys are column names and values are metadata objects with these fields:
- display_name: string (friendly name)
- description: string (what this column represents)
- business_definition: string (business context)
- semantic_type: string (one of: text, email, phone, url, currency, percentage, date, datetime, time, number, integer, boolean)
- data_format: string (e.g., "MM/DD/YYYY", "$#,##0.00")
- unit: string (e.g., "USD", "meters")
- is_pii: boolean (personally identifiable information)
- is_required: boolean (should not be null)
- default_aggregation: string (one of: SUM, AVG, COUNT, MIN, MAX, COUNT_DISTINCT)
- is_dimension: boolean (good for GROUP BY)
- is_measure: boolean (good for aggregation)

Only include fields that should be updated. Do not include fields that should remain unchanged.

Example output:
{{
  "email": {{"is_pii": true, "semantic_type": "email"}},
  "revenue": {{"default_aggregation": "SUM", "is_measure": true, "unit": "USD"}}
}}

JSON output:"""

    def _build_rules_prompt(self, schema: dict, instruction: str) -> str:
        """Build prompt for rule generation"""
        columns_info = []
        for col in schema['columns']:
            col_info = f"- {col['name']} ({col['dtype']})"
            if 'stats' in col:
                if 'top_values' in col['stats']:
                    examples = [str(v[0]) for v in col['stats']['top_values'][:3]]
                    col_info += f" - values: {examples}"
                elif 'min' in col['stats'] and 'max' in col['stats']:
                    col_info += f" - range: {col['stats']['min']} to {col['stats']['max']}"
            columns_info.append(col_info)

        return f"""You are a data analyst creating query rules for a dataset.

Available columns:
{chr(10).join(columns_info)}

User instruction: {instruction}

Create query rules based on this instruction. Rules can:
1. Filter data (add WHERE clause conditions)
2. Exclude columns (hide from SELECT)
3. Require conditions (always apply filters)

Output ONLY a JSON array of rule objects with these fields:
- name: string (descriptive name)
- description: string (what the rule does)
- rule_type: string (one of: "filter", "exclude_column", "always_include")
- condition: object (rule parameters)
- is_active: boolean (default true)
- priority: number (higher = applied first, default 0)

For filter/always_include rules, condition should have:
- column: string (column name)
- operator: string (=, !=, >, <, >=, <=, IN, BETWEEN)
- value: string/number/array (the value to compare)

For exclude_column rules, condition should have:
- column: string (column name to exclude)

Example output:
[
  {{
    "name": "Only Active Records",
    "description": "Filter to show only active status",
    "rule_type": "filter",
    "condition": {{"column": "status", "operator": "=", "value": "active"}},
    "is_active": true,
    "priority": 10
  }},
  {{
    "name": "Hide SSN",
    "description": "Exclude sensitive SSN column",
    "rule_type": "exclude_column",
    "condition": {{"column": "ssn"}},
    "is_active": true,
    "priority": 0
  }}
]

JSON output:"""

    async def _call_ai(self, prompt: str) -> str:
        """Call OpenRouter API"""
        print(f"🤖 Calling AI for metadata/rules generation with model: {settings.OPENROUTER_MODEL}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1
                }
            )

            if response.status_code != 200:
                raise Exception(f"AI API error (status {response.status_code}): {response.text}")

            result = response.json()

            if 'error' in result:
                raise Exception(f"AI API error: {result['error']}")

            if 'choices' not in result or len(result['choices']) == 0:
                raise Exception(f"Unexpected API response: {json.dumps(result)}")

            return result['choices'][0]['message']['content']

    def _parse_metadata_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response to extract metadata updates"""
        # Clean up response
        response = response.strip()

        # Remove markdown code blocks if present
        if response.startswith('```'):
            response = response.split('```')[1]
            if response.startswith('json'):
                response = response[4:]

        response = response.strip()

        try:
            metadata = json.loads(response)
            return metadata
        except json.JSONDecodeError as e:
            print(f"Failed to parse AI response: {response}")
            raise Exception(f"Failed to parse AI response: {str(e)}")

    def _parse_rules_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response to extract query rules"""
        # Clean up response
        response = response.strip()

        # Remove markdown code blocks if present
        if response.startswith('```'):
            response = response.split('```')[1]
            if response.startswith('json'):
                response = response[4:]

        response = response.strip()

        try:
            rules = json.loads(response)
            if not isinstance(rules, list):
                rules = [rules]
            return rules
        except json.JSONDecodeError as e:
            print(f"Failed to parse AI response: {response}")
            raise Exception(f"Failed to parse AI response: {str(e)}")
