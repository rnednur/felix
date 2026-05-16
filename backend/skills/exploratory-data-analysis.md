---
name: exploratory-data-analysis
display_name: Exploratory Data Analysis (EDA)
version: 1.0.0
scope: workflow
tags: [eda, exploration, analysis, visualization, statistics]
description: Systematic approach to exploring and understanding new datasets
author: AI Analytics Platform
---

# Exploratory Data Analysis (EDA)

## Overview

EDA is the process of investigating data to discover patterns, spot anomalies, test hypotheses, and check assumptions using summary statistics and visualizations.

## EDA Framework

### Phase 1: Understanding the Data

**Questions to answer:**
- What is the source of the data?
- What do rows and columns represent?
- What time period does it cover?
- How was the data collected?
- What is the grain (level of detail)?

**Initial exploration:**
```python
# Basic info
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print(f"Data types:\n{df.dtypes}")

# Sample rows
print(df.head())
print(df.sample(10))

# Memory usage
print(df.memory_usage(deep=True))
```

### Phase 2: Univariate Analysis

**Analyze each variable individually.**

**For numeric variables:**

```python
# Summary statistics
df['sales'].describe()

# Distribution visualization
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 4))

# Histogram
plt.subplot(1, 2, 1)
plt.hist(df['sales'], bins=30, edgecolor='black')
plt.xlabel('Sales')
plt.ylabel('Frequency')
plt.title('Distribution of Sales')

# Box plot
plt.subplot(1, 2, 2)
plt.boxplot(df['sales'])
plt.ylabel('Sales')
plt.title('Sales Box Plot')

plt.tight_layout()
plt.show()
```

**Key questions:**
- What is the central tendency (mean, median)?
- What is the spread (std, IQR)?
- Is the distribution normal, skewed, or bimodal?
- Are there outliers?
- Are there any unexpected values?

**For categorical variables:**

```python
# Frequency counts
df['category'].value_counts()

# Proportions
df['category'].value_counts(normalize=True)

# Bar chart
df['category'].value_counts().plot(kind='bar')
plt.xlabel('Category')
plt.ylabel('Count')
plt.title('Distribution of Categories')
plt.xticks(rotation=45)
plt.show()
```

**Key questions:**
- How many unique values?
- What is the distribution across categories?
- Are there rare categories?
- Are there typos or inconsistencies?

### Phase 3: Bivariate Analysis

**Explore relationships between two variables.**

**Numeric vs Numeric:**

```python
# Scatter plot
plt.scatter(df['x'], df['y'], alpha=0.5)
plt.xlabel('X Variable')
plt.ylabel('Y Variable')
plt.title('X vs Y Relationship')
plt.show()

# Correlation
correlation = df['x'].corr(df['y'])
print(f"Correlation: {correlation:.3f}")

# For many variables: correlation matrix
correlation_matrix = df[numeric_cols].corr()
import seaborn as sns
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
plt.title('Correlation Matrix')
plt.show()
```

**Categorical vs Numeric:**

```python
# Box plot by category
df.boxplot(column='sales', by='region')
plt.xlabel('Region')
plt.ylabel('Sales')
plt.title('Sales Distribution by Region')
plt.suptitle('')  # Remove default title
plt.show()

# Group statistics
df.groupby('region')['sales'].describe()

# Bar chart of means
df.groupby('region')['sales'].mean().plot(kind='bar')
plt.ylabel('Average Sales')
plt.xlabel('Region')
plt.title('Average Sales by Region')
plt.show()
```

**Categorical vs Categorical:**

```python
# Contingency table
contingency = pd.crosstab(df['region'], df['product_type'])
print(contingency)

# Heatmap
sns.heatmap(contingency, annot=True, fmt='d', cmap='YlOrRd')
plt.title('Region vs Product Type')
plt.show()

# Proportions
pd.crosstab(df['region'], df['product_type'], normalize='index')
```

### Phase 4: Multivariate Analysis

**Explore interactions between 3+ variables.**

**Three variables:**

```python
# Scatter with color by category
import matplotlib.pyplot as plt

for category in df['category'].unique():
    subset = df[df['category'] == category]
    plt.scatter(subset['x'], subset['y'], label=category, alpha=0.6)

plt.xlabel('X Variable')
plt.ylabel('Y Variable')
plt.legend()
plt.title('X vs Y by Category')
plt.show()

# Bubble chart (x, y, size)
plt.scatter(df['x'], df['y'], s=df['size']*10, alpha=0.5)
plt.xlabel('X Variable')
plt.ylabel('Y Variable')
plt.title('X vs Y (bubble size = Z)')
plt.show()
```

