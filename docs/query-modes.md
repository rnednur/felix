# Query Modes in Felix

Felix offers four intelligent query modes to handle different types of data analysis tasks. This guide explains when and how to use each mode.

## Mode Overview

| Mode | Speed | Complexity | Best For |
|------|-------|------------|----------|
| Auto (✨) | Variable | Variable | Most queries (recommended) |
| SQL (🗄️) | Very Fast | Low-Medium | Filtering, aggregations, grouping |
| Python (🐍) | Medium-Slow | High | ML, statistics, transformations |
| Deep Research (🧠) | Slow | Very High | Complex business questions |

## Auto Mode (✨)

### What It Does

Automatically selects SQL or Python based on your question.

### Detection Logic

Felix analyzes your query for keywords:

**Triggers Python Mode**:
- ML terms: predict, model, forecast, train, classification, regression
- Stats terms: correlation, significance, distribution, outliers
- Data ops: clean, transform, pivot, normalize, encode

**Defaults to SQL**:
- Simple aggregations and filters
- When no Python-specific keywords found

### When to Use

- **Default choice** for most users
- When unsure which mode to use
- For mixed workloads

### Examples

```
"Show top 10 customers" → Auto selects SQL
"Build prediction model" → Auto selects Python
"Average sales by region" → Auto selects SQL
"Correlation analysis" → Auto selects Python
```

## SQL Mode (🗄️)

### What It Does

Generates and executes DuckDB SQL queries for fast data retrieval.

### Capabilities

**Supported Operations**:
- SELECT, WHERE, GROUP BY, ORDER BY
- Aggregations: SUM, AVG, COUNT, MIN, MAX
- Date functions: strptime, EXTRACT, DATE_DIFF
- String operations: LIKE, CONCAT, SUBSTRING
- Window functions: ROW_NUMBER, RANK, LAG
- CTEs (Common Table Expressions)
- Joins (if multiple datasets in future)

**Performance**:
- Typical execution: < 1 second
- Handles millions of rows efficiently
- Columnar storage optimization

### When to Use

✅ **Use SQL for**:
- Filtering data
- Counting and grouping
- Simple calculations
- Finding top/bottom N
- Date-based queries
- Quick exploratory queries

❌ **Don't use SQL for**:
- Machine learning
- Statistical tests
- Complex transformations
- Pivot operations
- Advanced visualizations

### Example Queries

#### Basic Filtering
```
Show me all orders over $1000
→ SELECT * FROM dataset WHERE order_value > 1000 LIMIT 1000
```

#### Aggregation
```
Total revenue by product category
→ SELECT category, SUM(revenue) as total
  FROM dataset
  GROUP BY category
  ORDER BY total DESC
```

#### Date Queries
```
Count orders per month in 2023
→ SELECT
    strftime(strptime(order_date, '%m/%d/%Y'), '%Y-%m') as month,
    COUNT(*) as order_count
  FROM dataset
  WHERE strptime(order_date, '%m/%d/%Y') >= strptime('01/01/2023', '%m/%d/%Y')
  GROUP BY month
```

#### Top N
```
Top 5 salespeople by revenue
→ SELECT salesperson, SUM(revenue) as total
  FROM dataset
  GROUP BY salesperson
  ORDER BY total DESC
  LIMIT 5
```

### Date Handling

Felix automatically handles date parsing:

```sql
-- Your dates in format: "01/15/2023 02:30:45 PM"
-- Felix converts using:
strptime("Date Column", '%m/%d/%Y %I:%M:%S %p')

-- Extract year:
CAST(strftime(strptime("Date Column", '%m/%d/%Y %I:%M:%S %p'), '%Y') AS INTEGER)

-- Filter by date:
WHERE strptime("Date Column", '%m/%d/%Y %I:%M:%S %p') >= strptime('01/01/2023 12:00:00 AM', '%m/%d/%Y %I:%M:%S %p')
```

### Limitations

- Limit of 1000 rows by default (for display)
- Cannot train ML models
- Limited data transformations
- No statistical tests

## Python Mode (🐍)

### What It Does

Generates and executes Python code using pandas, scikit-learn, and data science libraries.

### Available Libraries

```python
pandas, numpy           # Data manipulation
scikit-learn            # Machine learning
scipy, statsmodels      # Statistics
matplotlib, seaborn     # Visualizations
xgboost, lightgbm       # Advanced ML
prophet                 # Time series forecasting
duckdb                  # Fast data loading
```

### When to Use

✅ **Use Python for**:
- Machine learning models
- Statistical analysis
- Correlation studies
- Data cleaning
- Feature engineering
- Complex transformations
- Time series forecasting
- Clustering analysis

### ML Capabilities

#### Classification
```python
# Felix can build:
- Logistic Regression
- Random Forest Classifier
- XGBoost Classifier
- Support Vector Machines

# Example query:
"Train a model to predict customer churn based on usage patterns"
```

#### Regression
```python
# Felix can build:
- Linear Regression
- Random Forest Regressor
- XGBoost Regressor
- Polynomial Regression

# Example query:
"Build a regression model to predict house prices"
```

#### Clustering
```python
# Felix can use:
- K-Means
- DBSCAN
- Hierarchical Clustering

# Example query:
"Segment customers into 5 groups based on behavior"
```

