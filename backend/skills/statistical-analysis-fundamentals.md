---
name: statistical-analysis-fundamentals
display_name: Statistical Analysis Fundamentals
version: 1.0.0
scope: task
tags: [statistics, analysis, data-science, hypothesis-testing, correlation]
description: Core statistical concepts and methods for data analysis
author: AI Analytics Platform
---

# Statistical Analysis Fundamentals

## Overview

This skill provides guidance on applying fundamental statistical methods correctly, interpreting results, and avoiding common pitfalls.

## Descriptive Statistics

### Central Tendency

**Mean (Average):**
- Sum of values / count
- Sensitive to outliers
- Use for: Normally distributed data without extreme outliers

**Median (Middle Value):**
- Middle value when sorted
- Robust to outliers
- Use for: Skewed data or data with outliers

**Mode (Most Frequent):**
- Most common value
- Can have multiple modes
- Use for: Categorical data or discrete distributions

**Example in SQL:**
```sql
SELECT
    AVG(price) as mean_price,
    MEDIAN(price) as median_price,
    MODE(category) as most_common_category
FROM products;
```

### Variability

**Standard Deviation (SD):**
- Measures spread around mean
- Same units as data
- ~68% of data within 1 SD, ~95% within 2 SD (normal distribution)

**Variance:**
- SD squared
- Used in many statistical tests

**Interquartile Range (IQR):**
- Q3 - Q1 (middle 50% of data)
- Robust to outliers
- Use for: Identifying outliers (values > Q3 + 1.5×IQR or < Q1 - 1.5×IQR)

**Example:**
```python
import pandas as pd

df['price_std'] = df['price'].std()
df['price_var'] = df['price'].var()

Q1 = df['price'].quantile(0.25)
Q3 = df['price'].quantile(0.75)
IQR = Q3 - Q1
outliers = df[(df['price'] < Q1 - 1.5*IQR) | (df['price'] > Q3 + 1.5*IQR)]
```

## Distribution Analysis

### Normal Distribution

**Characteristics:**
- Bell-shaped, symmetric
- Mean = Median = Mode
- Described by mean and standard deviation

**Testing for normality:**
- Visual: Histogram, Q-Q plot
- Statistical: Shapiro-Wilk test, Anderson-Darling test

**Why it matters:**
- Many statistical tests assume normality
- If violated, consider transformations or non-parametric tests

### Skewness

**Right-skewed (positive):**
- Long tail to the right
- Mean > Median
- Common in: Income, wealth, city sizes

**Left-skewed (negative):**
- Long tail to the left
- Mean < Median
- Common in: Test scores (ceiling effect), age at death

**Handling skewness:**
- Log transformation for right-skewed data
- Square root transformation for moderate skew
- Use median instead of mean

## Correlation Analysis

### Pearson Correlation (r)

**Measures:** Linear relationship between two continuous variables

**Range:** -1 to +1
- +1: Perfect positive correlation
- 0: No linear correlation
- -1: Perfect negative correlation

**Assumptions:**
- Both variables continuous
- Linear relationship
- No significant outliers
- Bivariate normality

**Example:**
```python
correlation = df['x'].corr(df['y'])
# r > 0.7: Strong correlation
# 0.4 < r < 0.7: Moderate correlation
# r < 0.4: Weak correlation
```

### Spearman Correlation (ρ)

**Measures:** Monotonic relationship (not necessarily linear)

**Use when:**
- Ordinal data
- Non-normal distributions
- Presence of outliers

**Interpretation:** Same scale as Pearson (-1 to +1)

### Important Notes

⚠️ **Correlation ≠ Causation**
- High correlation doesn't imply one causes the other
- Could be confounding variables
- Could be reverse causation
- Could be coincidence

**Example:**
```python
# Strong correlation doesn't mean causation
ice_cream_sales.corr(drownings)  # High correlation!
# Confounding variable: summer temperature
```

## Hypothesis Testing

### General Framework

1. **State hypotheses:**
   - Null hypothesis (H₀): No effect/difference
   - Alternative hypothesis (H₁): There is an effect/difference

2. **Choose significance level (α):**
   - Typically 0.05 (5%)
   - Lower α = more stringent test

3. **Calculate test statistic and p-value**

4. **Make decision:**
   - If p < α: Reject H₀ (significant result)
   - If p ≥ α: Fail to reject H₀ (not significant)

### Interpreting P-Values

**p-value:** Probability of observing data this extreme if H₀ is true

**Common misconceptions:**
- ❌ p-value is NOT the probability H₀ is true
- ❌ (1 - p) is NOT the probability H₁ is true
- ❌ Significant result doesn't mean large or important effect

