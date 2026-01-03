import json
import httpx
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.core.config import settings
from app.services.storage_service import StorageService
from app.services.embedding_service import EmbeddingService
from app.services.rule_service import RuleService
from app.models.dataset import DatasetGroup, DatasetGroupMembership


class NLToSQLService:
    """Convert natural language to SQL using LLM"""

    def __init__(self, db: Session = None):
        self.storage_service = StorageService()
        self.embedding_service = EmbeddingService()
        self.db = db
        self.rule_service = RuleService(db) if db else None

    async def generate_sql(
        self,
        nl_query: str,
        dataset_id: Optional[str] = None,
        group_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate SQL from natural language query

        Args:
            nl_query: Natural language query
            dataset_id: Single dataset ID (mutually exclusive with group_id)
            group_id: Dataset group ID for multi-dataset queries
        """
        if dataset_id and group_id:
            raise ValueError("Cannot specify both dataset_id and group_id")
        if not dataset_id and not group_id:
            raise ValueError("Must specify either dataset_id or group_id")

        if group_id:
            return await self._generate_sql_for_group(nl_query, group_id)
        else:
            return await self._generate_sql_for_dataset(nl_query, dataset_id)

    async def _generate_sql_for_dataset(self, nl_query: str, dataset_id: str) -> Dict[str, Any]:
        """Generate SQL for a single dataset with retry on errors"""
        # Load schema and embeddings
        schema = self.storage_service.load_schema(dataset_id)
        embedding_path = f"{settings.EMBEDDINGS_DIR}/{dataset_id}_embeddings.bin"

        # Retrieve relevant columns
        relevant_cols = self.embedding_service.search_similar_columns(
            nl_query, embedding_path, schema, top_k=10
        )

        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                # Build prompt (includes metadata and rules context)
                if attempt == 0:
                    # First attempt: normal prompt
                    prompt = self.build_prompt(nl_query, schema, relevant_cols, dataset_id)
                else:
                    # Retry with error context
                    prompt = self.build_retry_prompt(nl_query, schema, relevant_cols, dataset_id, validated_sql, last_error)

                # Call OpenRouter
                sql = await self.call_openrouter(prompt)

                # Validate and add guardrails
                validated_sql = self.apply_guardrails(sql)

                # Apply query rules (filters, exclusions, etc.)
                if self.rule_service:
                    validated_sql = self.rule_service.apply_rules_to_sql(validated_sql, dataset_id)

                # Test the SQL by executing it (import DuckDBService here to avoid circular import)
                from app.services.duckdb_service import DuckDBService
                duckdb_service = DuckDBService()

                # Try executing the query to validate syntax
                duckdb_service.execute_query(validated_sql, dataset_id=dataset_id)

                # If we get here, SQL is valid
                retry_info = {'attempted': attempt + 1} if attempt > 0 else {}

                return {
                    'sql': validated_sql,
                    'retrieved_columns': [col['column']['name'] for col in relevant_cols],
                    'confidence': self.estimate_confidence(relevant_cols),
                    **retry_info
                }

            except Exception as e:
                last_error = str(e)
                print(f"🔄 SQL attempt {attempt + 1} failed: {last_error}")

                if attempt == max_retries - 1:
                    # Final attempt failed
                    return {
                        'sql': validated_sql if 'validated_sql' in locals() else None,
                        'retrieved_columns': [col['column']['name'] for col in relevant_cols],
                        'confidence': self.estimate_confidence(relevant_cols),
                        'error': last_error,
                        'attempts': max_retries
                    }

                # Continue to next retry
                continue

        # Should never reach here, but return error if we do
        return {
            'sql': None,
            'retrieved_columns': [col['column']['name'] for col in relevant_cols],
            'confidence': self.estimate_confidence(relevant_cols),
            'error': 'Max retries exceeded',
            'attempts': max_retries
        }

    async def _generate_sql_for_group(self, nl_query: str, group_id: str) -> Dict[str, Any]:
        """Generate SQL for a dataset group (multi-table query) with retry on errors"""
        if not self.db:
            raise ValueError("Database session required for group queries")

        # Get group with memberships
        group = self.db.query(DatasetGroup).filter(
            DatasetGroup.id == group_id,
            DatasetGroup.deleted_at.is_(None)
        ).first()

        if not group:
            raise ValueError(f"Dataset group {group_id} not found")

        if not group.memberships:
            raise ValueError(f"Dataset group {group_id} has no datasets")

        # Load all schemas and embeddings
        dataset_schemas = []
        all_relevant_cols = []

        for membership in sorted(group.memberships, key=lambda m: m.display_order):
            dataset_id = membership.dataset_id
            alias = membership.alias or membership.dataset.name

            schema = self.storage_service.load_schema(dataset_id)
            embedding_path = f"{settings.EMBEDDINGS_DIR}/{dataset_id}_embeddings.bin"

            # Search relevant columns in this dataset
            relevant_cols = self.embedding_service.search_similar_columns(
                nl_query, embedding_path, schema, top_k=5
            )

            dataset_schemas.append({
                'dataset_id': dataset_id,
                'alias': alias,
                'schema': schema,
                'relevant_cols': relevant_cols
            })
            all_relevant_cols.extend(relevant_cols)

        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                # Build multi-table prompt
                if attempt == 0:
                    # First attempt: normal prompt
                    prompt = self.build_group_prompt(nl_query, dataset_schemas)
                else:
                    # Retry with error context
                    prompt = self.build_group_retry_prompt(nl_query, dataset_schemas, validated_sql, last_error)

                # Call OpenRouter
                sql = await self.call_openrouter(prompt)

                # Validate and add guardrails
                validated_sql = self.apply_guardrails_group(sql)

                # Test the SQL by executing it
                from app.services.duckdb_service import DuckDBService
                duckdb_service = DuckDBService()

                # Prepare dataset configs for multi-table query
                dataset_configs = [
                    {'dataset_id': ds['dataset_id'], 'alias': ds['alias']}
                    for ds in dataset_schemas
                ]

                # Try executing the query to validate syntax
                duckdb_service.execute_query(validated_sql, dataset_configs=dataset_configs)

                # If we get here, SQL is valid
                retry_info = {'attempted': attempt + 1} if attempt > 0 else {}

                return {
                    'sql': validated_sql,
                    'retrieved_columns': [col['column']['name'] for col in all_relevant_cols],
                    'confidence': self.estimate_confidence(all_relevant_cols),
                    'datasets_used': [ds['alias'] for ds in dataset_schemas],
                    **retry_info
                }

            except Exception as e:
                last_error = str(e)
                print(f"🔄 Group SQL attempt {attempt + 1} failed: {last_error}")

                if attempt == max_retries - 1:
                    # Final attempt failed
                    return {
                        'sql': validated_sql if 'validated_sql' in locals() else None,
                        'retrieved_columns': [col['column']['name'] for col in all_relevant_cols],
                        'confidence': self.estimate_confidence(all_relevant_cols),
                        'datasets_used': [ds['alias'] for ds in dataset_schemas],
                        'error': last_error,
                        'attempts': max_retries
                    }

                # Continue to next retry
                continue

        # Should never reach here, but return error if we do
        return {
            'sql': None,
            'retrieved_columns': [col['column']['name'] for col in all_relevant_cols],
            'confidence': self.estimate_confidence(all_relevant_cols),
            'datasets_used': [ds['alias'] for ds in dataset_schemas],
            'error': 'Max retries exceeded',
            'attempts': max_retries
        }

    def build_prompt(self, nl_query: str, schema: dict, relevant_cols: list, dataset_id: str = None) -> str:
        """Build prompt for LLM"""
        # Format relevant columns
        cols_info = []
        date_columns = []

        for item in relevant_cols:
            col = item['column']
            col_desc = f"- \"{col['name']}\" ({col['dtype']})"

            # Track date/time columns that are stored as STRINGS (need strptime)
            # Only add to date_columns if it's VARCHAR/STRING type with date-like name
            dtype_lower = col['dtype'].lower()
            is_string_type = 'varchar' in dtype_lower or 'string' in dtype_lower or 'text' in dtype_lower
            is_date_name = 'date' in col['name'].lower() or 'time' in col['name'].lower()

            if is_string_type and is_date_name:
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
The following columns are STRING columns containing dates in format "MM/DD/YYYY HH:MM:SS AM/PM": {', '.join([f'"{c}"' for c in date_columns])}
For THESE STRING COLUMNS ONLY, use strptime() to parse them:
- To convert to date: strptime("{col}", '%m/%d/%Y %I:%M:%S %p')
- To extract year: CAST(strftime(strptime("{col}", '%m/%d/%Y %I:%M:%S %p'), '%Y') AS INTEGER)
- To filter dates: strptime("{col}", '%m/%d/%Y %I:%M:%S %p') >= strptime('01/01/2020 12:00:00 AM', '%m/%d/%Y %I:%M:%S %p')

For columns that are already DATE or TIMESTAMP type, DO NOT use strptime():
- Use them directly: SELECT "date_column" FROM dataset WHERE "date_column" >= '2020-01-01'
- Extract year: CAST(strftime("date_column", '%Y') AS INTEGER)

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
- Check column data types: use strptime() ONLY for STRING columns with dates, not for DATE/TIMESTAMP columns
- Add LIMIT 1000 unless user specifies otherwise
- No cartesian joins
- Use column names exactly as shown in the schema
- For aggregations, include GROUP BY clause
- Return only the SQL query, no explanation or markdown formatting

SQL Query:"""

    def build_retry_prompt(self, nl_query: str, schema: dict, relevant_cols: list, dataset_id: str, failed_sql: str, error: str) -> str:
        """Build retry prompt with error context for SQL correction"""
        # Format relevant columns
        cols_info = []
        date_columns = []

        for item in relevant_cols:
            col = item['column']
            col_desc = f"- \"{col['name']}\" ({col['dtype']})"

            # Track date/time columns that are stored as STRINGS (need strptime)
            # Only add to date_columns if it's VARCHAR/STRING type with date-like name
            dtype_lower = col['dtype'].lower()
            is_string_type = 'varchar' in dtype_lower or 'string' in dtype_lower or 'text' in dtype_lower
            is_date_name = 'date' in col['name'].lower() or 'time' in col['name'].lower()

            if is_string_type and is_date_name:
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
The following columns are STRING columns containing dates in format "MM/DD/YYYY HH:MM:SS AM/PM": {', '.join([f'"{c}"' for c in date_columns])}
For THESE STRING COLUMNS ONLY, use strptime() to parse them:
- To convert to date: strptime("{col}", '%m/%d/%Y %I:%M:%S %p')
- To extract year: CAST(strftime(strptime("{col}", '%m/%d/%Y %I:%M:%S %p'), '%Y') AS INTEGER)
- To filter dates: strptime("{col}", '%m/%d/%Y %I:%M:%S %p') >= strptime('01/01/2020 12:00:00 AM', '%m/%d/%Y %I:%M:%S %p')

For columns that are already DATE or TIMESTAMP type, DO NOT use strptime():
- Use them directly: SELECT "date_column" FROM dataset WHERE "date_column" >= '2020-01-01'
- Extract year: CAST(strftime("date_column", '%Y') AS INTEGER)
"""

        # Get metadata and rules context
        rules_context = ""
        if self.rule_service and dataset_id:
            rules_context = self.rule_service.get_rules_context_for_llm(dataset_id)

        return f"""You are a SQL expert. The following SQL query FAILED with an error. Fix it.

Dataset Schema (most relevant columns):
{chr(10).join(cols_info)}

All available columns:
{', '.join([f'"{c["name"]}"' for c in schema['columns']])}

{date_instructions}
{rules_context}

User Request: {nl_query}

PREVIOUS FAILED SQL:
{failed_sql}

ERROR MESSAGE:
{error}

Fix the SQL query to address the error. Common issues:
- Column names must use double quotes (") not backticks (`)
- Check column names exist in schema
- Check column data types: use strptime() ONLY for STRING columns with dates, not for DATE/TIMESTAMP columns
- Ensure proper DuckDB syntax (not MySQL/PostgreSQL)
- Add LIMIT 1000 unless user specifies otherwise

Rules:
- This is DuckDB SQL (NOT MySQL or PostgreSQL syntax)
- Use table name "dataset"
- ALWAYS use double quotes (") for column names, never backticks (`)
- Return only the fixed SQL query, no explanation or markdown formatting

FIXED SQL Query:"""

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

    def build_group_prompt(self, nl_query: str, dataset_schemas: List[Dict[str, Any]]) -> str:
        """Build prompt for multi-dataset queries"""
        tables_info = []

        for ds in dataset_schemas:
            alias = ds['alias']
            schema = ds['schema']
            relevant_cols = ds['relevant_cols']

            # Format relevant columns for this table
            cols_info = []
            for item in relevant_cols:
                col = item['column']
                col_desc = f"  - \"{col['name']}\" ({col['dtype']})"
                if 'stats' in col and 'top_values' in col['stats']:
                    examples = [v[0] for v in col['stats']['top_values'][:3]]
                    col_desc += f" - examples: {examples}"
                cols_info.append(col_desc)

            table_desc = f"""Table: "{alias}"
Relevant columns:
{chr(10).join(cols_info)}
All columns: {', '.join([f'"{c["name"]}"' for c in schema['columns']])}
"""
            tables_info.append(table_desc)

        return f"""You are a SQL expert. Generate a DuckDB SQL query that works with multiple tables/datasets.

Available Tables:
{chr(10).join(tables_info)}

User Request: {nl_query}

Rules:
- This is DuckDB SQL (NOT MySQL or PostgreSQL syntax)
- ALWAYS use double quotes (") for BOTH table names AND column names
- Table names must be quoted: e.g., SELECT * FROM "studentVle" (NOT FROM studentVle)
- Column names must be quoted: e.g., "Order ID" (NOT `Order ID`)
- Each dataset is loaded as a separate table with the alias shown
- Use appropriate JOINs when data from multiple tables is needed
- Check column data types: use strptime() ONLY for STRING columns with dates, not for DATE/TIMESTAMP columns
- Add LIMIT 1000 unless user specifies otherwise
- Qualify column names with table aliases (e.g., "sales"."Order ID")
- For aggregations, include GROUP BY clause
- Return only the SQL query, no explanation or markdown formatting

SQL Query:"""

    def build_group_retry_prompt(self, nl_query: str, dataset_schemas: List[Dict[str, Any]], failed_sql: str, error: str) -> str:
        """Build retry prompt for multi-dataset queries"""
        tables_info = []

        for ds in dataset_schemas:
            alias = ds['alias']
            schema = ds['schema']
            relevant_cols = ds['relevant_cols']

            # Format relevant columns for this table
            cols_info = []
            for item in relevant_cols:
                col = item['column']
                col_desc = f"  - \"{col['name']}\" ({col['dtype']})"
                if 'stats' in col and 'top_values' in col['stats']:
                    examples = [v[0] for v in col['stats']['top_values'][:3]]
                    col_desc += f" - examples: {examples}"
                cols_info.append(col_desc)

            table_desc = f"""Table: "{alias}"
Relevant columns:
{chr(10).join(cols_info)}
All columns: {', '.join([f'"{c["name"]}"' for c in schema['columns']])}
"""
            tables_info.append(table_desc)

        return f"""You are a SQL expert. The following multi-table SQL query FAILED with an error. Fix it.

Available Tables:
{chr(10).join(tables_info)}

User Request: {nl_query}

PREVIOUS FAILED SQL:
{failed_sql}

ERROR MESSAGE:
{error}

Fix the SQL query to address the error. Common issues:
- BOTH table names AND column names must use double quotes (")
- Table names: "studentVle" NOT studentVle (unquoted table names are treated as schema names!)
- Column names: "Order ID" NOT `Order ID`
- Check column names exist in their respective tables
- Qualify column names with table aliases (e.g., "sales"."Order ID")
- Ensure proper JOINs if combining tables
- Use correct DuckDB syntax (not MySQL/PostgreSQL)
- Check column data types: use strptime() ONLY for STRING columns with dates, not for DATE/TIMESTAMP columns

Rules:
- This is DuckDB SQL (NOT MySQL or PostgreSQL syntax)
- ALWAYS quote table names: SELECT * FROM "tableName" (NOT FROM tableName)
- ALWAYS quote column names: "Column Name" (NOT `Column Name`)
- Qualify column names with quoted table aliases: "table"."column"
- Add LIMIT 1000 unless user specifies otherwise
- Return only the fixed SQL query, no explanation or markdown formatting

FIXED SQL Query:"""

    def apply_guardrails_group(self, sql: str) -> str:
        """Apply safety guardrails to multi-table SQL"""
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