**Many variables:**

```python
# Pair plot (requires seaborn)
import seaborn as sns
sns.pairplot(df[numeric_cols], diag_kind='kde')
plt.show()

# Parallel coordinates
from pandas.plotting import parallel_coordinates
parallel_coordinates(df, 'category', color=['red', 'blue', 'green'])
plt.title('Parallel Coordinates Plot')
plt.show()
```

### Phase 5: Time Series Analysis

**If data has temporal dimension:**

```python
# Ensure datetime index
df['date'] = pd.to_datetime(df['date'])
df_ts = df.set_index('date').sort_index()

# Plot time series
df_ts['sales'].plot(figsize=(12, 4))
plt.xlabel('Date')
plt.ylabel('Sales')
plt.title('Sales Over Time')
plt.show()

# Decomposition
from statsmodels.tsa.seasonal import seasonal_decompose
decomposition = seasonal_decompose(df_ts['sales'], model='additive', period=12)
decomposition.plot()
plt.show()

# Rolling statistics
df_ts['sales_ma_7'] = df_ts['sales'].rolling(window=7).mean()
df_ts['sales_ma_30'] = df_ts['sales'].rolling(window=30).mean()

df_ts[['sales', 'sales_ma_7', 'sales_ma_30']].plot(figsize=(12, 4))
plt.title('Sales with Moving Averages')
plt.show()
```

## Common EDA Patterns

### Pattern 1: Identifying Data Quality Issues

```python
def data_quality_report(df):
    """Generate comprehensive data quality report"""
    print("="*60)
    print("DATA QUALITY REPORT")
    print("="*60)

    # Missing values
    print("\nMissing Values:")
    missing = df.isna().sum()
    missing_pct = 100 * missing / len(df)
    missing_df = pd.DataFrame({
        'Missing': missing,
        'Percent': missing_pct
    })
    print(missing_df[missing_df['Missing'] > 0])

    # Duplicates
    dup_count = df.duplicated().sum()
    print(f"\nDuplicate Rows: {dup_count} ({100*dup_count/len(df):.2f}%)")

    # Data types
    print("\nData Types:")
    print(df.dtypes.value_counts())

    # Cardinality
    print("\nCardinality (unique values):")
    for col in df.columns:
        n_unique = df[col].nunique()
        print(f"  {col}: {n_unique} unique values")

    # Outliers (numeric columns)
    print("\nPotential Outliers (Z-score > 3):")
    for col in df.select_dtypes(include=[np.number]).columns:
        z_scores = np.abs(stats.zscore(df[col].dropna()))
        n_outliers = (z_scores > 3).sum()
        if n_outliers > 0:
            print(f"  {col}: {n_outliers} outliers")

data_quality_report(df)
```

### Pattern 2: Comparing Groups

```python
def compare_groups(df, numeric_col, group_col):
    """Compare a numeric variable across groups"""

    # Summary statistics
    print(df.groupby(group_col)[numeric_col].describe())

    # Visualization
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Box plot
    df.boxplot(column=numeric_col, by=group_col, ax=axes[0])
    axes[0].set_title(f'{numeric_col} by {group_col}')

    # Violin plot (requires seaborn)
    sns.violinplot(data=df, x=group_col, y=numeric_col, ax=axes[1])
    axes[1].set_title(f'{numeric_col} Distribution by {group_col}')

    plt.tight_layout()
    plt.show()

    # Statistical test
    groups = [group[numeric_col].values for name, group in df.groupby(group_col)]
    f_stat, p_value = stats.f_oneway(*groups)
    print(f"\nANOVA F-statistic: {f_stat:.4f}, p-value: {p_value:.4f}")

    if p_value < 0.05:
        print("Significant difference between groups (p < 0.05)")
    else:
        print("No significant difference between groups (p >= 0.05)")

compare_groups(df, 'sales', 'region')
```

### Pattern 3: Identifying Relationships

```python
def analyze_relationships(df, target_col, feature_cols):
    """Analyze relationships between features and target"""

    print(f"Analyzing relationships with {target_col}")
    print("="*60)

    # Correlations
    print("\nCorrelations with target:")
    correlations = df[feature_cols + [target_col]].corr()[target_col].sort_values(ascending=False)
    print(correlations)

    # Visualize top correlations
    top_features = correlations.abs().nlargest(6).index[1:]  # Exclude target itself

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()

    for i, feature in enumerate(top_features):
        ax = axes[i]
        ax.scatter(df[feature], df[target_col], alpha=0.5)
        ax.set_xlabel(feature)
        ax.set_ylabel(target_col)
        ax.set_title(f'Correlation: {correlations[feature]:.3f}')

    plt.tight_layout()
    plt.show()

analyze_relationships(df, 'sales', numeric_cols)
```