**What p-values tell you:**
- Low p-value (< 0.05): Evidence against H₀
- High p-value: Insufficient evidence against H₀ (not proof of H₀)

### T-Test

**Use for:** Comparing means

**Types:**
- **One-sample t-test:** Compare sample mean to known value
- **Independent t-test:** Compare means of two groups
- **Paired t-test:** Compare means of same group at two times

**Assumptions:**
- Continuous dependent variable
- Independent observations
- Normal distribution (or large sample)
- Equal variances (for independent t-test)

**Example:**
```python
from scipy import stats

# Independent t-test
group_a = df[df['group'] == 'A']['score']
group_b = df[df['group'] == 'B']['score']

t_stat, p_value = stats.ttest_ind(group_a, group_b)

if p_value < 0.05:
    print("Significant difference between groups")
```

### Chi-Square Test

**Use for:** Relationship between categorical variables

**Example:** Is product preference related to age group?

**Assumptions:**
- Categorical variables
- Independent observations
- Expected cell counts ≥ 5

**Example:**
```python
from scipy.stats import chi2_contingency

# Create contingency table
contingency = pd.crosstab(df['age_group'], df['product_preference'])

chi2, p_value, dof, expected = chi2_contingency(contingency)

if p_value < 0.05:
    print("Significant association between age and preference")
```

## Effect Size

### Why It Matters

**P-value tells you:** Is there an effect?
**Effect size tells you:** How large is the effect?

With large samples, tiny effects can be statistically significant but not practically meaningful.

### Common Effect Size Measures

**Cohen's d (for t-tests):**
- Small: d = 0.2
- Medium: d = 0.5
- Large: d = 0.8

**R-squared (for regression):**
- Proportion of variance explained
- Range: 0 to 1

**Cramér's V (for chi-square):**
- Association strength for categorical variables
- Range: 0 to 1

**Example:**
```python
from scipy import stats

# Calculate Cohen's d
mean_diff = group_a.mean() - group_b.mean()
pooled_std = np.sqrt((group_a.std()**2 + group_b.std()**2) / 2)
cohens_d = mean_diff / pooled_std

print(f"Cohen's d: {cohens_d:.2f}")
```

## Common Pitfalls

### 1. Multiple Testing Problem

**Issue:** Running many tests increases false positive rate.

**Solution:** Adjust significance level (Bonferroni correction: α / number_of_tests)

### 2. Sample Size Too Small

**Issue:** Low statistical power (can't detect real effects).

**Solution:** Calculate required sample size before study or use caution interpreting null results.

### 3. Assuming Normality Without Testing

**Issue:** Many tests assume normal distribution.

**Solution:** Test normality visually and statistically, use non-parametric alternatives if needed.

### 4. Cherry-Picking Results

**Issue:** Only reporting significant findings (publication bias).

**Solution:** Pre-register hypotheses, report all tests conducted.

### 5. Confusing Statistical and Practical Significance

**Issue:** Statistically significant doesn't mean important.

**Solution:** Always report effect sizes alongside p-values.

## Best Practices

1. **Visualize first:** Plot data before running tests
2. **Check assumptions:** Verify test assumptions are met
3. **Report completely:** Include test statistic, p-value, effect size, confidence intervals
4. **Use appropriate tests:** Match test to data type and distribution
5. **Consider practical significance:** Is the effect large enough to matter?
6. **Be transparent:** Report all analyses, not just significant ones
7. **Understand limitations:** Sample bias, measurement error, confounding variables
8. **Replicate when possible:** Single study rarely definitive

## Choosing the Right Test

**Comparing two groups:**
- Continuous outcome, normal: Independent t-test
- Continuous outcome, non-normal: Mann-Whitney U test
- Paired observations: Paired t-test or Wilcoxon signed-rank

**Comparing 3+ groups:**
- Continuous outcome, normal: ANOVA
- Continuous outcome, non-normal: Kruskal-Wallis test
- Categorical outcome: Chi-square test

**Relationship between variables:**
- Two continuous: Pearson or Spearman correlation
- Continuous outcome, multiple predictors: Multiple regression
- Binary outcome: Logistic regression

## Warnings

⚠️ **Correlation does not imply causation**: Always consider confounding variables

⚠️ **Small sample sizes have low power**: May miss real effects

⚠️ **P-hacking invalidates results**: Don't run many tests and report only significant ones

⚠️ **Outliers can drastically affect results**: Always check for and handle outliers appropriately

⚠️ **Violated assumptions invalidate tests**: Check assumptions before running parametric tests

⚠️ **Effect size matters more than p-value**: Focus on practical significance, not just statistical

## Resources

- Statistics How To: https://www.statisticshowto.com/
- Understanding Statistical Power and Significance Testing
- Effect Size Calculator and Interpreter
- Sample Size Calculator
