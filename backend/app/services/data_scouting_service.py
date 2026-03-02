"""
Data Scouting Service

Performs intelligent data profiling to bridge the gap between what the system thinks
the data is and what it actually is. Generates contextual insights and scouting questions
to build trust early and uncover discrepancies.

Uses a hybrid approach:
- Fast rule-based pattern detection for common patterns (email, phone, URL)
- LLM-powered semantic analysis for business context and domain-specific patterns
- Intelligent triggering to balance speed and cost
"""

import math
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import re
import json
from datetime import datetime, date
from app.services.duckdb_service import DuckDBService
from app.services.storage_service import StorageService
from app.core.config import settings
import os
import hashlib
import openai


class DataScoutingService:
    """
    Provides data profiling and scouting capabilities:
    - Sample-based analysis
    - Metadata validation
    - Pattern detection
    - PII detection
    - LLM-powered observation generation
    """

    def __init__(self):
        self.duckdb_service = DuckDBService()
        self.storage_service = StorageService()

        # Configure openai library to use OpenRouter
        openai.api_base = "https://openrouter.ai/api/v1"
        openai.api_key = settings.OPENROUTER_API_KEY

        # Simple in-memory cache for LLM pattern discoveries (keyed by column hash)
        self._pattern_cache: Dict[str, Dict[str, Any]] = {}

        # LLM configuration from settings
        self.llm_model = settings.OPENROUTER_MODEL
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
        self.llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS", "500"))

    def _serialize_for_json(self, obj: Any) -> Any:
        """Helper to serialize datetime/date objects for JSON, sanitizing NaN/Inf floats"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, (np.integer, np.floating)):
            val = obj.item()
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                return None
            return val
        elif isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, dict):
            return {self._serialize_for_json(k): self._serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_for_json(item) for item in obj]
        else:
            return obj

    # Log configuration on initialization
        print(f"[DataScoutingService] Initialized with model: {self.llm_model}, temp: {self.llm_temperature}, max_tokens: {self.llm_max_tokens}")

    def scout_dataset(self, dataset_id: str, sample_size: int = 1000) -> Dict[str, Any]:
        """
        Perform comprehensive data scouting on a dataset.

        Returns observations, discrepancies, and scouting questions.
        """
        # Load schema and sample data
        schema = self.storage_service.load_schema(dataset_id)
        sample_df = self._load_sample(dataset_id, sample_size)

        # Perform profiling
        column_profiles = self._profile_columns(sample_df, schema)

        # Detect issues and discrepancies
        discrepancies = self._detect_discrepancies(column_profiles, schema)

        # Generate natural language observations
        observations = self._generate_observations(column_profiles, schema, discrepancies)

        # Generate scouting questions
        questions = self._generate_scouting_questions(discrepancies, column_profiles)

        result = {
            'success': True,
            'dataset_id': dataset_id,
            'sample_size': len(sample_df),
            'total_rows': schema.get('total_rows', 0),
            'observations': observations,
            'scouting_questions': questions,
            'column_profiles': column_profiles,
            'discrepancies': discrepancies,
            'timestamp': datetime.utcnow().isoformat()
        }
        return self._serialize_for_json(result)

    def _load_sample(self, dataset_id: str, sample_size: int) -> pd.DataFrame:
        """Load a sample of the dataset for profiling"""
        # Use StorageService to load the dataset
        df = self.storage_service.load_dataset(dataset_id)

        # Return sample or full dataset if smaller
        if len(df) > sample_size:
            return df.head(sample_size)
        return df

    def _profile_columns(self, df: pd.DataFrame, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Profile each column with detailed statistics and pattern analysis
        """
        profiles = []

        for col in df.columns:
            profile = {
                'column_name': col,
                'dtype': str(df[col].dtype),
                'null_count': int(df[col].isna().sum()),
                'null_percentage': float((df[col].isna().sum() / len(df)) * 100),
                'populated_percentage': float(((len(df) - df[col].isna().sum()) / len(df)) * 100),
                'unique_count': int(df[col].nunique()),
                'cardinality': 'high' if df[col].nunique() > len(df) * 0.9 else 'medium' if df[col].nunique() > len(df) * 0.5 else 'low',
                'has_duplicates': bool(df[col].duplicated().any()),
            }

            # Get metadata from schema
            schema_col = next((c for c in schema.get('columns', []) if c['name'] == col), None)
            if schema_col:
                profile['metadata_description'] = schema_col.get('description')
                profile['metadata_business_name'] = schema_col.get('business_name')

            # Pattern analysis for non-null values
            non_null_series = df[col].dropna()

            if len(non_null_series) > 0:
                # Detect patterns (hybrid: rules + LLM)
                profile['patterns'] = self._detect_patterns(non_null_series, col)

                # PII detection
                profile['potential_pii'] = self._detect_pii(col, non_null_series)

                # Type-specific profiling
                if pd.api.types.is_numeric_dtype(df[col]):
                    profile.update(self._profile_numeric(non_null_series))
                elif pd.api.types.is_string_dtype(df[col]) or df[col].dtype == 'object':
                    profile.update(self._profile_text(non_null_series))
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    profile.update(self._profile_datetime(non_null_series))

            profiles.append(profile)

        return profiles

    def _detect_patterns(self, series: pd.Series, column_name: str = "") -> Dict[str, Any]:
        """
        Hybrid pattern detection: Fast rule-based + LLM semantic analysis

        Phase 1: Always run fast regex-based detection
        Phase 2: Conditionally run LLM semantic analysis for deeper insights
        """
        # PHASE 1: Fast rule-based detection (always runs)
        patterns = self._detect_patterns_rules(series)

        # PHASE 2: LLM semantic analysis (conditional - only when valuable)
        if self._should_use_llm_for_patterns(patterns, series, column_name):
            try:
                # Generate cache key from column name + sample values
                cache_key = self._generate_cache_key(column_name, series)

                # Check cache first
                if cache_key in self._pattern_cache:
                    patterns['semantic'] = self._pattern_cache[cache_key]
                else:
                    # Run LLM analysis
                    semantic_insights = self._discover_semantic_patterns(series, column_name, patterns)
                    patterns['semantic'] = semantic_insights
                    # Cache the result
                    self._pattern_cache[cache_key] = semantic_insights
            except Exception as e:
                print(f"LLM pattern discovery failed for {column_name}: {e}")
                patterns['semantic'] = None
        else:
            patterns['semantic'] = None

        return patterns

    def _detect_patterns_rules(self, series: pd.Series) -> Dict[str, Any]:
        """Fast rule-based pattern detection (no LLM calls)"""
        patterns = {
            'email_pattern': 0,
            'phone_pattern': 0,
            'url_pattern': 0,
            'date_pattern': 0,
            'numeric_string': 0,
            'mixed_values': False,
            'inconsistent_format': False
        }

        if not pd.api.types.is_string_dtype(series) and series.dtype != 'object':
            return patterns

        sample = series.head(100).astype(str)

        # Email pattern
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        patterns['email_pattern'] = sum(bool(re.match(email_regex, str(val))) for val in sample)

        # Phone pattern (various formats)
        phone_regex = r'^\+?1?\d{9,15}$'
        patterns['phone_pattern'] = sum(bool(re.match(phone_regex, str(val).replace('-', '').replace(' ', '').replace('(', '').replace(')', ''))) for val in sample)

        # URL pattern
        url_regex = r'^https?://'
        patterns['url_pattern'] = sum(bool(re.match(url_regex, str(val))) for val in sample)

        # Check for mixed values (e.g., "N/A", "Unknown" mixed with real data)
        placeholder_values = {'n/a', 'na', 'none', 'null', 'unknown', 'missing', '-', ''}
        has_placeholders = any(str(val).lower().strip() in placeholder_values for val in sample)
        has_real_data = any(str(val).lower().strip() not in placeholder_values for val in sample)
        patterns['mixed_values'] = has_placeholders and has_real_data

        return patterns

    def _should_use_llm_for_patterns(
        self,
        patterns: Dict[str, Any],
        series: pd.Series,
        column_name: str
    ) -> bool:
        """
        Decide if LLM semantic analysis is worth the cost.

        Trigger LLM when:
        - Mixed/inconsistent values detected (quality issues)
        - High cardinality (likely business IDs/codes)
        - No clear standard pattern detected
        - Column name suggests business-specific meaning
        """
        # Skip for very small columns
        if len(series.dropna()) < 5:
            return False

        # Trigger if mixed values detected
        if patterns.get('mixed_values'):
            return True

        # Trigger for high cardinality (likely business IDs, codes, etc.)
        unique_ratio = series.nunique() / len(series)
        if unique_ratio > 0.7:  # 70%+ unique values
            return True

        # Trigger if no standard patterns detected
        has_standard_pattern = (
            patterns.get('email_pattern', 0) > 50 or  # Majority are emails
            patterns.get('phone_pattern', 0) > 50 or  # Majority are phones
            patterns.get('url_pattern', 0) > 50       # Majority are URLs
        )
        if not has_standard_pattern and unique_ratio > 0.3:
            return True

        # Trigger for business-meaningful column names
        business_indicators = [
            'id', 'code', 'ref', 'number', 'key', 'sku', 'order',
            'invoice', 'ticket', 'account', 'customer', 'product',
            'transaction', 'handle', 'slug', 'token'
        ]
        col_lower = column_name.lower()
        if any(indicator in col_lower for indicator in business_indicators):
            return True

        return False

    def _generate_cache_key(self, column_name: str, series: pd.Series) -> str:
        """Generate cache key from column name + sample values"""
        sample_str = str(series.head(10).tolist())
        key_string = f"{column_name}:{sample_str}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def _discover_semantic_patterns(
        self,
        series: pd.Series,
        column_name: str,
        base_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use LLM to discover semantic patterns and business context.

        Returns enriched insights about what this column represents.
        """
        # Get clean sample (no nulls)
        sample = series.dropna().head(20).tolist()

        if len(sample) == 0:
            return {
                'semantic_type': 'unknown',
                'confidence': 0.0,
                'error': 'No non-null values to analyze'
            }

        # Serialize sample to handle datetime/date objects
        serialized_sample = self._serialize_for_json(sample)

        # Build context from rule-based patterns
        pattern_context = []
        if base_patterns['email_pattern'] > 10:
            pattern_context.append(f"- {base_patterns['email_pattern']} values match email pattern")
        if base_patterns['phone_pattern'] > 10:
            pattern_context.append(f"- {base_patterns['phone_pattern']} values match phone pattern")
        if base_patterns['url_pattern'] > 10:
            pattern_context.append(f"- {base_patterns['url_pattern']} values match URL pattern")
        if base_patterns['mixed_values']:
            pattern_context.append("- Contains mixed placeholder values (N/A, Unknown, etc.)")

        pattern_summary = "\n".join(pattern_context) if pattern_context else "No standard patterns detected"

        prompt = f"""Analyze this data column and identify semantic patterns:

