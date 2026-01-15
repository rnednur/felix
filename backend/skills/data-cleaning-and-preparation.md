---
name: data-cleaning-and-preparation
display_name: Data Cleaning and Preparation
version: 1.0.0
scope: task
tags: [data-cleaning, preprocessing, quality, transformation, etl]
description: Best practices for cleaning and preparing data for analysis
author: AI Analytics Platform
---

# Data Cleaning and Preparation

## Overview

Data cleaning is often 60-80% of the analysis effort. This skill provides systematic approaches to identifying and resolving data quality issues.

## Data Quality Assessment

### Initial Data Inspection

**First steps when receiving new data:**

1. **Check dimensions:**
```python
print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
```

2. **Examine structure:**
```python
df.info()  # Data types, null counts
df.head(10)  # First rows
df.tail(10)  # Last rows
df.sample(20)  # Random sample
```

3. **Summary statistics:**
```python
df.describe()  # Numeric columns
df.describe(include='object')  # Categorical columns
```

4. **Check for duplicates:**
```python
duplicates = df.duplicated().sum()
duplicate_rows = df[df.duplicated(keep=False)]
```

### Common Data Quality Issues

**Issue checklist:**
- ☑ Missing values (NULL, NaN, empty strings)
- ☑ Duplicates (exact or fuzzy)
- ☑ Inconsistent formatting (dates, names, categories)
- ☑ Invalid values (negative ages, future dates)
- ☑ Outliers (extreme values)
- ☑ Wrong data types (numbers as strings)
- ☑ Encoding issues (special characters)
- ☑ Inconsistent categories ("USA" vs "United States")

## Missing Data

### Types of Missing Data

**MCAR (Missing Completely At Random):**
- Missingness unrelated to any variable
- Safest to handle with deletion or simple imputation

**MAR (Missing At Random):**
- Missingness related to observed variables
- Can use model-based imputation

**MNAR (Missing Not At Random):**
- Missingness related to the missing value itself
- Most problematic, requires domain knowledge

### Handling Strategies

**1. Deletion**

```python
# Remove rows with any missing values
df_clean = df.dropna()

# Remove rows with missing values in specific columns
df_clean = df.dropna(subset=['important_col1', 'important_col2'])

# Remove columns with >50% missing
threshold = len(df) * 0.5
df_clean = df.dropna(axis=1, thresh=threshold)
```

**Use when:** Small percentage of missing data (<5%), MCAR

**2. Simple Imputation**

```python
# Mean/median for numeric columns
df['age'].fillna(df['age'].median(), inplace=True)

# Mode for categorical columns
df['category'].fillna(df['category'].mode()[0], inplace=True)

# Forward fill (carry last value forward)
df['sensor_reading'].fillna(method='ffill', inplace=True)

# Backward fill
df['sensor_reading'].fillna(method='bfill', inplace=True)
```

**Use when:** Moderate missing data, simple patterns

**3. Indicator Variables**

```python
# Create indicator for missingness
df['age_missing'] = df['age'].isna().astype(int)
df['age'].fillna(df['age'].median(), inplace=True)
```

**Use when:** Missingness itself may be informative

**4. Model-Based Imputation**

```python
from sklearn.impute import KNNImputer

imputer = KNNImputer(n_neighbors=5)
df_imputed = pd.DataFrame(
    imputer.fit_transform(df[numeric_cols]),
    columns=numeric_cols
)
```

**Use when:** MAR, multiple correlated variables

## Duplicate Removal

### Exact Duplicates

```python
# Find exact duplicates
df[df.duplicated(keep=False)]

# Remove duplicates (keep first occurrence)
df_clean = df.drop_duplicates()

# Remove duplicates based on specific columns
df_clean = df.drop_duplicates(subset=['customer_id', 'date'])
```

### Fuzzy Duplicates

For near-duplicates (typos, formatting differences):

```python
# Example: Similar names
from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio() > 0.9

# Group similar entries
# (More complex implementation needed for real use)
```

**Common causes:**
- Typos: "Jhon" vs "John"
- Case differences: "USA" vs "usa"
- Extra spaces: "New York " vs "New York"
- Different formats: "2024-01-01" vs "01/01/2024"

## Data Type Conversion

### String to Numeric

```python
# Remove $ and commas, convert to float
df['price'] = df['price'].str.replace('$', '').str.replace(',', '').astype(float)

# Handle errors gracefully
df['age'] = pd.to_numeric(df['age'], errors='coerce')  # Invalid -> NaN
```

### Date Parsing

```python
# Parse dates
df['date'] = pd.to_datetime(df['date'])

# Handle multiple formats
df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')

# Extract components
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day_of_week'] = df['date'].dt.dayofweek
```

### Categorical Encoding

```python
# Standardize categories (lowercase, strip spaces)
df['category'] = df['category'].str.lower().str.strip()

# Map inconsistent values
category_mapping = {
    'usa': 'United States',
    'us': 'United States',
    'america': 'United States'
}
df['country'] = df['country'].replace(category_mapping)
```

## Outlier Detection and Handling

### Statistical Methods

**IQR Method:**
```python
Q1 = df['value'].quantile(0.25)
Q3 = df['value'].quantile(0.75)
IQR = Q3 - Q1

lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

outliers = df[(df['value'] < lower_bound) | (df['value'] > upper_bound)]
```

**Z-Score Method:**
```python
from scipy import stats

z_scores = np.abs(stats.zscore(df['value']))
outliers = df[z_scores > 3]  # More than 3 standard deviations
```

### Handling Strategies