## EDA Checklist

### Data Structure
- ☑ Number of rows and columns
- ☑ Column names and meanings
- ☑ Data types appropriate
- ☑ Index structure (especially for time series)

### Data Quality
- ☑ Missing values identified and understood
- ☑ Duplicates checked
- ☑ Outliers identified
- ☑ Data ranges make sense
- ☑ Inconsistencies noted

### Distributions
- ☑ Numeric variables: shape, center, spread
- ☑ Categorical variables: frequencies, rare categories
- ☑ Identify skewness, multimodality
- ☑ Check for impossible values

### Relationships
- ☑ Correlations between numeric variables
- ☑ Group differences for categorical variables
- ☑ Time trends if applicable
- ☑ Interactions between variables

### Context
- ☑ Domain knowledge applied
- ☑ Data generation process understood
- ☑ Limitations acknowledged
- ☑ Hypotheses formulated

## Best Practices

1. **Start broad, then focus:** Get overall picture before diving deep
2. **Visualize early and often:** Plots reveal patterns statistics miss
3. **Document discoveries:** Keep notes on findings and questions
4. **Be systematic:** Follow a checklist to avoid missing important checks
5. **Question everything:** Challenge assumptions about the data
6. **Consider domain context:** Statistical patterns need business interpretation
7. **Iterate:** EDA is not linear; revisit earlier steps as you learn
8. **Collaborate:** Discuss findings with domain experts
9. **Use multiple views:** Different visualizations reveal different insights
10. **Save your work:** Keep scripts and notebooks for reproducibility

## Common Pitfalls

### Pitfall 1: Confirmation Bias

**Problem:** Only looking for patterns you expect to find.

**Solution:** Actively look for disconfirming evidence.

### Pitfall 2: Over-Interpreting Patterns

**Problem:** Seeing meaningful patterns in random noise.

**Solution:** Use statistical tests, consider sample size, replicate findings.

### Pitfall 3: Ignoring Data Quality

**Problem:** Analyzing without checking for errors, missing values, outliers.

**Solution:** Always start with data quality assessment.

### Pitfall 4: Skipping Univariate Analysis

**Problem:** Jumping straight to complex multivariate analysis.

**Solution:** Understand each variable individually first.

### Pitfall 5: Forgetting Domain Context

**Problem:** Drawing conclusions without domain knowledge.

**Solution:** Involve domain experts, research the context.

## EDA Report Template

```markdown
# Exploratory Data Analysis Report

## Dataset Overview
- **Source:** [Where data came from]
- **Time Period:** [Coverage]
- **Grain:** [What each row represents]
- **Dimensions:** [Rows x Columns]

## Data Quality Assessment
- **Missing Values:** [Summary]
- **Duplicates:** [Count and handling]
- **Outliers:** [Identified outliers]
- **Issues:** [Any data quality concerns]

## Key Findings

### Univariate Analysis
- [Variable 1]: [Distribution, summary stats, notable features]
- [Variable 2]: [Distribution, summary stats, notable features]
- ...

### Bivariate Analysis
- [Relationship 1]: [Description and strength]
- [Relationship 2]: [Description and strength]
- ...

### Multivariate Patterns
- [Pattern 1]: [Description]
- [Pattern 2]: [Description]
- ...

## Hypotheses for Testing
1. [Hypothesis 1]
2. [Hypothesis 2]
...

## Recommendations for Further Analysis
1. [Recommendation 1]
2. [Recommendation 2]
...

## Limitations
- [Limitation 1]
- [Limitation 2]
...
```

## Warnings

⚠️ **EDA is exploratory, not confirmatory:** Patterns need validation with new data

⚠️ **Multiple testing inflates false positives:** Don't run dozens of tests and report only significant ones

⚠️ **Correlation doesn't imply causation:** Need experiments or careful causal analysis

⚠️ **Sample may not represent population:** Consider sampling bias

⚠️ **Outliers may be valuable:** Don't automatically remove them

⚠️ **Visualizations can mislead:** Check axes, scales, and chart types carefully

## Resources

- Python Data Science Handbook (Jake VanderPlas)
- Pandas Visualization Documentation
- Seaborn Gallery: https://seaborn.pydata.org/examples/index.html
- Matplotlib Gallery: https://matplotlib.org/stable/gallery/index.html
- R4DS: Exploratory Data Analysis Chapter
