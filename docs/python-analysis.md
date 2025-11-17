# Python Analysis in Felix

Complete guide to using Felix's Python mode for machine learning, statistical analysis, and advanced data processing.

## Overview

Python mode allows you to perform sophisticated analysis that goes beyond simple SQL queries. Felix generates and executes Python code using industry-standard data science libraries.

## Available Libraries

### Data Manipulation
- **pandas**: DataFrame operations, transformations
- **numpy**: Numerical computing, arrays
- **duckdb**: Fast data loading and filtering

### Machine Learning
- **scikit-learn**: Classification, regression, clustering
- **xgboost**: Gradient boosting (advanced ML)
- **lightgbm**: Light gradient boosting
- **prophet**: Time series forecasting (Facebook)

### Statistics
- **scipy**: Statistical tests, distributions
- **statsmodels**: Time series, regression analysis

### Visualization
- **matplotlib**: Plotting and charts
- **seaborn**: Statistical visualizations

## Machine Learning

### Classification

Predict categorical outcomes (yes/no, categories, classes).

#### Example Queries

```
Build a model to predict customer churn
Train a classifier to identify high-value customers
Predict product category based on features
Classify emails as spam or not spam
```

#### Supported Algorithms

```python
# Logistic Regression
- Best for: Binary classification, interpretability
- Speed: Fast
- Example: "Predict if customer will churn (yes/no)"

# Random Forest Classifier
- Best for: Complex patterns, feature importance
- Speed: Medium
- Example: "Classify customers into segments"

# XGBoost Classifier
- Best for: High accuracy, competitions
- Speed: Medium-Slow
- Example: "Predict loan default with highest accuracy"

# Support Vector Machines (SVM)
- Best for: Small-medium datasets, non-linear patterns
- Speed: Slow
- Example: "Classify handwritten digits"
```

#### Output

Felix provides:
- **Model accuracy** (0-1 score)
- **Precision, Recall, F1-score**
- **Confusion matrix** (as visualization)
- **Feature importance** (which features matter most)
- **Prediction examples** on test data

### Regression

Predict continuous numerical values.

#### Example Queries

```
Predict house prices based on features
Forecast sales revenue for next month
Estimate delivery time based on distance
Build a model to predict customer lifetime value
```

#### Supported Algorithms

```python
# Linear Regression
- Best for: Linear relationships, interpretability
- Speed: Very Fast
- Example: "Predict price based on size"

# Random Forest Regressor
- Best for: Non-linear patterns, robustness
- Speed: Medium
- Example: "Predict sales based on multiple factors"

# XGBoost Regressor
- Best for: High accuracy, complex patterns
- Speed: Medium-Slow
- Example: "Predict house prices with best accuracy"

# Polynomial Regression
- Best for: Curved relationships
- Speed: Fast
- Example: "Model non-linear growth patterns"
```

#### Output

Felix provides:
- **R² score** (model fit, 0-1)
- **RMSE** (Root Mean Squared Error)
- **MAE** (Mean Absolute Error)
- **Actual vs Predicted** plot
- **Residual analysis**
- **Feature importance**

### Clustering

Group similar data points together (unsupervised learning).

#### Example Queries

```
Segment customers into 5 groups
Find natural groupings in the data
Cluster products by similarity
Identify customer personas
```

#### Supported Algorithms

```python
# K-Means
- Best for: Known number of clusters, spherical clusters
- Speed: Fast
- Example: "Group customers into 5 segments"

# DBSCAN
- Best for: Arbitrary shapes, outlier detection
- Speed: Medium
- Example: "Find natural clusters in location data"

# Hierarchical Clustering
- Best for: Tree-like relationships, small datasets
- Speed: Slow
- Example: "Build customer taxonomy"
```

#### Output

Felix provides:
- **Cluster assignments** for each record
- **Cluster sizes** and statistics
- **Silhouette score** (cluster quality)
- **Visualization** (2D projection if high-dimensional)
- **Cluster characteristics** (average values per cluster)

### Time Series Forecasting

Predict future values based on historical trends.

#### Example Queries

```
Forecast next 30 days of sales
Predict monthly revenue for Q4
Estimate future demand using Prophet
Forecast website traffic for next week
```

#### Supported Methods

```python
# Prophet (Facebook)
- Best for: Seasonal patterns, holidays, missing data
- Speed: Medium
- Example: "Forecast sales with weekly and yearly seasonality"

# ARIMA (via statsmodels)
- Best for: Stationary time series, short-term forecasts
- Speed: Medium-Slow
- Example: "Predict next month's stock price"

# Exponential Smoothing
- Best for: Trending data, simple forecasts
- Speed: Fast
- Example: "Forecast next quarter revenue"
```

#### Output

