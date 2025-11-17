# Deep Research Mode in Felix

Deep Research is Felix's most powerful analysis mode, designed to answer complex business questions through multi-stage comprehensive analysis.

## Overview

Deep Research Mode breaks down complex questions into multiple sub-analyses, executes them in parallel, and synthesizes findings into a comprehensive report with visualizations and actionable insights.

## When to Use Deep Research

### Ideal Use Cases

✅ **Complex Business Questions**
```
Why are sales declining in Q3?
What factors drive customer churn?
How can we improve customer retention?
What causes seasonal variations in demand?
```

✅ **Root Cause Analysis**
```
Why did revenue drop last month?
What's causing the increase in support tickets?
Why are conversion rates declining?
What's impacting customer satisfaction?
```

✅ **Strategic Insights**
```
What are the key drivers of profitability?
How do different customer segments behave?
What trends should we focus on?
Which products have growth potential?
```

✅ **Comprehensive Reports**
- Board presentations
- Executive summaries
- Quarterly business reviews
- Strategic planning

### When NOT to Use

❌ Simple queries → Use SQL
❌ Single ML model → Use Python
❌ Quick data check → Use Auto mode
❌ Time-sensitive queries → Use SQL or Python (faster)

## How It Works

### 1. Question Decomposition

Felix analyzes your question and breaks it into specific sub-questions.

**Example**:
```
User: "Why are sales declining in Q3?"

Felix generates:
1. What is the overall sales trend?
2. How do Q3 sales compare to previous quarters?
3. Which product categories show decline?
4. Which regions are most affected?
5. Are there seasonal patterns?
6. How does customer behavior differ in Q3?
7. What external factors might contribute?
```

### 2. Analysis Planning

Felix decides which analysis method to use for each sub-question.

```
Sub-Question → Analysis Method

"Overall sales trend" → SQL aggregation
"Product category performance" → SQL group by
"Seasonal patterns" → Python time series
"Customer behavior analysis" → Python segmentation
"Predictive factors" → Python correlation
```

### 3. Parallel Execution

All analyses run in parallel for speed:

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  SQL Query  │  │  SQL Query  │  │   Python    │
│   #1        │  │   #2        │  │   Analysis  │
└─────────────┘  └─────────────┘  └─────────────┘
      ↓                ↓                 ↓
    Results         Results          Results
      └────────────────┴─────────────────┘
                       ↓
               Synthesis & Report
```

### 4. Results Synthesis

Felix analyzes all findings to draw conclusions:

- Identifies patterns across analyses
- Correlates findings
- Detects causal relationships
- Highlights key insights

### 5. Report Generation

Comprehensive report with:
- Executive summary
- Key findings
- Supporting visualizations
- Detailed analysis breakdown
- Follow-up recommendations

## Report Structure

### 1. Header

```
Deep Research Report
Date: [Current date]
Question: [Your original question]
Execution Time: [X.X seconds]
Analyses Performed: [N sub-questions]
Visualizations: [M charts]
```

### 2. Executive Summary

**One-paragraph answer** to your question:

```
Example:
Sales are declining in Q3 primarily due to a 23% drop in the
Electronics category, concentrated in the Northeast region.
Analysis reveals strong seasonal patterns, with Q3 historically
showing 15-20% lower demand. Customer purchase frequency has
decreased 18% compared to Q2, while average order value remains
stable. Recommendation: Focus promotional efforts on Electronics
and target Northeast customers with Q3-specific campaigns.
```

### 3. Key Findings

Numbered list of insights:

```
1. Electronics category sales decreased 23% compared to Q2
2. Northeast region shows 31% decline, other regions stable
3. Customer purchase frequency down 18%, suggesting engagement issue
4. Average order value stable at $127, indicating pricing not the issue
5. Historical data shows consistent Q3 seasonality (15-20% dip)
```

### 4. Visualizations

Charts embedded in report:

- Trend lines (sales over time)
- Regional comparisons (bar charts)
- Category breakdowns (pie charts)
- Correlation heatmaps
- Prediction plots

### 5. Data Coverage

Transparency about analysis:

```
Questions Answered: 8/10
Successful Queries: 8
Failed Queries: 2

