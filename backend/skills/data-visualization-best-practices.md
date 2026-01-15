---
name: data-visualization-best-practices
display_name: Data Visualization Best Practices
version: 1.0.0
scope: task
tags: [visualization, charts, graphs, design, communication]
description: Guidelines for creating clear, effective, and honest data visualizations
author: AI Analytics Platform
---

# Data Visualization Best Practices

## Overview

This skill provides expert guidance on creating effective data visualizations that communicate insights clearly and accurately.

## Chart Selection

### Choosing the Right Chart Type

**Comparison:**
- Bar chart: Comparing categories
- Grouped bar: Comparing subcategories
- Column chart: Time-series comparison (few points)

**Distribution:**
- Histogram: Single variable distribution
- Box plot: Distribution summary with outliers
- Violin plot: Distribution shape

**Relationship:**
- Scatter plot: Two variable correlation
- Bubble chart: Three variables (x, y, size)
- Heatmap: Matrix of values

**Composition:**
- Pie chart: Parts of a whole (max 5-6 slices)
- Stacked bar: Composition over categories
- Treemap: Hierarchical composition

**Trend:**
- Line chart: Continuous data over time
- Area chart: Cumulative values over time
- Sparkline: Inline trend indication

## Design Principles

### 1. Clarity Over Decoration

**Remove chart junk:**
- Unnecessary grid lines
- 3D effects (distort perception)
- Decorative elements
- Redundant labels

**Example Vega-Lite spec:**
```json
{
  "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
  "mark": "bar",
  "encoding": {
    "x": {"field": "category", "type": "nominal", "axis": {"title": "Product Category"}},
    "y": {"field": "sales", "type": "quantitative", "axis": {"title": "Total Sales ($)"}}
  },
  "config": {
    "view": {"stroke": null},
    "axis": {"grid": false, "domainWidth": 1}
  }
}
```

### 2. Color with Purpose

**Use color to:**
- Highlight key data points
- Group related data
- Show sequential or diverging scales

**Avoid:**
- Rainbow color schemes (not perceptually uniform)
- Too many colors (cognitive overload)
- Color as only differentiator (accessibility)

