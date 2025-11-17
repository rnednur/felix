# Felix User Guide

Complete guide to using Felix for data analytics and insights.

## Overview

Felix is an AI-powered analytics platform that lets you analyze data using natural language. Simply upload your dataset and ask questions - Felix generates the SQL queries, Python code, and visualizations automatically.

## Interface Components

### 1. Chat Sidebar (Left)

The chat sidebar is your main interaction point with Felix.

**Features**:
- Ask questions in natural language
- View conversation history
- Quick action suggestions
- Mode selector (Auto, SQL, Python, Deep Research)

**Tips**:
- Press Enter to send messages
- Previous questions are saved in the conversation
- Use suggested prompts for inspiration

### 2. Main Content Area (Right)

The main area has several tabs:

#### Spreadsheet Tab
- View raw dataset (first 100 rows)
- Browse all columns
- See data exactly as uploaded

#### Schema Tab
- Column names and data types
- Statistical summaries (min, max, mean, etc.)
- Top values for categorical columns
- Missing value information
- Data quality indicators

#### Dashboard Tab
- Query results from SQL queries
- Automatically generated charts
- Interactive data tables
- Visual insights

#### Report Tab
- Deep Research analysis reports
- Comprehensive findings
- Multiple visualizations
- Downloadable PDF reports

#### Code Tab
- Generated SQL or Python code
- Execution status and results
- Performance metrics
- Output data and visualizations

## Uploading Datasets

### Supported Formats

- **CSV** (.csv): Comma-separated values
- **Excel** (.xlsx, .xls): Microsoft Excel files
- **Parquet** (.parquet): Apache Parquet columnar format

### Size Limits

- Maximum file size: **100MB**
- Maximum rows: **100,000** (for optimal performance)
- For larger datasets, consider aggregating or filtering before upload

### Upload Process

1. Click **Upload Dataset** button or drag & drop file
2. Felix automatically:
   - Detects column types
   - Generates statistics
   - Creates embeddings for semantic search
   - Prepares data for fast querying

### Best Practices

- **Clean column names**: Use descriptive names without special characters
- **Consistent formatting**: Dates in standard format (MM/DD/YYYY)
- **Remove duplicates**: Pre-clean data for better results
- **Include headers**: First row should contain column names

## Asking Questions

### Query Types

#### Basic Queries
```
Show me the first 10 rows
How many records are there?
What columns are in this dataset?
```

#### Aggregation Queries
```
What's the total sales by region?
Count customers by country
Average order value by month
```

#### Filtering Queries
```
Show customers with revenue > $10,000
Find all orders from 2023
List products with price between $50 and $100
```

#### Analysis Queries
```
Top 10 products by profit margin
Compare sales across quarters
Which categories have the highest growth?
```

#### Advanced Python Analysis
```
Perform exploratory data analysis
Calculate correlation between numeric columns
Identify outliers in the dataset
Build a prediction model for sales
Train a classifier to predict customer churn
```

#### Deep Research
```
Why are sales declining in Q3?
What factors drive customer retention?
Analyze the impact of pricing on revenue
Identify key trends and patterns
```

## Query Modes

### Auto Mode (✨)

Felix automatically determines whether to use SQL or Python.

**When to use**:
- Most queries (recommended default)
- Let Felix optimize the approach
- When unsure which mode to use

**How it works**:
- Analyzes your question
- Detects keywords (predict, model, correlation → Python)
- Defaults to SQL for speed when possible

### SQL Mode (🗄️)

Fast queries using DuckDB SQL engine.

**Best for**:
- Filtering and aggregations
- Counting and grouping
- Simple calculations
- Quick data exploration

**Advantages**:
- Very fast execution (< 1 second)
- Efficient for large datasets
- Direct database queries

**Example queries**:
```sql
-- Felix generates:
SELECT region, SUM(sales) as total_sales
FROM dataset
GROUP BY region
ORDER BY total_sales DESC
LIMIT 10
```

### Python Mode (🐍)