Felix provides:
- **Forecast values** with confidence intervals
- **Historical vs Predicted** plot
- **Trend and seasonality** components
- **Forecast accuracy** metrics (MAPE, MAE)
- **Future predictions** (next N periods)

## Statistical Analysis

### Correlation Analysis

Measure relationships between variables.

#### Example Queries

```
Calculate correlation between price and sales
Which features are most correlated with revenue?
Show correlation matrix for all numeric columns
Test if age and income are correlated
```

#### Methods

```python
# Pearson Correlation
- Measures: Linear relationships
- Range: -1 to +1
- Example: "Correlation between price and demand"

# Spearman Correlation
- Measures: Monotonic relationships (can be non-linear)
- Range: -1 to +1
- Example: "Rank correlation between variables"
```

#### Output

- Correlation coefficients
- P-values (statistical significance)
- Heatmap visualization
- Strong correlations highlighted

### Hypothesis Testing

Test statistical claims about your data.

#### Example Queries

```
Is there a significant difference in sales between regions?
Test if conversion rates differ by channel
Compare average order values across segments
Check if promotion increased sales significantly
```

#### Available Tests

```python
# T-Test
- Compares: Two group means
- Example: "Test if Group A sales > Group B sales"

# ANOVA
- Compares: Multiple group means
- Example: "Test if sales differ across 5 regions"

# Chi-Square Test
- Compares: Categorical distributions
- Example: "Test if churn rate differs by subscription type"

# Mann-Whitney U Test
- Compares: Non-normal distributions
- Example: "Test median differences (non-parametric)"
```

#### Output

- Test statistic value
- P-value (< 0.05 = significant)
- Confidence intervals
- Interpretation (significant or not)
- Effect size

### Distribution Analysis

Understand the shape and characteristics of your data.

#### Example Queries

```
Analyze distribution of order values
Check if revenue follows normal distribution
Identify outliers in the dataset
Show distribution of customer ages
```

#### Analyses

```python
# Normality Tests
- Shapiro-Wilk test
- Anderson-Darling test
- Q-Q plots

# Descriptive Statistics
- Mean, median, mode
- Std deviation, variance
- Skewness, kurtosis

# Outlier Detection
- IQR method
- Z-score method
- Isolation Forest
```

#### Output

- Histogram with fitted curve
- Box plots for outliers
- Statistical summary
- Outlier identification
- Distribution parameters

## Data Transformation

### Cleaning and Preprocessing

#### Example Queries

```
Clean and standardize the dataset
Handle missing values using imputation
Remove outliers from numeric columns
Normalize all features to 0-1 range
```

#### Operations

```python
# Missing Value Handling
- Drop rows/columns
- Mean/median imputation
- Forward/backward fill
- Predictive imputation

# Outlier Handling
- Remove extreme values
- Cap at percentiles
- Transform (log, sqrt)

# Encoding
- Label encoding (ordinal)
- One-hot encoding (nominal)
- Target encoding

# Scaling
- StandardScaler (mean=0, std=1)
- MinMaxScaler (0-1 range)
- RobustScaler (outlier-resistant)
```

### Feature Engineering

#### Example Queries

```
Create new features from existing columns
Extract date components (year, month, day)
Calculate rolling averages
Generate interaction features
```

#### Operations

```python
# Date Features
- Extract year, month, day, weekday
- Calculate day of week, quarter
- Time since event

# Aggregations
- Rolling mean/sum/std
- Lag features
- Cumulative sums

# Interactions
- Product of features
- Ratios and percentages
- Polynomial features

# Binning
- Discretize continuous variables
- Create categorical ranges
```

## Exploratory Data Analysis (EDA)

### Comprehensive Analysis

#### Example Query

```
Perform exploratory data analysis on this dataset
```

#### What Felix Generates

```python
1. Dataset Overview
   - Shape (rows × columns)
   - Column types
   - Memory usage

2. Statistical Summary
   - Descriptive stats for numeric columns
   - Value counts for categorical columns

3. Missing Values
   - Count and percentage per column
   - Visualization of missing patterns

4. Distributions
   - Histograms for numeric columns
   - Bar charts for categorical columns

5. Correlations
   - Correlation matrix
   - Heatmap visualization
   - Top correlated pairs

6. Outliers
   - Box plots
   - Outlier detection
   - Flagged extreme values

7. Relationships
   - Scatter plots (key pairs)
   - Pair plots (if < 10 columns)
```

## Visualizations

Felix automatically generates visualizations as part of Python analysis.

### Chart Types