**Good color schemes:**
- Sequential: Single hue progression (blues: #deebf7 → #08519c)
- Diverging: Two hues from center (red-white-blue)
- Categorical: Distinct hues (max 7-8 categories)

**Example with semantic colors:**
```json
{
  "mark": "bar",
  "encoding": {
    "x": {"field": "month", "type": "ordinal"},
    "y": {"field": "revenue", "type": "quantitative"},
    "color": {
      "field": "status",
      "type": "nominal",
      "scale": {
        "domain": ["profit", "loss"],
        "range": ["#2ecc71", "#e74c3c"]
      }
    }
  }
}
```

### 3. Appropriate Scales

**Zero baseline for bar charts:**
- Bar lengths must be proportional to values
- Truncated y-axis misleads

**Logarithmic scales:**
- Use for exponential data (multiple orders of magnitude)
- Always label clearly as log scale

**Time series:**
- Keep time on x-axis (convention)
- Use consistent intervals

## Composition Guidelines

### Axis Design

**Labels:**
- Clear, concise axis titles
- Appropriate precision (no unnecessary decimals)
- Readable font size (min 10-12pt)
- Horizontal labels when possible

**Ticks:**
- Enough to guide without clutter (typically 5-10)
- Round numbers (0, 10, 20, not 0, 13, 26)
- Consider k/M/B suffixes for large numbers

**Example:**
```json
{
  "encoding": {
    "x": {
      "field": "year",
      "type": "ordinal",
      "axis": {
        "labelAngle": 0,
        "title": "Year"
      }
    },
    "y": {
      "field": "population",
      "type": "quantitative",
      "axis": {
        "title": "Population (millions)",
        "format": ".1f",
        "tickCount": 6
      }
    }
  }
}
```

### Legend Design

**Placement:**
- Top or right side (not bottom)
- Inside plot area only if space available
- Close to relevant data

**Content:**
- Descriptive labels (not field names)
- Order matches data importance
- Remove if single series

### Title and Annotations

**Effective titles:**
- Descriptive, not just field names
- Communicate the insight ("Sales Increased 40% in Q4")
- Subtitle for additional context

**Annotations:**
- Highlight key points or thresholds
- Use sparingly (only for important info)
- Clear, non-overlapping labels

## Common Patterns

### Pattern 1: Time Series with Reference Line

Show trend with important threshold:

```json
{
  "layer": [
    {
      "mark": "line",
      "encoding": {
        "x": {"field": "date", "type": "temporal"},
        "y": {"field": "value", "type": "quantitative"}
      }
    },
    {
      "mark": "rule",
      "encoding": {
        "y": {"datum": 100},
        "color": {"value": "red"},
        "strokeDash": {"value": [4, 4]}
      }
    }
  ]
}
```

### Pattern 2: Grouped Bar Chart

Compare categories across groups:

```json
{
  "mark": "bar",
  "encoding": {
    "x": {"field": "category", "type": "nominal"},
    "y": {"field": "value", "type": "quantitative"},
    "xOffset": {"field": "group"},
    "color": {"field": "group", "type": "nominal"}
  }
}
```

### Pattern 3: Distribution with Box Plot

Show distribution summary:

```json
{
  "mark": {"type": "boxplot", "extent": 1.5},
  "encoding": {
    "x": {"field": "category", "type": "nominal"},
    "y": {"field": "value", "type": "quantitative"}
  }
}
```

### Pattern 4: Scatter with Regression

Show correlation with trend:

```json
{
  "layer": [
    {
      "mark": "point",
      "encoding": {
        "x": {"field": "x", "type": "quantitative"},
        "y": {"field": "y", "type": "quantitative"}
      }
    },
    {
      "mark": {"type": "line", "color": "red"},
      "transform": [{"regression": "y", "on": "x"}],
      "encoding": {
        "x": {"field": "x", "type": "quantitative"},
        "y": {"field": "y", "type": "quantitative"}
      }
    }
  ]
}
```

## Accessibility

### Color Blindness

**Guidelines:**
- Don't rely on color alone
- Use patterns, shapes, or labels
- Test with colorblind simulators
- Use colorblind-safe palettes

**Safe color pairs:**
- Blue + Orange
- Blue + Yellow
- Red + Blue (not red + green)

### Text Alternatives

**Provide:**
- Alt text describing key insights
- Data tables as fallback
- Clear axis labels (not just color legend)

## Best Practices Summary

1. **Choose appropriate chart type** for your data and message
2. **Start y-axis at zero** for bar charts
3. **Remove unnecessary elements** (maximize data-ink ratio)
4. **Use color purposefully** and sparingly
5. **Label clearly** with appropriate precision
6. **Maintain consistent scales** across related charts
7. **Highlight key insights** with annotations
8. **Test readability** at actual display size
9. **Consider accessibility** (color blindness, screen readers)
10. **Iterate based on feedback** from actual users

## Common Anti-Patterns

### Anti-Pattern 1: Pie Charts with Too Many Slices

**Problem:** Hard to compare angles, especially small slices.

**Solution:** Use bar chart for more than 5-6 categories.

### Anti-Pattern 2: Dual Y-Axes

**Problem:** Can be used to mislead by manipulating scale.

**Solution:** Use two separate charts or normalize to same scale.

### Anti-Pattern 3: 3D Charts

**Problem:** Perspective distorts values, making comparison difficult.

**Solution:** Always use 2D charts.

### Anti-Pattern 4: Truncated Bar Chart Y-Axis

**Problem:** Bar lengths not proportional to values (misleading).

**Solution:** Start y-axis at zero, or use line chart if showing change.

## Warnings

⚠️ **Truncated axes can mislead**: Use responsibly with clear labeling.

⚠️ **3D effects distort perception**: Stick to 2D representations.

⚠️ **Too many colors reduce clarity**: Limit palette to 5-7 distinct colors.

⚠️ **Pie charts have limited utility**: Consider alternatives for most use cases.

⚠️ **Aspect ratio matters**: Maintain appropriate width:height ratios.

⚠️ **Animation can distract**: Use sparingly and with purpose.

## Resources

- Vega-Lite Documentation: https://vega.github.io/vega-lite/
- ColorBrewer (color schemes): https://colorbrewer2.org/
- Data Visualization Catalogue
- Edward Tufte's "The Visual Display of Quantitative Information"
