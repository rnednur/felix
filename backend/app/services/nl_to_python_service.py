import json
import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.services.storage_service import StorageService
from app.services.embedding_service import EmbeddingService
from app.services.nl_to_sql_service import NLToSQLService


class AnalysisMode:
    """Analysis mode types"""
    SQL = "sql"
    PYTHON = "python"
    ML = "ml"
    WORKFLOW = "workflow"
    STATS = "stats"


class NLToPythonService:
    """Convert natural language to executable Python code for advanced analytics"""

    def __init__(self):
        self.storage_service = StorageService()
        self.embedding_service = EmbeddingService()
        self._nl_to_sql_service = None  # Lazy load to avoid model download on init

    def detect_mode(self, nl_query: str) -> str:
        """Detect which analysis mode to use based on query content"""
        query_lower = nl_query.lower()

        # ML keywords
        ml_keywords = [
            'predict', 'model', 'forecast', 'train', 'machine learning',
            'regression', 'classification', 'cluster', 'random forest',
            'decision tree', 'neural', 'xgboost', 'accuracy'
        ]

        # Multi-step workflow keywords
        workflow_keywords = [
            'then', 'after that', 'first', 'next', 'finally',
            'step 1', 'step 2', 'and then', 'followed by'
        ]

        # Statistical analysis keywords
        stats_keywords = [
            'correlation', 'significance', 'test', 'distribution',
            'p-value', 'hypothesis', 'normal', 'variance', 'standard deviation',
            'outlier', 'anomaly', 'trend'
        ]

        # Python-specific operations
        python_keywords = [
            'clean', 'transform', 'pivot', 'melt', 'merge',
            'impute', 'normalize', 'scale', 'encode'
        ]

        if any(kw in query_lower for kw in ml_keywords):
            return AnalysisMode.ML
        elif any(kw in query_lower for kw in workflow_keywords):
            return AnalysisMode.WORKFLOW
        elif any(kw in query_lower for kw in stats_keywords):
            return AnalysisMode.STATS
        elif any(kw in query_lower for kw in python_keywords):
            return AnalysisMode.PYTHON
        else:
            return AnalysisMode.SQL  # Default to existing SQL behavior

    async def generate_python_code(
        self,
        nl_query: str,
        dataset_id: str,
        mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate Python code from natural language query"""

        # Auto-detect mode if not provided
        if mode is None:
            mode = self.detect_mode(nl_query)

        # Load schema and embeddings
        schema = self.storage_service.load_schema(dataset_id)
        embedding_path = f"{settings.EMBEDDINGS_DIR}/{dataset_id}_embeddings.bin"

        # Retrieve relevant columns
        relevant_cols = self.embedding_service.search_similar_columns(
            nl_query, embedding_path, schema, top_k=15
        )

        # Generate DuckDB SQL query for efficient data loading
        # This filters/aggregates data at SQL level before Python processing
        duckdb_query = None
        try:
            # Lazy load NL-to-SQL service (avoids model download on init)
            if self._nl_to_sql_service is None:
                self._nl_to_sql_service = NLToSQLService()

            sql_result = await self._nl_to_sql_service.generate_sql(nl_query, dataset_id)
            raw_sql = sql_result['sql']

            # Keep the SQL query as-is with "FROM dataset"
            # The code executor creates a DuckDB view named "dataset" that matches this
            duckdb_query = raw_sql

        except Exception as e:
            # If SQL generation fails, fall back to loading entire dataset
            print(f"Warning: DuckDB query generation failed: {e}")
            duckdb_query = "SELECT * FROM dataset"  # Fallback - use entire dataset view

        # Build prompt based on mode (now includes DuckDB query)
        prompt = self.build_python_prompt(nl_query, schema, relevant_cols, mode, duckdb_query)

        # Call OpenRouter
        code = await self.call_openrouter(prompt)

        # Parse workflow steps if applicable
        steps = self.parse_workflow(code, mode)

        return {
            'code': code,
            'mode': mode,
            'retrieved_columns': [col['column']['name'] for col in relevant_cols],
            'duckdb_query': duckdb_query,
            'steps': steps,
            'requires_execution': True,
            'estimated_runtime': self.estimate_runtime(code, mode)
        }

    def build_python_prompt(
        self,
        nl_query: str,
        schema: dict,
        relevant_cols: list,
        mode: str,
        duckdb_query: str
    ) -> str:
        """Build prompt for Python code generation"""

        # Format relevant columns
        cols_info = []
        for item in relevant_cols:
            col = item['column']
            col_desc = f"- \"{col['name']}\" ({col['dtype']})"

            if 'stats' in col:
                if 'top_values' in col['stats']:
                    examples = [v[0] for v in col['stats']['top_values'][:3]]
                    col_desc += f" - examples: {examples}"
                elif 'min' in col['stats'] and 'max' in col['stats']:
                    col_desc += f" - range: {col['stats']['min']} to {col['stats']['max']}"
            cols_info.append(col_desc)

        # Mode-specific instructions
        mode_instructions = self.get_mode_instructions(mode)

        return f"""You are a Python data analysis expert. Generate executable Python code for the following request.

Dataset Schema (most relevant columns):
{chr(10).join(cols_info)}

All available columns:
{', '.join([f'"{c["name"]}"' for c in schema['columns']])}

User Request: {nl_query}

{mode_instructions}

CRITICAL REQUIREMENTS:
1. Load data efficiently using DuckDB (pre-configured connection with optimized query):
   ```python
   # A DuckDB connection 'duckdb_conn' is already available with a 'dataset' view
   # The following optimized query filters data at SQL level (much faster than pandas):
   df = duckdb_conn.execute("{duckdb_query}").df()
   ```
   Note: You can also use the pre-loaded 'df' variable, but DuckDB query is faster for filtering
2. Store final output in a variable called 'result' (must be JSON-serializable)
3. Use only these libraries: pandas, numpy, scikit-learn, scipy, statsmodels, matplotlib, seaborn, duckdb
4. Include clear comments explaining each major step
5. Handle missing values and errors gracefully
6. For visualizations:
   - Save plots as base64-encoded PNG
   - Format: {{'data': 'base64_string_here', 'type': 'plot_type', 'caption': 'description'}}
   - Use this code to save plots:
     ```python
     import base64
     from io import BytesIO
     buffer = BytesIO()
     plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
     buffer.seek(0)
     plot_base64 = base64.b64encode(buffer.read()).decode()
     plt.close()
     ```
7. Return result as a dictionary with keys: 'summary', 'data', 'metrics', 'visualizations'

Example result format:
```python
result = {{
    'summary': 'Brief description of findings',
    'data': df_result.to_dict('records'),  # or list of values
    'metrics': {{'r2_score': 0.85, 'rmse': 12.3}},  # if applicable
    'visualizations': [
        {{'data': plot_base64, 'type': 'scatter', 'caption': 'Actual vs Predicted'}}
    ]  # base64 string in 'data' field, NOT 'base64'
}}
```

Generate only the Python code, no markdown formatting or explanations outside comments.

Python Code:"""

    def get_mode_instructions(self, mode: str) -> str:
        """Get mode-specific instructions for prompt"""

        if mode == AnalysisMode.ML:
            return """MODE: Machine Learning

Required steps:
1. Feature selection and preprocessing
2. Train/test split (80/20)
3. Model training (choose appropriate algorithm)
4. Model evaluation (metrics: R², RMSE for regression; accuracy, precision, recall for classification)
5. Feature importance (if applicable)
6. Prediction examples

Store trained model in 'model' variable for potential saving."""

        elif mode == AnalysisMode.STATS:
            return """MODE: Statistical Analysis

Include:
1. Descriptive statistics
2. Appropriate statistical tests (t-test, chi-square, ANOVA, etc.)
3. Correlation analysis if relevant
4. P-values and confidence intervals
5. Interpretation of results
6. Visualizations (histograms, scatter plots, box plots as needed)"""

        elif mode == AnalysisMode.WORKFLOW:
            return """MODE: Multi-Step Workflow

Break analysis into clear steps:
1. Define each step as a separate function
2. Chain functions together
3. Comment each step clearly
4. Store intermediate results
5. Return combined results showing progression"""

        else:  # PYTHON mode
            return """MODE: Python Data Analysis

Focus on:
1. Data cleaning and transformation
2. Aggregations and calculations
3. Clear, efficient pandas operations
4. Meaningful output format"""

    async def call_openrouter(self, prompt: str) -> str:
        """Call OpenRouter API for code generation"""
        print(f"🤖 [Python] Calling OpenRouter API with model: {settings.OPENROUTER_MODEL}")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3  # Lower temperature for more deterministic code
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

            # Extract code from response
            if 'choices' not in result or len(result['choices']) == 0:
                raise Exception(f"Unexpected API response format: {json.dumps(result)}")

            code = result['choices'][0]['message']['content']

            # Clean up code (remove markdown if present)
            code = code.replace('```python', '').replace('```', '').strip()

            return code

    def parse_workflow(self, code: str, mode: str) -> List[Dict[str, Any]]:
        """Parse code into workflow steps"""

        if mode != AnalysisMode.WORKFLOW:
            return [{
                'step': 1,
                'description': self.extract_description_from_code(code),
                'code': code
            }]

        # For workflow mode, try to identify separate steps
        # This is a simple heuristic - could be improved with AST parsing
        steps = []
        lines = code.split('\n')
        current_step = []
        step_num = 1

        for line in lines:
            # Detect step boundaries (comments like "# Step 1:", function definitions, etc.)
            if line.strip().startswith('# Step') or line.strip().startswith('def '):
                if current_step:
                    steps.append({
                        'step': step_num,
                        'description': self.extract_step_description(current_step),
                        'code': '\n'.join(current_step)
                    })
                    step_num += 1
                    current_step = []
            current_step.append(line)

        # Add final step
        if current_step:
            steps.append({
                'step': step_num,
                'description': self.extract_step_description(current_step),
                'code': '\n'.join(current_step)
            })

        return steps if steps else [{'step': 1, 'description': 'Analysis', 'code': code}]

    def extract_description_from_code(self, code: str) -> str:
        """Extract description from code comments"""
        lines = code.split('\n')
        for line in lines:
            if line.strip().startswith('#') and len(line.strip()) > 2:
                return line.strip()[1:].strip()
        return "Data analysis"

    def extract_step_description(self, code_lines: List[str]) -> str:
        """Extract description from step code"""
        for line in code_lines:
            if line.strip().startswith('#'):
                desc = line.strip()[1:].strip()
                if len(desc) > 5:  # Meaningful comment
                    return desc
        return "Processing step"

    def estimate_runtime(self, code: str, mode: str) -> str:
        """Estimate approximate runtime based on code complexity"""

        # Simple heuristic based on operations
        has_ml = any(kw in code for kw in ['fit(', 'train', 'GridSearchCV'])
        has_loops = 'for ' in code or 'while ' in code
        has_groupby = 'groupby' in code

        if has_ml:
            return "30-120 seconds (ML model training)"
        elif has_loops and has_groupby:
            return "10-30 seconds (complex aggregations)"
        elif has_groupby:
            return "5-10 seconds (aggregations)"
        else:
            return "1-5 seconds (simple operations)"

    def validate_code_safety(self, code: str) -> Dict[str, Any]:
        """Validate that code is safe to execute"""

        dangerous_patterns = [
            'import os', 'import sys', 'import subprocess',
            'eval(', 'exec(', '__import__',
            'open(', 'write(', 'delete',
            'rmdir', 'unlink', 'remove'
        ]

        issues = []
        for pattern in dangerous_patterns:
            if pattern in code:
                issues.append(f"Potentially dangerous pattern detected: {pattern}")

        return {
            'is_safe': len(issues) == 0,
            'issues': issues
        }
