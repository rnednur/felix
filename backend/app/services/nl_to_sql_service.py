import json
import httpx
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.storage_service import StorageService
from app.services.embedding_service import EmbeddingService
from app.services.rule_service import RuleService


class NLToSQLService:
    """Convert natural language to SQL using LLM"""

    def __init__(self, db: Session = None):
        self.storage_service = StorageService()
        self.embedding_service = EmbeddingService()
        self.db = db
        self.rule_service = RuleService(db) if db else None

    async def generate_sql(self, nl_query: str, dataset_id: str) -> Dict[str, Any]:
        """Generate SQL from natural language query"""
        # Load schema and embeddings
        schema = self.storage_service.load_schema(dataset_id)
        embedding_path = f"{settings.EMBEDDINGS_DIR}/{dataset_id}_embeddings.bin"

        # Retrieve relevant columns
        relevant_cols = self.embedding_service.search_similar_columns(
            nl_query, embedding_path, schema, top_k=10
        )

        # Build prompt (includes metadata and rules context)
        prompt = self.build_prompt(nl_query, schema, relevant_cols, dataset_id)

        # Call OpenRouter
        sql = await self.call_openrouter(prompt)

        # Validate and add guardrails
        validated_sql = self.apply_guardrails(sql)

        # Apply query rules (filters, exclusions, etc.)
        if self.rule_service:
            validated_sql = self.rule_service.apply_rules_to_sql(validated_sql, dataset_id)

        return {
            'sql': validated_sql,
            'retrieved_columns': [col['column']['name'] for col in relevant_cols],
            'confidence': self.estimate_confidence(relevant_cols)
        }

    def build_prompt(self, nl_query: str, schema: dict, relevant_cols: list, dataset_id: str = None) -> str:
        """Build prompt for LLM"""
        # Format relevant columns
        cols_info = []
        date_columns = []

        for item in relevant_cols:
            col = item['column']
            col_desc = f"- \"{col['name']}\" ({col['dtype']})"

            # Track date/time columns
            if 'date' in col['name'].lower() or 'time' in col['name'].lower():
                date_columns.append(col['name'])

            if 'stats' in col:
                if 'top_values' in col['stats']:
                    examples = [v[0] for v in col['stats']['top_values'][:3]]
                    col_desc += f" - examples: {examples}"
                elif 'min' in col['stats'] and 'max' in col['stats']:
                    col_desc += f" - range: {col['stats']['min']} to {col['stats']['max']}"
            cols_info.append(col_desc)

        # Build date handling instructions
        date_instructions = ""
        if date_columns:
            date_instructions = f"""
IMPORTANT - Date/Time Handling:
The following columns contain dates in format "MM/DD/YYYY HH:MM:SS AM/PM": {', '.join([f'"{c}"' for c in date_columns])}
- To convert to date: strptime("{col}", '%m/%d/%Y %I:%M:%S %p')
- To extract year: CAST(strftime(strptime("{col}", '%m/%d/%Y %I:%M:%S %p'), '%Y') AS INTEGER)
- To filter dates: strptime("{col}", '%m/%d/%Y %I:%M:%S %p') >= strptime('01/01/2020 12:00:00 AM', '%m/%d/%Y %I:%M:%S %p')
- To get min/max dates: Use strptime() to convert before MIN/MAX
- For date ranges: Always use strptime() to parse the string dates

Example: SELECT MIN(strptime("Date Rptd", '%m/%d/%Y %I:%M:%S %p')) as min_date FROM dataset
"""

        # Get metadata and rules context
        rules_context = ""
        if self.rule_service and dataset_id:
            rules_context = self.rule_service.get_rules_context_for_llm(dataset_id)

        return f"""You are a SQL expert. Generate a DuckDB SQL query for the following request.

Dataset Schema (most relevant columns):
{chr(10).join(cols_info)}

All available columns:
{', '.join([f'"{c["name"]}"' for c in schema['columns']])}

{date_instructions}
{rules_context}

User Request: {nl_query}

Rules:
- This is DuckDB SQL (NOT MySQL or PostgreSQL syntax)
- Use table name "dataset"
- ALWAYS use double quotes (") for column names, never backticks (`)
- Example: SELECT "Order ID", "Customer Name" FROM dataset
- For date columns, ALWAYS use strptime() to parse the string format
- Add LIMIT 1000 unless user specifies otherwise
- No cartesian joins
- Use column names exactly as shown in the schema
- For aggregations, include GROUP BY clause
- Return only the SQL query, no explanation or markdown formatting

SQL Query:"""

    async def call_openrouter(self, prompt: str) -> str:
        """Call OpenRouter API"""
        print(f"🤖 Calling OpenRouter API with model: {settings.OPENROUTER_MODEL}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )

            # Check response status
            if response.status_code != 200:
                error_detail = response.text
                raise Exception(f"OpenRouter API error (status {response.status_code}): {error_detail}")

            result = response.json()

            # Check for error in response
            if 'error' in result:
                raise Exception(f"OpenRouter API error: {result['error']}")

            # Extract SQL from response
            if 'choices' not in result or len(result['choices']) == 0:
                raise Exception(f"Unexpected API response format: {json.dumps(result)}")

            return result['choices'][0]['message']['content']

    def apply_guardrails(self, sql: str) -> str:
        """Apply safety guardrails to SQL"""
        # Strip markdown code blocks
        sql = sql.replace('```sql', '').replace('```', '').strip()

        # Remove any leading/trailing whitespace
        sql = sql.strip()

        # Fix backticks - DuckDB uses double quotes, not backticks
        sql = sql.replace('`', '"')

        # Add LIMIT if not present
        if 'LIMIT' not in sql.upper():
            sql += ' LIMIT 1000'

        return sql

    def estimate_confidence(self, relevant_cols: list) -> float:
        """Estimate confidence based on column similarity scores"""
        if not relevant_cols:
            return 0.0

        # Average of top similarities
        similarities = [col['similarity'] for col in relevant_cols[:3]]
        return sum(similarities) / len(similarities)