**Column name:** {column_name}

**Sample values (first 20):**
{json.dumps(serialized_sample, indent=2)}

**Rule-based detection found:**
{pattern_summary}

**Task:** Identify what this column represents in a business context.

Return JSON with this structure:
{{
  "semantic_type": "Short label (e.g., 'customer_id', 'order_number', 'product_sku', 'user_handle', 'email', 'category')",
  "business_context": "What this represents in business terms (1-2 sentences)",
  "format_pattern": "Describe the format/structure if there is one (e.g., 'ORD-YYYYMMDD-####', 'Twitter handles (@username)', 'UUID v4')",
  "quality_issues": ["List any data quality issues found", "e.g., inconsistent formats, mixed types, invalid values"],
  "suggested_validations": ["List validation rules that would make sense", "e.g., 'Must start with ORD-', 'Length should be 10-12 chars'"],
  "confidence_score": 0.0-1.0
}}

Be specific and practical. Focus on actionable insights."""

        try:
            response = openai.ChatCompletion.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are a data profiling expert. Analyze data patterns and provide actionable insights in valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.llm_max_tokens,
                temperature=self.llm_temperature
            )

            content = response['choices'][0]['message']['content'].strip()

            # Try to extract JSON if wrapped in markdown code blocks
            if content.startswith('```'):
                content = content.split('```')[1]
                if content.startswith('json'):
                    content = content[4:]
                content = content.strip()

            result = json.loads(content)
            return result

        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            print(f"Response content: {content}")
            return {
                'semantic_type': 'unknown',
                'confidence_score': 0.0,
                'error': 'Failed to parse LLM response'
            }
        except Exception as e:
            print(f"LLM semantic pattern discovery failed: {e}")
            return {
                'semantic_type': 'unknown',
                'confidence_score': 0.0,
                'error': str(e)
            }

    def _detect_pii(self, column_name: str, series: pd.Series) -> Dict[str, Any]:
        """Detect potential PII (Personally Identifiable Information)"""
        pii_indicators = {
            'is_potential_pii': False,
            'pii_types': [],
            'confidence': 'low'
        }

        col_lower = column_name.lower()

        # Column name-based detection
        pii_keywords = {
            'email': ['email', 'e-mail', 'mail'],
            'phone': ['phone', 'tel', 'mobile', 'cell'],
            'name': ['name', 'firstname', 'lastname', 'fullname'],
            'address': ['address', 'street', 'city', 'zip', 'postal'],
            'ssn': ['ssn', 'social security'],
            'credit_card': ['card', 'cc', 'credit'],
            'dob': ['birth', 'dob', 'birthday'],
            'ip_address': ['ip', 'ipaddress']
        }

        for pii_type, keywords in pii_keywords.items():
            if any(keyword in col_lower for keyword in keywords):
                pii_indicators['pii_types'].append(pii_type)
                pii_indicators['is_potential_pii'] = True
                pii_indicators['confidence'] = 'high'

        # Pattern-based detection (for string columns)
        if pd.api.types.is_string_dtype(series) or series.dtype == 'object':
            sample = series.head(50).astype(str)

            # Email pattern
            if sum('@' in str(val) for val in sample) > len(sample) * 0.5:
                if 'email' not in pii_indicators['pii_types']:
                    pii_indicators['pii_types'].append('email')
                    pii_indicators['is_potential_pii'] = True
                    pii_indicators['confidence'] = 'medium'

        return pii_indicators

    def _profile_numeric(self, series: pd.Series) -> Dict[str, Any]:
        """Profile numeric columns"""
        def safe_float(val) -> Optional[float]:
            try:
                v = float(val)
                return None if (math.isnan(v) or math.isinf(v)) else v
            except (TypeError, ValueError):
                return None

        return {
            'min': safe_float(series.min()),
            'max': safe_float(series.max()),
            'mean': safe_float(series.mean()),
            'median': safe_float(series.median()),
            'std': safe_float(series.std()),
            'has_negatives': bool((series < 0).any()),
            'has_zeros': bool((series == 0).any()),
            'is_integer_like': bool(series.dropna().apply(lambda x: float(x).is_integer()).all())
        }

    def _profile_text(self, series: pd.Series) -> Dict[str, Any]:
        """Profile text/string columns"""
        str_series = series.astype(str)

        return {
            'min_length': int(str_series.str.len().min()),
            'max_length': int(str_series.str.len().max()),
            'avg_length': float(str_series.str.len().mean()),
            'most_common_values': series.value_counts().head(5).to_dict(),
            'has_empty_strings': bool((str_series == '').any()),
            'has_whitespace_only': bool(str_series.str.strip().eq('').any())
        }

    def _profile_datetime(self, series: pd.Series) -> Dict[str, Any]:
        """Profile datetime columns"""
        return {
            'min_date': str(series.min()),
            'max_date': str(series.max()),
            'date_range_days': int((series.max() - series.min()).days)
        }

    def _detect_discrepancies(self, profiles: List[Dict[str, Any]], schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect discrepancies between metadata and actual data
        """
        discrepancies = []

        for profile in profiles:
            col_name = profile['column_name']

            # High null rate
            if profile['null_percentage'] > 40:
                discrepancies.append({
                    'column': col_name,
                    'type': 'high_null_rate',
                    'severity': 'medium',
                    'description': f"{col_name} has {profile['null_percentage']:.1f}% null values",
                    'metadata_description': profile.get('metadata_description')
                })

            # Mixed values (e.g., "N/A" in email field)
            if profile.get('patterns', {}).get('mixed_values'):
                discrepancies.append({
                    'column': col_name,
                    'type': 'mixed_values',
                    'severity': 'high',
                    'description': f"{col_name} contains placeholder values mixed with real data",
                    'suggestion': f"Consider cleaning or moving placeholder values to a separate indicator field"
                })

            # Email column with non-email values
            if 'email' in col_name.lower() and profile.get('patterns', {}).get('email_pattern', 0) < 80:
                discrepancies.append({
                    'column': col_name,
                    'type': 'pattern_mismatch',
                    'severity': 'high',
                    'description': f"{col_name} contains non-email values (only {profile.get('patterns', {}).get('email_pattern', 0)}% match email pattern)",
                    'suggestion': "Clean non-email values or move to a separate field"
                })

            # Undocumented column
            if not profile.get('metadata_description'):
                if profile['cardinality'] == 'low':  # Categorical column without docs
                    discrepancies.append({
                        'column': col_name,
                        'type': 'missing_documentation',
                        'severity': 'low',
                        'description': f"{col_name} is a categorical field with no documentation",
                        'suggestion': f"Document the possible values: {list(profile.get('most_common_values', {}).keys())[:3]}"
                    })

            # High cardinality - potential primary key
            if profile['cardinality'] == 'high' and not profile['has_duplicates']:
                discrepancies.append({
                    'column': col_name,
                    'type': 'potential_key',
                    'severity': 'info',
                    'description': f"{col_name} has high cardinality ({profile['unique_count']} unique values) with no duplicates",
                    'suggestion': "This looks like a strong primary key or identifier"
                })

            # PII detection
            if profile.get('potential_pii', {}).get('is_potential_pii'):
                pii_types = ', '.join(profile['potential_pii']['pii_types'])
                discrepancies.append({
                    'column': col_name,
                    'type': 'pii_detected',
                    'severity': 'high',
                    'description': f"Potential PII detected in {col_name}: {pii_types}",
                    'suggestion': "Ensure proper data handling and access controls"
                })

        return discrepancies

    def _generate_observations(
        self,
        profiles: List[Dict[str, Any]],
        schema: Dict[str, Any],
        discrepancies: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate natural language observations from profiling data.
        Enhanced with semantic insights from LLM pattern discovery.
        """
        observations = []

        for profile in profiles:
            col = profile['column_name']
            patterns = profile.get('patterns', {})
            semantic = patterns.get('semantic') if patterns else None

            # Priority 1: Semantic insights from LLM (if available and confident)
            if semantic and semantic.get('confidence_score', 0) > 0.7:
                obs = f"**{col}**: {semantic.get('business_context', 'Semantic analysis available')}"
                if semantic.get('format_pattern'):
                    obs += f" (Format: {semantic['format_pattern']})"
                observations.append(obs)
                continue

            # Priority 2: Standard observations with pattern info
            # Observation about population rate
            if profile['null_percentage'] < 5:
                obs = f"The column **{col}** is {profile['populated_percentage']:.0f}% populated"

                # Add pattern info if available
                if patterns.get('email_pattern', 0) > 90:
                    obs += " and follows standard email patterns"
                elif patterns.get('phone_pattern', 0) > 90:
                    obs += " and follows phone number patterns"
                elif semantic and semantic.get('semantic_type'):
                    obs += f" ({semantic['semantic_type']})"

                observations.append(obs + ".")

            elif profile['null_percentage'] > 40:
                obs = f"**{col}**"
                if profile.get('metadata_description'):
                    obs += f" (described as \"{profile['metadata_description']}\")"
                obs += f" has {profile['null_percentage']:.0f}% null values — is this expected?"
                observations.append(obs)

            # Observation about categorical values
            if profile['cardinality'] == 'low' and profile.get('most_common_values'):
                values_str = ", ".join([f'"{k}" ({v})' for k, v in list(profile['most_common_values'].items())[:3]])
                obs = f"**{col}** contains values: {values_str}"

                if not profile.get('metadata_description'):
                    obs += " — no documentation found"
                elif semantic and semantic.get('semantic_type'):
                    obs += f" (appears to be {semantic['semantic_type']})"

                observations.append(obs + ".")

            # Observation about potential primary key
            if profile['cardinality'] == 'high' and not profile['has_duplicates']:
                obs = f"High cardinality in **{col}** (~{profile['unique_count']:,} unique values) with no duplicates"

                if semantic and semantic.get('semantic_type'):
                    obs += f" — likely {semantic['semantic_type']}"
                else:
                    obs += " — looks like a strong primary key"

                observations.append(obs + ".")

            # PII warning
            if profile.get('potential_pii', {}).get('is_potential_pii'):
                pii_types = ', '.join(profile['potential_pii']['pii_types'])
                observations.append(f"⚠️ Potential PII detected: **{col}** ({pii_types}).")

        return observations[:10]  # Limit to top 10 observations

    def _generate_scouting_questions(
        self,
        discrepancies: List[Dict[str, Any]],
        profiles: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate targeted scouting questions based on discrepancies.
        Enhanced with semantic insights from LLM pattern discovery.
        """
        questions = []

        for disc in discrepancies:
            col = disc['column']

            if disc['type'] == 'mixed_values':
                questions.append(
                    f"Should non-standard values in **{col}** be cleaned or moved to a separate field?"
                )

            elif disc['type'] == 'high_null_rate':
                questions.append(
                    f"Is the high null rate ({disc['description'].split('%')[0].split()[-1]}%) in **{col}** intentional?"
                )

            elif disc['type'] == 'missing_documentation':
                # Check if we have semantic insights for this column
                profile = next((p for p in profiles if p['column_name'] == col), None)
                if profile and profile.get('patterns', {}).get('semantic'):
                    semantic = profile['patterns']['semantic']
                    if semantic.get('semantic_type'):
                        questions.append(
                            f"Should **{col}** be documented as '{semantic['semantic_type']}'?"
                        )
                    else:
                        questions.append(
                            f"What do the values in **{col}** represent? Should they be documented?"
                        )
                else:
                    questions.append(
                        f"What do the values in **{col}** represent? Should they be documented?"
                    )

            elif disc['type'] == 'pattern_mismatch':
                questions.append(disc.get('suggestion', f"How should we handle inconsistent values in **{col}**?"))

        # Add questions from semantic quality issues
        for profile in profiles:
            patterns = profile.get('patterns', {})
            semantic = patterns.get('semantic') if patterns else None

            if semantic and semantic.get('quality_issues'):
                for issue in semantic['quality_issues'][:2]:  # Max 2 per column
                    questions.append(f"**{profile['column_name']}**: {issue}")

        return questions[:10]  # Limit to top 10 questions

    async def generate_llm_observations(
        self,
        dataset_id: str,
        profiles: List[Dict[str, Any]],
        schema: Dict[str, Any],
        sample_data: pd.DataFrame
    ) -> str:
        """
        Use LLM to generate natural, conversational observations about the data
        """
        # Prepare context
        context = {
            'dataset_name': schema.get('dataset_name', 'dataset'),
            'total_rows': schema.get('total_rows', 0),
            'column_count': len(profiles),
            'sample_rows': sample_data.head(5).to_dict('records'),
            'profiles': profiles[:10]  # Top 10 columns
        }

        prompt = f"""You are a data profiling expert. You've just analyzed a dataset called "{context['dataset_name']}" with {context['total_rows']:,} rows and {context['column_count']} columns.

Here's what you found:

Sample data (first 5 rows):
{context['sample_rows']}

Column profiles:
{profiles[:10]}

Generate a concise, friendly "First Look Observations" summary in natural language. Focus on:
1. Data quality issues (nulls, mixed values, inconsistencies)
2. Potential primary keys or identifiers
3. PII or sensitive data
4. Unexpected patterns or discrepancies

Format as a bulleted list, max 6 observations. Be specific and actionable.
"""

        try:
            response = openai.ChatCompletion.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are a data profiling expert who generates clear, actionable insights."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.llm_max_tokens,
                temperature=self.llm_temperature
            )

            return response['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"LLM observation generation failed: {e}")
            # Fallback to rule-based observations
            return "\n".join([f"- {obs}" for obs in self._generate_observations(profiles, schema, [])])