Data Gaps Identified:
- Customer demographic data not available
- External market data not included
```

### 6. Research Details

Expandable sections for each analysis:

```
[Collapsible Section] Analysis #1: Overall Sales Trend
  Question: What is the overall sales trend?
  Method: SQL
  Status: ✓ Success

  [Show SQL Query]
  [Show Results Table]
  [Show Visualization]
```

### 7. Follow-up Questions

Recommended next analyses:

```
Consider exploring these questions for deeper insights:

1. What specific product SKUs in Electronics are declining most?
2. What's the customer retention rate in the Northeast region?
3. How does Q3 performance compare year-over-year?
4. What marketing campaigns ran during Q3?
5. Can we predict Q4 sales based on current trends?
```

## Example Deep Research

### Question: "Why are sales declining in Q3?"

#### Sub-Questions Generated

1. **Overall Trend Analysis**
   ```sql
   SELECT
     quarter,
     SUM(sales) as total_sales,
     COUNT(*) as num_orders
   FROM dataset
   GROUP BY quarter
   ORDER BY quarter
   ```

2. **Regional Breakdown**
   ```sql
   SELECT
     region,
     SUM(CASE WHEN quarter = 'Q3' THEN sales END) as q3_sales,
     SUM(CASE WHEN quarter = 'Q2' THEN sales END) as q2_sales,
     ((q3_sales - q2_sales) / q2_sales * 100) as pct_change
   FROM dataset
   GROUP BY region
   ```

3. **Category Analysis**
   ```python
   # Python analysis for category trends
   df_categories = df.groupby(['quarter', 'category']).agg({
       'sales': 'sum',
       'order_id': 'count'
   }).reset_index()

   # Calculate quarter-over-quarter change
   ```

4. **Customer Behavior**
   ```python
   # Customer frequency analysis
   customer_stats = df.groupby(['customer_id', 'quarter']).agg({
       'order_id': 'count',
       'sales': 'mean'
   }).reset_index()

   # Compare Q2 vs Q3 behavior
   ```

5. **Seasonal Patterns**
   ```python
   # Time series decomposition
   from statsmodels.tsa.seasonal import seasonal_decompose

   ts_data = df.groupby('date')['sales'].sum()
   decomposition = seasonal_decompose(ts_data, period=365)
   ```

#### Sample Report Output

**Executive Summary**:
> Sales declined 17% in Q3 compared to Q2, driven primarily by a 23%
> drop in Electronics ($2.1M lost revenue) and concentrated in the
> Northeast region (-31%). Analysis reveals strong seasonal patterns
> with Q3 historically 15-20% below Q2. Customer purchase frequency
> decreased 18% while average order value remained stable at $127,
> suggesting retention rather than pricing issues.

**Key Findings**:
1. Overall Q3 sales: $9.8M (down from $11.8M in Q2, -17%)
2. Electronics category: -23% ($2.1M decrease)
3. Northeast region: -31% decline; other regions: -8% average
4. Customer frequency: -18%; Average order value: stable
5. Historical Q3 pattern: 15-20% dip is normal
6. Customer cohort from Q1/Q2 showing reduced activity
7. Seasonal decomposition confirms cyclical pattern

**Recommended Actions**:
1. Launch targeted Q3 promotional campaigns for Electronics
2. Increase customer engagement programs in Northeast
3. Investigate why Q1/Q2 customers are less active in Q3
4. Plan for recurring Q3 seasonality in future forecasts

## Performance

### Execution Time

| Complexity | Sub-Questions | Time |
|------------|---------------|------|
| Simple | 3-5 | 30-60 seconds |
| Medium | 5-10 | 60-120 seconds |
| Complex | 10-15 | 120-180 seconds |

### Resource Usage

- Runs queries in parallel for speed
- Limits concurrent executions to 5
- Handles failures gracefully
- Continues even if some queries fail

## Report Features

### PDF Export

Download professional reports:

1. Click "Download PDF" in Report tab
2. Opens browser print dialog
3. Select "Save as PDF"
4. Only report content (no sidebar/UI)

**PDF includes**:
- All sections
- Embedded visualizations
- Formatted tables
- Page breaks for readability

### Sharing

Reports can be:
- Downloaded as PDF
- Screenshots shared
- Copied for presentations
- Embedded in documents

## Advanced Features

### Error Handling

Deep Research is resilient:

```
If analysis fails:
1. Logs failure reason
2. Continues with other analyses
3. Reports partial results
4. Indicates data gaps in report
5. Suggests alternative approaches
```

### Data Quality Checks

```
Before synthesis, Felix validates:
- Sufficient data for conclusions
- Consistent results across queries
- Statistical significance
- No contradictory findings
```

### Adaptive Analysis

```
Based on initial results, Felix may:
- Add follow-up queries
- Drill deeper into anomalies
- Expand analysis scope
- Adjust granularity
```

## Best Practices

### 1. Ask Open-Ended Questions

✅ Good:
```
Why are customers churning?
What drives our profitability?
How can we improve conversion rates?
```

❌ Too Specific (use SQL instead):
```
How many customers churned last month?
What's our profit margin?
What's our conversion rate?
```

### 2. Provide Context

Better results with context:

```
Instead of: "Why are sales down?"
Try: "Why are e-commerce sales declining compared to last quarter?"
```

### 3. Be Patient

- Deep Research takes 1-3 minutes
- Progress shown in real-time
- Don't interrupt execution

### 4. Review Full Report

- Don't just read summary
- Expand research details
- Check visualizations
- Review follow-ups

### 5. Iterate

Use follow-up questions:

```
Initial: "Why are sales declining?"
→ Report identifies regional issues

