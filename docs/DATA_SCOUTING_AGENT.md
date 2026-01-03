# Data Scouting Agent

## Overview

The Data Scouting Agent is an intelligent data profiling system that automatically analyzes datasets when they're loaded, providing actionable insights about data quality, patterns, and discrepancies. It bridges the gap between what the system thinks the data is (metadata) and what it actually is (real patterns).

The agent uses a **hybrid approach** that combines fast rule-based pattern detection with intelligent LLM-powered semantic analysis, optimizing for both speed and insight quality while minimizing API costs.

## Philosophy

Traditional data profiling tools show you statistics. The Data Scouting Agent goes further by:

1. **Building Trust Early**: Shows you've "looked at the data" before asking questions
2. **Uncovering Discrepancies**: Validates metadata against actual patterns
3. **Enabling Smarter Questions**: Generates targeted follow-up questions
4. **Providing Context**: Understands business meaning, not just technical patterns

Think of it as a **"First Look"** or **"Data Pulse Check"** — quick vital signs and observations that help you understand your data's reality.

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Scouting Agent                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Load Sample (1000 rows)                                 │
│     └─── StorageService.load_dataset()                      │
│                                                              │
│  2. Profile Columns                                          │
│     ├─── Rule-Based Detection (ALWAYS)                      │
│     │    • Email patterns (regex)                           │
│     │    • Phone patterns (regex)                           │
│     │    • URL patterns (regex)                             │
│     │    • Mixed values detection                           │
│     │    • Null rates, cardinality                          │
│     │                                                        │
│     └─── LLM Semantic Analysis (CONDITIONAL)                │
│          • Trigger Logic:                                   │
│          │  ✓ Mixed/inconsistent values                     │
│          │  ✓ High cardinality (70%+ unique)                │
│          │  ✓ No standard patterns found                    │
│          │  ✓ Business column names (order_id, sku, etc)    │
│          │                                                   │
│          • Discovers:                                        │
│            ✓ Semantic type (customer_id, order_number)      │
│            ✓ Business context                               │
│            ✓ Format patterns (ORD-YYYYMMDD-####)            │
│            ✓ Quality issues                                 │
│            ✓ Suggested validations                          │
│                                                              │
│  3. Detect Discrepancies                                     │
│     • High null rates                                        │
│     • Pattern mismatches                                     │
│     • Missing documentation                                  │
│     • PII detection                                          │
│                                                              │
│  4. Generate Observations & Questions                        │
│     • Natural language insights                             │
│     • Targeted scouting questions                           │
│     • Priority-based severity levels                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Hybrid Pattern Detection

The agent uses a two-phase approach:

#### Phase 1: Rule-Based Detection (Always Runs)
Fast, deterministic pattern matching using regex and statistical analysis:

```python
# Email detection
email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# Phone detection
phone_regex = r'^\+?1?\d{9,15}$'

# URL detection
url_regex = r'^https?://'

# Mixed values (N/A, Unknown mixed with real data)
placeholder_values = {'n/a', 'na', 'none', 'null', 'unknown', 'missing'}
```

**Cost:** Zero API calls
**Speed:** Instant
**Coverage:** ~60-70% of columns with clear patterns

#### Phase 2: LLM Semantic Analysis (Conditional)
Intelligent semantic understanding for business context:

**Triggering Logic:**
```python
def should_use_llm(column):
    # Skip for very small columns
    if len(column.dropna()) < 5:
        return False

    # Trigger if mixed values detected
    if has_mixed_placeholder_values(column):
        return True

    # Trigger for high cardinality (likely IDs/codes)
    if unique_ratio > 0.7:
        return True

    # Trigger if no standard patterns found
    if not (is_email or is_phone or is_url):
        return True

    # Trigger for business column names
    if column_name contains ['id', 'code', 'ref', 'sku', 'order']:
        return True

    return False
```

**LLM Discovers:**
- **Semantic Type**: `customer_id`, `order_number`, `product_sku`, `user_handle`
- **Business Context**: "Order reference numbers from Shopify e-commerce system"
- **Format Pattern**: `ORD-YYYYMMDD-####`, `@username`, `UUID v4`
- **Quality Issues**: "3 records missing prefix", "Inconsistent date formatting"
- **Suggested Validations**: "Must start with ORD-", "Length should be 10-12 chars"

**Cost:** API calls for ~30-40% of columns
**Speed:** ~1-2 seconds per column (cached)
**Coverage:** High-value business insights

### Smart Caching

The agent caches LLM results using MD5 hashing of `column_name + sample_values`:

```python
cache_key = md5(f"{column_name}:{sample_values[:10]}").hexdigest()

if cache_key in cache:
    return cached_result  # No API call
else:
    result = call_llm(...)
    cache[cache_key] = result  # Cache for next time
    return result
```

**Benefits:**
- Subsequent analyses of the same dataset are instant
- No redundant API calls for similar columns
- Significant cost savings

## Example Output

### For a `customers` Table

#### First Look Observations
```
• The column email is 98% populated and follows standard email patterns.

• customer_since (described as "Date customer joined") has 40% null values — is this expected?

• status contains values: "Active" (820), "Churned" (150), "Pending" (30) — no documentation found.

• High cardinality in customer_id (~1.2M unique values) with no duplicates — looks like a strong primary key.

• customer_ref: Customer reference numbers from Salesforce CRM integration (Format: CUST-#####-XX where XX is region code)

• ⚠️ Potential PII detected: email, full_name, phone, address (email, name, phone, address).
```

#### High Priority Issues
```
⚠️ email: Contains non-email values (only 98% match email pattern)
   💡 Clean non-email values or move to a separate field

⚠️ customer_ref: 5 records missing region code suffix
   💡 Should these be updated to match CUST-#####-XX format?
```

#### Scouting Questions
```
? Should non-standard values in email be cleaned or moved to a separate field?

? What does "Pending" status mean? Should it be documented?

? Is the high null rate (40%) in customer_since intentional?

? Should customer_ref be documented as 'crm_customer_id'?

? customer_ref: 2 records use old numeric-only format - should these be migrated?
```

#### Semantic Analysis Details (Expandable)
```
┌─ customer_ref ──────────────────────────── [89% confident] ─┐
│ Type: crm_customer_id                                        │
│ Context: Customer reference numbers from Salesforce CRM      │
│          integration used for cross-system tracking          │
│ Format: CUST-#####-XX where XX is region code (US/UK/EU/AS) │
│                                                              │
│ Quality Issues:                                              │
│ • 5 records missing region code suffix                      │
│ • 2 records use old numeric-only format                     │
│                                                              │
│ Suggested Validations:                                       │
│ • Should match pattern CUST-#####-[A-Z]{2}                  │
│ • Region codes should be valid: US, UK, EU, AS              │
└──────────────────────────────────────────────────────────────┘
```

## API Endpoints

### 1. Full Scouting Analysis
```http
POST /api/v1/datasets/{dataset_id}/scout
Content-Type: application/json

{
  "sample_size": 1000  // Optional, default: 1000
}
```

**Response:**
```json
{
  "success": true,
  "dataset_id": "abc-123",
  "sample_size": 1000,
  "total_rows": 50000,
  "observations": [
    "The column email is 98% populated and follows standard email patterns.",
    "..."
  ],
  "scouting_questions": [
    "Should non-standard values in email be cleaned?",
    "..."
  ],
  "column_profiles": [
    {
      "column_name": "email",
      "dtype": "object",
      "null_percentage": 2.0,
      "patterns": {
        "email_pattern": 98,
        "mixed_values": true,
        "semantic": {
          "semantic_type": "contact_email",
          "business_context": "Customer contact emails...",
          "confidence_score": 0.92
        }
      }
    }
  ],
  "discrepancies": [
    {
      "column": "email",
      "type": "pattern_mismatch",
      "severity": "high",
      "description": "Contains non-email values",
      "suggestion": "Clean or move to separate field"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 2. Regenerate Observations (LLM-Only)
```http
POST /api/v1/datasets/{dataset_id}/scout/regenerate-observations
Content-Type: application/json

{
  "use_llm": true
}
```

**Response:**
```json
{
  "success": true,
  "observations": "• Column email shows...\n• Column status...",
  "method": "llm"
}
```

### 3. Quick Summary
```http
GET /api/v1/datasets/{dataset_id}/scout/summary
```

**Response:**
```json
{
  "success": true,
  "dataset_id": "abc-123",
  "dataset_name": "customers.csv",
  "total_rows": 50000,
  "observations_count": 6,
  "questions_count": 5,
  "discrepancies_count": 8,
  "high_priority_issues": [
    {
      "column": "email",
      "severity": "high",
      "description": "Contains non-email values"
    }
  ]
}
```

## Frontend Integration

### DataScoutPanel Component

The `DataScoutPanel` component automatically appears in the Dataset Hub view:

```tsx
<DataScoutPanel
  datasetId={datasetId}
  datasetName={datasetName}
  onQuestionClick={(question) => onQuerySelect(question)}
/>
```

**Features:**
- ✨ Auto-loads on dataset open
- 🔄 Refresh button to re-run analysis
- 📊 AI-Enhanced badge showing hybrid analysis
- 📈 Analytics counter (X columns with semantic AI • Y with rule-based)
- 🔍 Expandable semantic details view
- ⚠️ Priority-based issue display (high/medium/info)
- ❓ Clickable scouting questions

### UI Components

#### Card Component
```tsx
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'

<Card className="border-purple-200">
  <CardHeader>
    <CardTitle>Data Scout Report</CardTitle>
  </CardHeader>
  <CardContent>
    {/* Content */}
  </CardContent>
</Card>
```

#### Badge Component
```tsx
import { Badge } from '@/components/ui/badge'

<Badge variant="outline" className="bg-purple-50 text-purple-700">
  AI-Enhanced
</Badge>
```

## Configuration

### Environment Variables

All LLM configuration is managed via `.env`:

```bash
# Required
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Optional: Fine-tune LLM behavior
LLM_TEMPERATURE=0.2  # Lower = more deterministic (0.0-1.0)
LLM_MAX_TOKENS=500   # Maximum tokens for responses
```

### Model Selection Priority

1. `OPENROUTER_MODEL` (if set) ← **Primary**
2. `LLM_MODEL` (if OPENROUTER_MODEL not set) ← Fallback
3. `"anthropic/claude-3.5-sonnet"` ← Default

### Recommended Models

| Use Case | Model | Temperature | Max Tokens |
|----------|-------|-------------|------------|
| **Production** | `anthropic/claude-3.5-sonnet` | 0.2 | 500 |
| **Cost Savings** | `anthropic/claude-3-haiku` | 0.1 | 300 |
| **High Quality** | `anthropic/claude-3-opus` | 0.3 | 700 |
| **Fast Testing** | `openai/gpt-3.5-turbo` | 0.2 | 400 |

### Temperature Guidelines

- **0.0-0.2**: Highly deterministic, consistent results
- **0.2-0.5**: Balanced creativity and consistency (recommended)
- **0.5-0.8**: More creative, diverse observations
- **0.8-1.0**: Very creative (not recommended for data profiling)

## Cost Optimization

### Strategy Overview

The hybrid approach provides significant cost savings:

| Approach | Columns Analyzed | LLM Calls | Relative Cost |
|----------|-----------------|-----------|---------------|
| **All LLM** | 20 | 20 | 100% |
| **Hybrid** | 20 | 7 | **35%** |
| **Rule-Based Only** | 20 | 0 | 0% (but limited insights) |

### Cost Breakdown Example

For a typical dataset with 20 columns:

```
Standard Patterns (Rule-Based Only):
- email (98% match) → No LLM call
- phone (95% match) → No LLM call
- website (URL pattern) → No LLM call
- created_at (datetime) → No LLM call
- status (low cardinality, documented) → No LLM call
Total: 5 columns, $0 cost

Business-Specific Patterns (LLM Analysis):
- order_id (high cardinality) → LLM call
- customer_ref (business name) → LLM call
- product_sku (mixed formats) → LLM call
- transaction_code (no clear pattern) → LLM call
- user_handle (business context) → LLM call
- account_number (validation needed) → LLM call
- reference_id (quality issues) → LLM call
Total: 7 columns, ~$0.02-0.05 cost

Overall: 65% cost reduction vs full LLM approach
```

### Cache Hit Rate

With caching enabled:
- **First analysis**: 100% LLM calls (baseline cost)
- **Second analysis** (same dataset): ~5% LLM calls (95% cached)
- **Similar datasets**: ~30-40% LLM calls (partial cache hits)

### Best Practices

1. **Use appropriate sample sizes**: Default 1000 rows is optimal
2. **Enable caching**: Cache persists during server runtime
3. **Choose right model**: Use Haiku for testing, Sonnet for production
4. **Adjust temperature**: Lower temperature = more deterministic = fewer retries
5. **Monitor token usage**: Set LLM_MAX_TOKENS appropriately

## Use Cases

### 1. Data Quality Validation
**Scenario**: New dataset uploaded, need to validate quality before analysis

**Process**:
1. Dataset loaded
2. Data Scout automatically runs
3. Identifies: 40% null values in critical column
4. Flags: Mixed placeholder values in email field
5. Suggests: Clean data before proceeding

**Value**: Catch quality issues early, prevent bad analysis

### 2. Metadata Validation
**Scenario**: Dataset has documentation, but is it accurate?

**Process**:
1. Scout compares metadata descriptions to actual patterns
2. Finds: "customer_since" described as "Date joined" but 40% null
3. Questions: "Is this null rate expected for prospects?"
4. Discovers: Metadata is outdated

**Value**: Ensure documentation matches reality

### 3. Onboarding New Data
**Scenario**: Receiving data from external source, need to understand it quickly

**Process**:
1. Upload dataset
2. Scout provides "First Look" observations
3. LLM discovers: "Shopify order IDs in format ORD-YYYYMMDD-####"
4. Identifies: Business context and validation rules
5. Generates: Targeted questions for clarification

**Value**: Rapid understanding of unfamiliar data

### 4. PII Detection
**Scenario**: Need to identify sensitive data before sharing

**Process**:
1. Scout analyzes all columns
2. Detects potential PII: email, phone, address, SSN
3. Flags with high severity
4. Suggests: "Ensure proper data handling and access controls"

**Value**: Compliance and security

### 5. Data Profiling for ML
**Scenario**: Preparing dataset for machine learning

**Process**:
1. Scout identifies data types and patterns
2. Detects quality issues (nulls, inconsistencies)
3. Suggests validations and cleaning steps
4. Provides format patterns for encoding

**Value**: Clean, validated data for better models

## Technical Details

### Dependencies

**Backend:**
```python
pandas>=1.5.0
numpy>=1.24.0
openai==0.27.10  # Legacy API
```

**Frontend:**
```json
{
  "@tanstack/react-query": "^5.28.0",
  "lucide-react": "^0.378.0",
  "class-variance-authority": "^0.7.0"
}
```

### Database Schema

No additional database tables required. The scouting service operates on:
- Existing `datasets` table
- Parquet files in `DATASETS_DIR/{dataset_id}/data.parquet`
- Schema files in `DATASETS_DIR/{dataset_id}/schema.json`

### Performance

**Typical Analysis Times:**
- Small dataset (10 columns, 1000 rows): ~2-3 seconds
- Medium dataset (25 columns, 1000 rows): ~5-7 seconds
- Large dataset (50 columns, 1000 rows): ~10-15 seconds

**Breakdown:**
- Data loading: ~100-500ms
- Rule-based profiling: ~500-1000ms
- LLM semantic analysis: ~1-2s per column (if triggered)
- Caching: ~10-50ms lookup

### Error Handling

The service includes comprehensive error handling:

1. **LLM Failures**: Falls back to rule-based observations
2. **File Not Found**: Returns clear error message
3. **Invalid JSON**: Attempts to extract JSON from markdown
4. **API Timeouts**: Retries with exponential backoff
5. **Empty Columns**: Skips LLM analysis for columns with <5 non-null values

### Logging

The service logs important events:

```
[DataScoutingService] Initialized with model: anthropic/claude-3.5-sonnet, temp: 0.2, max_tokens: 500
LLM pattern discovery failed for customer_id: Timeout
LLM observation generation failed: API error
```

## Best Practices

### For Users

1. **Review observations carefully**: They're AI-generated, not absolute truth
2. **Use scouting questions as guides**: They highlight areas needing clarification
3. **Check semantic details**: Expand to see full LLM reasoning
4. **Validate PII findings**: Confirm before taking action
5. **Update metadata**: Use insights to improve documentation

### For Developers

1. **Monitor LLM costs**: Track API usage in production
2. **Adjust trigger thresholds**: Fine-tune when LLM analysis runs
3. **Cache aggressively**: Persist cache to disk in production
4. **Handle errors gracefully**: Always provide fallback to rule-based
5. **Test with diverse data**: Ensure patterns work across domains
6. **Version prompts**: Track LLM prompt changes for reproducibility

### For Administrators

1. **Set reasonable limits**: Configure LLM_MAX_TOKENS appropriately
2. **Monitor API keys**: Rotate OPENROUTER_API_KEY regularly
3. **Review costs**: Track spending per dataset/user
4. **Enable logging**: Monitor LLM calls and failures
5. **Configure rate limits**: Prevent abuse

## Troubleshooting

### Issue: No semantic insights showing

**Possible Causes:**
1. LLM triggering thresholds not met
2. API key not configured
3. Column has <5 non-null values

**Solutions:**
- Check logs for trigger decisions
- Verify OPENROUTER_API_KEY in .env
- Ensure columns have sufficient data

### Issue: Slow analysis

**Possible Causes:**
1. Too many columns triggering LLM
2. Large sample size
3. API latency

**Solutions:**
- Reduce sample_size parameter
- Adjust trigger thresholds
- Use faster model (Haiku)
- Enable/verify caching

### Issue: Inaccurate observations

**Possible Causes:**
1. Temperature too high (too creative)
2. Sample not representative
3. LLM hallucination

**Solutions:**
- Lower LLM_TEMPERATURE to 0.1-0.2
- Increase sample_size for better representation
- Review and validate AI insights manually

### Issue: High API costs

**Possible Causes:**
1. Too many LLM calls
2. Large max_tokens setting
3. No caching

**Solutions:**
- Tighten trigger thresholds
- Reduce LLM_MAX_TOKENS to 300-400
- Verify cache is working
- Use cheaper model (Haiku)

## Roadmap

### Planned Features

- [ ] **Persistent caching**: Cache to Redis/database
- [ ] **Pattern library**: Learn common patterns across datasets
- [ ] **Custom triggers**: User-configurable LLM trigger rules
- [ ] **Anomaly detection**: Statistical outlier identification
- [ ] **Relationship discovery**: Cross-column pattern analysis
- [ ] **Historical tracking**: Track data quality over time
- [ ] **Export reports**: Download scouting reports as PDF
- [ ] **Batch scouting**: Analyze multiple datasets at once

### Future Enhancements

- Multi-language support for observations
- Custom observation templates
- Integration with data catalog systems
- Automated metadata generation from insights
- Real-time scouting as data streams in

## Contributing

### Adding New Pattern Detectors

To add a new rule-based pattern:

```python
def _detect_patterns_rules(self, series: pd.Series) -> Dict[str, Any]:
    patterns = {
        # ... existing patterns ...
        'your_pattern': 0
    }

    # Add your detection logic
    your_regex = r'^YOUR_PATTERN$'
    patterns['your_pattern'] = sum(
        bool(re.match(your_regex, str(val)))
        for val in series.head(100)
    )

    return patterns
```

### Customizing LLM Prompts

Modify the prompt in `_discover_semantic_patterns()`:

```python
prompt = f"""Your custom prompt here:

Column: {column_name}
Sample: {sample}

Return JSON with:
{{
  "your_custom_field": "...",
  ...
}}
"""
```

### Testing

```bash
# Run backend tests
pytest tests/test_data_scouting_service.py

# Test specific pattern
pytest tests/test_data_scouting_service.py::test_email_detection

# Test with sample dataset
python -m pytest tests/ -v --dataset=sample_customers.csv
```

## FAQ

**Q: Does the agent modify my data?**
A: No, it's read-only. It only analyzes and provides insights.

**Q: How accurate are the semantic insights?**
A: Confidence scores are provided. Typically 70-95% accuracy for well-formed data.

**Q: Can I disable LLM analysis?**
A: Yes, set `LLM_TEMPERATURE=-1` or modify trigger thresholds to never trigger.

**Q: What happens if OpenRouter is down?**
A: Graceful fallback to rule-based observations only.

**Q: Is PII detection 100% accurate?**
A: No, it's pattern-based detection. Always manually verify PII findings.

**Q: Can I use a different LLM provider?**
A: Yes, modify `openai.api_base` to point to your provider's OpenAI-compatible endpoint.

**Q: How long are results cached?**
A: In-memory cache persists until server restart. Implement Redis for persistence.

**Q: Can I export scouting reports?**
A: Not yet, but it's on the roadmap. You can access raw JSON via API.

---

## Support

For issues, questions, or contributions:
- GitHub Issues: https://github.com/rnednur/felix/issues
- Documentation: `/docs/`
- API Reference: `/api/docs` (when server running)

---

**Built with ❤️ using Claude Code**
