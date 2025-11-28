"""
Service for comparing multiple ML models automatically
"""
import httpx
import json
from typing import Dict, Any, List
from app.core.config import settings
from app.services.storage_service import StorageService
from app.services.embedding_service import EmbeddingService


class MLComparisonService:
    """Compare multiple ML models for a given task"""

    def __init__(self):
        self.storage_service = StorageService()
        self.embedding_service = EmbeddingService()

    async def generate_comparison_code(
        self,
        nl_query: str,
        dataset_id: str,
        model_types: List[str] = None
    ) -> Dict[str, Any]:
        """Generate Python code that trains and compares multiple models

        Args:
            nl_query: Natural language description of ML task
            dataset_id: Dataset ID
            model_types: List of model types to compare (default: auto-select based on task)
                Options: 'random_forest', 'xgboost', 'linear_regression', 'logistic_regression'
        """

        # Load schema and embeddings
        schema = self.storage_service.load_schema(dataset_id)
        embedding_path = f"{settings.EMBEDDINGS_DIR}/{dataset_id}_embeddings.bin"

        # Retrieve relevant columns
        relevant_cols = self.embedding_service.search_similar_columns(
            nl_query, embedding_path, schema, top_k=15
        )

        # Auto-detect task type (classification vs regression)
        task_type = self._detect_task_type(nl_query)

        # Auto-select models if not specified
        if model_types is None:
            if task_type == 'classification':
                model_types = ['random_forest', 'xgboost']
            else:  # regression
                model_types = ['random_forest', 'xgboost']

        # Build comparison prompt
        prompt = self._build_comparison_prompt(nl_query, schema, relevant_cols, task_type, model_types)

        # Call OpenRouter
        code = await self._call_openrouter(prompt)

        return {
            'code': code,
            'task_type': task_type,
            'models_compared': model_types,
            'retrieved_columns': [col['column']['name'] for col in relevant_cols],
            'requires_execution': True,
            'estimated_runtime': self._estimate_runtime(model_types)
        }

    def _detect_task_type(self, nl_query: str) -> str:
        """Detect if task is classification or regression"""
        query_lower = nl_query.lower()

        classification_keywords = [
            'classify', 'classification', 'predict category', 'predict class',
            'predict type', 'predict whether', 'predict if', 'binary', 'multiclass'
        ]

        if any(kw in query_lower for kw in classification_keywords):
            return 'classification'
        else:
            return 'regression'

    def _build_comparison_prompt(
        self,
        nl_query: str,
        schema: dict,
        relevant_cols: list,
        task_type: str,
        model_types: List[str]
    ) -> str:
        """Build prompt for model comparison code generation"""

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

        # Model-specific templates
        model_templates = {
            'random_forest': {
                'regression': "RandomForestRegressor(n_estimators=100, random_state=42)",
                'classification': "RandomForestClassifier(n_estimators=100, random_state=42)"
            },
            'xgboost': {
                'regression': "xgb.XGBRegressor(n_estimators=100, random_state=42)",
                'classification': "xgb.XGBClassifier(n_estimators=100, random_state=42)"
            }
        }

        models_to_train = [model_templates.get(mt, {}).get(task_type) for mt in model_types if mt in model_templates]

        metrics_code = """
# Regression metrics
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
metrics = {
    'r2_score': r2_score(y_test, y_pred),
    'rmse': mean_squared_error(y_test, y_pred, squared=False),
    'mae': mean_absolute_error(y_test, y_pred)
}
""" if task_type == 'regression' else """
# Classification metrics
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
metrics = {
    'accuracy': accuracy_score(y_test, y_pred),
    'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
    'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),
    'f1_score': f1_score(y_test, y_pred, average='weighted', zero_division=0)
}
"""

        return f"""You are a Python ML expert. Generate code that trains and compares {len(model_types)} different models.

Dataset Schema (most relevant columns):
{chr(10).join(cols_info)}

All available columns:
{', '.join([f'"{c["name"]}"' for c in schema['columns']])}

User Request: {nl_query}

Task Type: {task_type.upper()}

Models to Compare: {', '.join(model_types)}

REQUIREMENTS:
1. Load data using DuckDB (pre-configured connection available):
   ```python
   df = duckdb_conn.execute("SELECT * FROM dataset LIMIT 10000").df()
   ```

2. Train and evaluate EACH of these models:
{chr(10).join([f"   - {mt}" for mt in models_to_train])}

3. For each model:
   - Preprocess data (handle missing values, encode categoricals if needed)
   - Split into train/test (80/20)
   - Train the model
   - Make predictions
   - Calculate metrics using this code:
{metrics_code}
   - Store results in a comparison dict

4. Final result format:
```python
result = {{
    'summary': 'Comparison of {len(model_types)} models for {task_type}',
    'best_model': 'model_name_here',  # Based on primary metric
    'comparison': [
        {{
            'model': 'RandomForest',
            'metrics': {{'r2_score': 0.85, 'rmse': 12.3}} or {{'accuracy': 0.92}},
            'training_time': 2.5  # seconds
        }},
        # ... for each model
    ],
    'recommendation': 'Brief explanation of why best model was chosen'
}}
```

5. Libraries available: pandas, numpy, sklearn, xgboost, duckdb

Generate only the Python code, no markdown formatting or explanations outside comments.

Python Code:"""

    async def _call_openrouter(self, prompt: str) -> str:
        """Call OpenRouter API for code generation"""
        print(f"🤖 [ML Comparison] Calling OpenRouter API")
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
                    "temperature": 0.2  # Low temperature for consistent code
                }
            )

            if response.status_code != 200:
                raise Exception(f"OpenRouter API error: {response.status_code}")

            result = response.json()

            if 'choices' not in result or len(result['choices']) == 0:
                raise Exception(f"Unexpected API response format")

            code = result['choices'][0]['message']['content']

            # Clean up code
            code = code.replace('```python', '').replace('```', '').strip()

            return code

    def _estimate_runtime(self, model_types: List[str]) -> str:
        """Estimate runtime based on number of models"""
        num_models = len(model_types)

        if num_models == 1:
            return "30-60 seconds (single model)"
        elif num_models == 2:
            return "60-120 seconds (2 models)"
        else:
            return f"{num_models * 30}-{num_models * 60} seconds ({num_models} models)"
