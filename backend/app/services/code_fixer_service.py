"""
Service to automatically fix common code generation errors
"""
import re
import httpx
import json
from typing import Dict, Any, Optional
from app.core.config import settings


class CodeFixerService:
    """Automatically fix common LLM code generation errors"""

    def __init__(self):
        self.common_fixes = [
            self._fix_label_encoder_mixed_types,
            self._fix_numpy_read_parquet,
            self._fix_missing_column_quotes,
            self._fix_sklearn_imports,
            self._fix_data_loading
        ]

    async def attempt_fix_with_llm(self, code: str, error: str, error_trace: str = None) -> Optional[str]:
        """Use LLM to intelligently fix the code based on error"""

        print(f"🔧 Attempting to fix code error with LLM...")

        # Build prompt for LLM
        prompt = f"""You are a Python code debugger. The following code failed with an error. Fix the code.

ORIGINAL CODE:
```python
{code}
```

ERROR MESSAGE:
{error}

{f'STACK TRACE:{error_trace}' if error_trace else ''}

REQUIREMENTS:
1. Return ONLY the fixed Python code, no explanations
2. Keep the same structure and variable names
3. The code must store final output in 'result' variable
4. Fix the specific error without changing the logic
5. Do not add markdown formatting

FIXED CODE:"""

        try:
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
                        "temperature": 0.1  # Very low temperature for precise fixes
                    }
                )

                if response.status_code != 200:
                    print(f"❌ LLM fix failed: HTTP {response.status_code}")
                    return None

                result = response.json()

                if 'choices' not in result or len(result['choices']) == 0:
                    print(f"❌ LLM fix failed: Unexpected response format")
                    return None

                fixed_code = result['choices'][0]['message']['content']

                # Clean up code (remove markdown if present)
                fixed_code = fixed_code.replace('```python', '').replace('```', '').strip()

                print(f"✅ LLM generated fixed code")
                return fixed_code

        except Exception as e:
            print(f"❌ LLM fix error: {e}")
            return None

    def attempt_fix(self, code: str, error: str) -> Optional[str]:
        """Try to fix code based on error message using simple pattern matching"""

        # Try each fixer
        for fixer in self.common_fixes:
            fixed_code = fixer(code, error)
            if fixed_code != code:
                return fixed_code

        return None

    def _fix_label_encoder_mixed_types(self, code: str, error: str) -> str:
        """Fix: Encoders require their input argument must be uniformly strings or numbers"""

        if "Encoders require" not in error and "uniformly strings or numbers" not in error:
            return code

        # Convert all columns to string before label encoding
        if "LabelEncoder()" in code:
            # Find all le.fit_transform patterns
            pattern = r"(df\[['\"]\w+['\"].*?)\s*=\s*le\.fit_transform\((df\[['\"]\w+['\"])\)"

            def replace_with_string_conversion(match):
                assignment = match.group(1)
                column_ref = match.group(2)
                return f"{assignment} = le.fit_transform({column_ref}.astype(str))"

            fixed_code = re.sub(pattern, replace_with_string_conversion, code)

            if fixed_code != code:
                return fixed_code

        return code

    def _fix_numpy_read_parquet(self, code: str, error: str) -> str:
        """Fix: module 'numpy' has no attribute 'read_parquet'"""

        if "numpy" not in error or "read_parquet" not in error:
            return code

        # Replace np.read_parquet with pd.read_parquet
        fixed_code = code.replace("np.read_parquet", "pd.read_parquet")

        return fixed_code

    def _fix_missing_column_quotes(self, code: str, error: str) -> str:
        """Fix: KeyError for column names"""

        # If error is just a column name, it's likely a KeyError
        if len(error) < 50 and not any(c in error for c in ['\n', '(', ')']):
            column_name = error.strip("'\"")

            # Try to find similar column references and fix them
            # This is a simple heuristic - in production you'd want schema-aware fixing
            return code

        return code

    def _fix_sklearn_imports(self, code: str, error: str) -> str:
        """Fix common sklearn import issues"""

        if "cannot import name" in error.lower():
            # Common sklearn import fixes
            fixes = {
                "from sklearn.preprocessing import LabelEncoder":
                    "from sklearn.preprocessing import LabelEncoder, StandardScaler",
                "from sklearn.model_selection import train_test_split":
                    "from sklearn.model_selection import train_test_split, cross_val_score"
            }

            for old, new in fixes.items():
                if old in code:
                    code = code.replace(old, new)

        return code

    def _fix_data_loading(self, code: str, error: str) -> str:
        """Ensure data is loaded correctly"""

        # Make sure df is loaded from parquet_path
        if "df" in error and "not defined" in error.lower():
            if "df = pd.read_parquet(parquet_path)" not in code:
                # Add it at the beginning
                lines = code.split('\n')
                # Find first non-import, non-comment line
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('import') and not line.strip().startswith('from'):
                        insert_idx = i
                        break

                lines.insert(insert_idx, "df = pd.read_parquet(parquet_path)")
                code = '\n'.join(lines)

        return code

    def get_fix_suggestion(self, error: str) -> Optional[str]:
        """Get human-readable fix suggestion for common errors"""

        suggestions = {
            "Encoders require": "Converting categorical columns to string type before encoding",
            "numpy.*read_parquet": "Using pandas instead of numpy for reading parquet files",
            "KeyError": "Checking column names match your dataset schema",
            "cannot import": "Fixing library imports",
            "not defined": "Ensuring data is loaded properly"
        }

        for pattern, suggestion in suggestions.items():
            if re.search(pattern, error, re.IGNORECASE):
                return suggestion

        return None