Follow-up: "What's different about customer behavior in the Northeast region?"
→ Deeper dive into specific finding
```

## Limitations

### What Deep Research Can't Do

❌ **Real-time predictions**: Not for operational decisions
❌ **External data**: Only analyzes uploaded dataset
❌ **Causal proof**: Shows correlations, not causation
❌ **Expert domain knowledge**: Statistical insights only

### Data Requirements

Minimum requirements:
- At least 1000 rows
- Multiple dimensions (columns)
- Time-based data for trend analysis
- Numerical metrics for aggregation

### Time Constraints

- Maximum execution: 5 minutes
- Individual query timeout: 120 seconds
- Suitable for analysis, not real-time operations

## Example Use Cases

### Business Performance

```
"Why did revenue decrease last quarter?"
"What's driving our margin compression?"
"How do our top customers differ from others?"
```

### Customer Insights

```
"What factors lead to customer churn?"
"Why do some customers spend more than others?"
"What makes our most loyal customers different?"
```

### Product Analysis

```
"Which products should we discontinue?"
"What drives product returns?"
"Why do some products have better margins?"
```

### Operational Excellence

```
"What's causing delivery delays?"
"Why are support tickets increasing?"
"What factors impact order fulfillment time?"
```

## Tips for Great Reports

### 1. Specific Time Periods

```
Better: "Why are sales declining in Q3 2023?"
vs: "Why are sales declining?"
```

### 2. Comparative Questions

```
Better: "What's different between high-value and low-value customers?"
vs: "Tell me about customers"
```

### 3. Actionable Focus

```
Better: "What can we do to improve retention?"
vs: "What's our retention rate?"
```

## Next Steps

- Review [Python Analysis](./python-analysis.md) for ML details
- Check [Query Modes](./query-modes.md) for mode selection
- Read [API Reference](./api-reference.md) for automation