Advanced analysis using pandas, scikit-learn, and more.

**Best for**:
- Machine learning models
- Statistical analysis
- Data transformations
- Complex calculations
- Correlation analysis

**Supported libraries**:
- pandas, numpy
- scikit-learn (ML models)
- scipy (statistics)
- statsmodels (time series)
- matplotlib, seaborn (visualizations)
- prophet (forecasting)

**Example queries**:
```
Build a regression model to predict revenue
Calculate Pearson correlation between price and sales
Perform PCA dimensionality reduction
Train a random forest classifier
```

### Deep Research Mode (🧠)

Multi-stage comprehensive analysis.

**Best for**:
- Complex business questions
- Root cause analysis
- Comprehensive reports
- Multi-dimensional insights

**How it works**:
1. Breaks question into sub-questions
2. Runs multiple queries (SQL + Python)
3. Synthesizes findings
4. Generates report with visualizations
5. Provides follow-up recommendations

**Example queries**:
```
Why are sales declining?
What drives customer satisfaction?
Analyze seasonal patterns and trends
```

## Working with Results

### SQL Query Results

- **Dashboard Tab**: View results as table
- **Auto-generated charts**: Felix creates visualizations based on data type
- **Export**: Copy results or download as CSV

### Python Execution Results

Displayed in **Code Tab**:

- **Output**: Summary of findings
- **Metrics**: Model performance, statistics
- **Data**: Result tables and values
- **Visualizations**: Charts and plots
- **Code**: Review generated Python code

### Deep Research Reports

Shown in **Report Tab**:

- **Executive Summary**: Key findings
- **Visualizations**: Multiple charts
- **Supporting Details**: All queries and results
- **Follow-up Questions**: Recommended next analyses
- **Download PDF**: Export complete report

## Dataset Overview

Click **Describe Dataset** to get AI insights:

- Dataset structure and size
- Column breakdown (numeric, categorical, datetime)
- Data quality metrics
- AI-generated description
- Quick tips for analysis

## Advanced Features

### Code Review and Editing

1. View generated code in **Code Tab**
2. Copy code for external use
3. Understand Felix's approach
4. Learn SQL/Python from examples

### Error Recovery

Felix automatically fixes common errors:

- Missing imports
- Type mismatches
- Column name issues
- Data loading problems

If execution fails:
1. Felix attempts automatic fix
2. Retries up to 2 times
3. Shows detailed error if unable to fix

### Custom Analysis

For custom workflows:
1. Start with Felix-generated code
2. Copy to your IDE
3. Modify as needed
4. Run independently

## Best Practices

### 1. Start Simple
- Begin with basic queries
- Understand your data first
- Build complexity gradually

### 2. Use Dataset Overview
- Click "Describe Dataset" when starting
- Review Schema tab
- Check data quality

### 3. Be Specific
❌ "Analyze sales"
✅ "What are the top 5 products by revenue in 2023?"

### 4. Iterate
- Start with broad question
- Refine based on results
- Ask follow-ups

### 5. Check Your Data
- Verify column names in Schema tab
- Ensure date formats are consistent
- Look for missing values

### 6. Choose Right Mode
- Simple queries → SQL (fast)
- ML/Statistics → Python (powerful)
- Complex questions → Deep Research (comprehensive)

## Keyboard Shortcuts

- `Enter` - Send message
- `Cmd/Ctrl + K` - Focus chat input
- `Esc` - Close modals

## Tips & Tricks

1. **Use natural language**: Felix understands conversational queries
2. **Mention column names**: "Show me sales by product_category"
3. **Specify time periods**: "in 2023", "last quarter", "this month"
4. **Ask for visualizations**: "show as chart", "plot the trend"
5. **Request specific formats**: "as percentage", "rounded to 2 decimals"

## Next Steps

- Learn about [Query Modes](./query-modes.md) in detail
- Explore [Python Analysis](./python-analysis.md) for ML
- Try [Deep Research](./deep-research.md) for insights
- Check [API Reference](./api-reference.md) for integration