#### Time Series
```python
# Felix can use:
- Prophet (Facebook)
- ARIMA (via statsmodels)
- Exponential Smoothing

# Example query:
"Forecast next 30 days of sales using Prophet"
```

### Statistical Analysis

```python
# Available analyses:
- Pearson/Spearman correlation
- T-tests, ANOVA
- Chi-square tests
- Distribution analysis
- Hypothesis testing
- Confidence intervals

# Example query:
"Test if there's a significant difference in sales between regions"
```

### Code Structure

Felix generates well-structured code:

```python
# 1. Data loading (using DuckDB for efficiency)
df = duckdb_conn.execute("SELECT * FROM dataset").df()

# 2. Data preprocessing
# - Handle missing values
# - Feature engineering
# - Encoding categorical variables

# 3. Analysis/ML
# - Train/test split
# - Model training
# - Evaluation

# 4. Results
result = {
    'summary': 'Brief description',
    'data': results_df.to_dict('records'),
    'metrics': {'accuracy': 0.95},
    'visualizations': [{'data': base64_plot, 'caption': '...'}]
}
```

### Execution Time

- Simple analysis: 1-5 seconds
- Complex aggregations: 5-10 seconds
- ML model training: 30-120 seconds

### Error Recovery

Felix automatically fixes common errors:
1. Type mismatches in encoders
2. Missing imports
3. Data loading issues
4. Column name errors

If automatic fix fails, Felix uses LLM to intelligently debug and retry.

## Deep Research Mode (🧠)

### What It Does

Performs multi-stage comprehensive analysis to answer complex business questions.

### How It Works

```
User Question
    ↓
1. Question Decomposition
   - Breaks into sub-questions
   - Identifies required analyses
    ↓
2. Query Generation
   - Generates SQL queries
   - Generates Python code
   - Plans execution order
    ↓
3. Execution
   - Runs all queries
   - Handles failures gracefully
   - Collects results
    ↓
4. Synthesis
   - Analyzes all findings
   - Identifies patterns
   - Draws conclusions
    ↓
5. Report Generation
   - Executive summary
   - Key findings
   - Visualizations
   - Follow-up questions
```

### When to Use

✅ **Use Deep Research for**:
- Complex business questions
- Root cause analysis
- Multi-dimensional insights
- Comprehensive reports
- Strategic decisions

### Example Analyses

#### Sales Decline Analysis
```
Question: "Why are sales declining in Q3?"

Felix generates:
1. Overall sales trend query
2. Regional breakdown
3. Product category analysis
4. Customer segment analysis
5. Seasonal patterns
6. Correlation with external factors
7. Comparative period analysis

Output: 10-page report with visualizations and recommendations
```

#### Customer Churn Investigation
```
Question: "What drives customer churn?"

Felix analyzes:
1. Churn rate over time
2. Feature correlation with churn
3. Customer segment analysis
4. Behavioral patterns
5. Product usage statistics
6. Support ticket analysis
7. Prediction model

Output: Comprehensive churn analysis report
```

### Report Structure

Deep Research reports include:

1. **Executive Summary**
   - Main findings in 2-3 sentences
   - Direct answer to question

2. **Key Findings**
   - Numbered list of insights
   - Data-backed statements

3. **Visualizations**
   - Charts and graphs
   - Embedded in report

4. **Data Coverage**
   - Questions answered count
   - Data gaps identified

5. **Research Details**
   - All sub-queries executed
   - Expandable code sections
   - Results for each analysis

6. **Follow-up Questions**
   - Recommended next analyses
   - Deeper dive suggestions

### Performance

- Execution time: 30 seconds - 3 minutes
- Depends on complexity and number of sub-questions
- Progress shown in real-time

### PDF Export

Download comprehensive reports:
- Click "Download PDF" button
- Only report content (no sidebar/chat)
- Print-optimized formatting
- All visualizations included

## Choosing the Right Mode

### Decision Tree

```
Is it a complex business question?
├─ Yes → Deep Research
└─ No
    ├─ Need ML or advanced stats?
    │   ├─ Yes → Python
    │   └─ No → SQL
    └─ Not sure? → Auto
```

### Performance Comparison

```
Query: "Average sales by region"
- SQL: 0.1 seconds ⚡
- Python: 2 seconds
- Deep Research: 45 seconds

Query: "Build prediction model"
- SQL: Not possible ❌
- Python: 60 seconds ✓
- Deep Research: 120 seconds (with full report)

Query: "Why are revenues declining?"
- SQL: Partial answer
- Python: Partial answer
- Deep Research: Comprehensive answer ✓
```

## Mode Switching

You can switch modes anytime:

1. Click mode buttons in chat sidebar
2. Or use keywords in your query:
   - "using SQL show me..."
   - "with Python calculate..."
   - "deep dive into..."

## Best Practices

1. **Start with Auto** - Let Felix choose
2. **Use SQL for speed** - When you know it's a simple query
3. **Python for accuracy** - When you need precise statistics or ML
4. **Deep Research for insights** - When you need comprehensive understanding

## Next Steps

- Learn [Python Analysis](./python-analysis.md) in detail
- Explore [Deep Research](./deep-research.md) capabilities
- Check [API Reference](./api-reference.md) for programmatic access