**1. Keep (if valid):**
- Outliers may be real, important data points
- Example: Billionaires in income data

**2. Cap (winsorize):**
```python
# Cap at percentiles
df['value_capped'] = df['value'].clip(
    lower=df['value'].quantile(0.01),
    upper=df['value'].quantile(0.99)
)
```

**3. Transform:**
```python
# Log transformation reduces impact of outliers
df['value_log'] = np.log1p(df['value'])  # log(1 + x)
```

**4. Remove:**
```python
df_clean = df[(df['value'] >= lower_bound) & (df['value'] <= upper_bound)]
```

**⚠️ Always investigate outliers before removing!**

## Data Standardization

### Text Standardization

```python
# Lowercase
df['text'] = df['text'].str.lower()

# Remove leading/trailing whitespace
df['text'] = df['text'].str.strip()

# Remove extra spaces
df['text'] = df['text'].str.replace(r'\s+', ' ', regex=True)

# Remove special characters
df['text'] = df['text'].str.replace(r'[^a-zA-Z0-9\s]', '', regex=True)
```

### Numeric Standardization

```python
# Standardization (z-score normalization)
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
df['value_standardized'] = scaler.fit_transform(df[['value']])

# Min-Max normalization (0-1 range)
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()
df['value_normalized'] = scaler.fit_transform(df[['value']])
```

### Date/Time Standardization

```python
# Standardize to UTC
df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

# Align to common interval (e.g., daily)
df['date'] = df['timestamp'].dt.date
```

## Data Validation

### Define Validation Rules

```python
def validate_data(df):
    issues = []

    # Check age range
    if (df['age'] < 0).any() or (df['age'] > 120).any():
        issues.append("Invalid age values detected")

    # Check date range
    if (df['date'] > pd.Timestamp.now()).any():
        issues.append("Future dates detected")

    # Check required fields
    required_fields = ['customer_id', 'date', 'amount']
    for field in required_fields:
        if df[field].isna().any():
            issues.append(f"Missing values in required field: {field}")

    # Check value ranges
    if (df['amount'] < 0).any():
        issues.append("Negative amounts detected")

    return issues

issues = validate_data(df)
if issues:
    print("Data quality issues:")
    for issue in issues:
        print(f"  - {issue}")
```

## Transformation Patterns

### Creating Derived Features

```python
# Binning continuous variables
df['age_group'] = pd.cut(df['age'],
                          bins=[0, 18, 35, 50, 65, 100],
                          labels=['<18', '18-35', '36-50', '51-65', '65+'])

# Aggregating to higher level
df['year_month'] = df['date'].dt.to_period('M')

# Combining columns
df['full_name'] = df['first_name'] + ' ' + df['last_name']

# Calculating ratios
df['profit_margin'] = (df['revenue'] - df['cost']) / df['revenue']
```

### Reshaping Data

```python
# Pivot (wide to long)
df_long = df.melt(
    id_vars=['id', 'date'],
    value_vars=['sales_q1', 'sales_q2', 'sales_q3', 'sales_q4'],
    var_name='quarter',
    value_name='sales'
)

# Unpivot (long to wide)
df_wide = df_long.pivot(
    index='id',
    columns='quarter',
    values='sales'
)
```

## Best Practices

1. **Document everything:** Keep a log of all cleaning steps
2. **Never modify original data:** Work on copies
3. **Be systematic:** Follow a checklist, don't clean ad-hoc
4. **Validate after cleaning:** Check results match expectations
5. **Preserve data lineage:** Track transformations for reproducibility
6. **Domain knowledge is key:** Understand the data context
7. **Automate when possible:** Create reusable cleaning pipelines
8. **Version your data:** Track data versions alongside code
9. **Profile before and after:** Compare statistics pre/post cleaning
10. **Communicate issues:** Report data quality problems to source

## Data Cleaning Pipeline Template

```python
def clean_data(df_raw):
    """Complete data cleaning pipeline"""
    df = df_raw.copy()

    # 1. Initial assessment
    print("Initial shape:", df.shape)
    print("Missing values:\n", df.isna().sum())

    # 2. Remove duplicates
    df = df.drop_duplicates()
    print(f"After dedup: {df.shape}")

    # 3. Handle missing values
    # (Strategy depends on your data)
    df = df.dropna(subset=['critical_column'])
    df['optional_column'].fillna(df['optional_column'].median(), inplace=True)

    # 4. Fix data types
    df['date'] = pd.to_datetime(df['date'])
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')

    # 5. Standardize formats
    df['category'] = df['category'].str.lower().str.strip()

    # 6. Validate
    issues = validate_data(df)
    if issues:
        raise ValueError(f"Data validation failed: {issues}")

    # 7. Remove outliers (if appropriate)
    # df = remove_outliers(df, column='value')

    print("Final shape:", df.shape)
    return df

df_clean = clean_data(df_raw)
```

## Warnings

⚠️ **Never delete the original data:** Always work on copies

⚠️ **Beware of data leakage:** Don't use information from test set during cleaning

⚠️ **Document your decisions:** Why you removed/imputed certain values

⚠️ **Outliers may be valid:** Investigate before removing

⚠️ **Imputation introduces bias:** Document assumptions

⚠️ **Automated cleaning can hide issues:** Always inspect results

⚠️ **One size doesn't fit all:** Cleaning strategies depend on context

## Resources

- Pandas Documentation: https://pandas.pydata.org/docs/
- Data Cleaning with Python: Common Patterns and Best Practices
- Understanding Data Quality Dimensions
- scikit-learn Preprocessing Documentation