```python
# Automatically created based on analysis:

Scatter Plots
- Actual vs Predicted (regression)
- Feature relationships

Bar Charts
- Feature importance
- Category comparisons
- Top N items

Line Charts
- Time series trends
- Forecast plots

Heatmaps
- Correlation matrices
- Confusion matrices

Box Plots
- Outlier detection
- Distribution comparison

Histograms
- Distribution analysis
- Frequency plots

Pie Charts
- Proportion analysis
- Category breakdown
```

### Visualization Format

All visualizations are:
- Base64-encoded PNG images
- 150 DPI (high quality)
- Properly sized for display
- Included in results automatically

## Code Structure

Felix generates clean, well-documented code:

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# 1. Load data efficiently using DuckDB
df = duckdb_conn.execute("""
    SELECT * FROM dataset
    WHERE category = 'Electronics'
    LIMIT 10000
""").df()

# 2. Preprocessing
# Handle missing values
df = df.fillna(df.mean())

# Feature engineering
df['price_per_unit'] = df['total_price'] / df['quantity']

# 3. Feature selection
X = df[['price', 'quantity', 'price_per_unit']]
y = df['will_purchase']

# 4. Train/test split (80/20)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 5. Model training
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 6. Evaluation
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

# 7. Visualization
# (matplotlib code to create charts)

# 8. Results
result = {
    'summary': f'Model accuracy: {accuracy:.3f}',
    'data': predictions.to_dict('records'),
    'metrics': {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall
    },
    'visualizations': [
        {'data': plot_base64, 'caption': 'Feature Importance'}
    ]
}
```

## Error Handling

Felix includes robust error handling:

### Automatic Fixes

```python
# Common errors automatically fixed:

1. Type Mismatches
   - Label encoder with mixed types
   → Converts to string first

2. Missing Imports
   - Adds required imports
   → Auto-installs if needed

3. Column Names
   - Fixes quote issues
   → Matches schema exactly

4. Data Loading
   - Ensures dataset loaded
   → Adds read_parquet if missing
```

### LLM-Based Fixes

If automatic fixes don't work:
1. Sends error to LLM
2. LLM analyzes code + error
3. Generates fixed version
4. Retries execution
5. Up to 2 retry attempts

### Error Messages

Clear, actionable error messages:
```
❌ Code execution failed
Error: ValueError: could not convert string to float

Attempted fix: Converting categorical columns to numeric
Status: Retrying... (attempt 2/3)
```

## Performance Optimization

### Data Loading

Felix uses DuckDB for efficient loading:

```python
# Instead of loading entire dataset:
df = pd.read_parquet(parquet_path)  # Slow for large data

# Felix generates filtered query:
df = duckdb_conn.execute("""
    SELECT * FROM dataset
    WHERE date >= '2023-01-01'
    AND category IN ('A', 'B', 'C')
    LIMIT 10000
""").df()  # Much faster!
```

### Execution Time

Typical execution times:

| Operation | Time |
|-----------|------|
| Data loading | 1-2 seconds |
| Simple stats | 1-5 seconds |
| ML model (1K rows) | 5-15 seconds |
| ML model (10K rows) | 15-60 seconds |
| ML model (100K rows) | 60-120 seconds |
| Deep learning | Not supported |

### Memory Limits

- Maximum memory: 1GB
- Timeout: 120 seconds
- Auto-terminates if exceeded

## Best Practices

### 1. Start Simple

```
❌ "Build a neural network to predict sales"
✅ "Build a regression model to predict sales"
```

### 2. Specify Details

```
❌ "Analyze correlation"
✅ "Calculate Pearson correlation between price and sales"
```

### 3. Check Data First

- Review Schema tab
- Ensure numeric columns are numeric
- Check for missing values

### 4. Iterate

```
Step 1: "Perform EDA"
Step 2: "Build model using top 3 correlated features"
Step 3: "Tune model with cross-validation"
```

### 5. Understand Results

- Review generated code in Code tab
- Check metrics and visualizations
- Validate predictions make sense

## Example Workflows

### ML Model Development

```
1. "Perform exploratory data analysis"
   → Understand data structure

2. "Show correlation with target variable revenue"
   → Identify important features

3. "Build regression model to predict revenue using top 5 features"
   → Train initial model

4. "Calculate feature importance"
   → Understand model decisions

5. "Show prediction examples for top 10 records"
   → Validate predictions
```

### Customer Segmentation

```
1. "Standardize all numeric features"
   → Prepare data

2. "Segment customers into 5 groups using K-means"
   → Perform clustering

3. "Show cluster characteristics and sizes"
   → Understand segments

4. "Visualize clusters using first 2 components"
   → View results

5. "Assign cluster labels to all customers"
   → Apply segmentation
```

## Next Steps

- Try [Deep Research](./deep-research.md) for comprehensive analysis
- Check [API Reference](./api-reference.md) for programmatic access
- Read [Configuration](./configuration.md) to customize settings
