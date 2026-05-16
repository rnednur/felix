---
name: sql-query-optimization
display_name: SQL Query Optimization
version: 1.0.0
scope: task
tags: [sql, performance, optimization, query, database]
description: Expert guidance on writing efficient SQL queries and optimizing query performance
author: AI Analytics Platform
---

# SQL Query Optimization

## Overview

This skill provides expert guidance on writing efficient SQL queries, identifying performance bottlenecks, and applying optimization techniques.

## Core Principles

### 1. Query Structure Optimization

**Start with the most selective filters first:**
- Apply WHERE clauses that eliminate the most rows early
- Use indexed columns in WHERE clauses
- Avoid functions on indexed columns (breaks index usage)

**Example:**
```sql
-- Bad: Function on indexed column
SELECT * FROM orders
WHERE YEAR(order_date) = 2024;

-- Good: Direct comparison uses index
SELECT * FROM orders
WHERE order_date >= '2024-01-01'
  AND order_date < '2025-01-01';
```

### 2. Join Optimization

**Ordering matters for performance:**
- Start with the smallest table
- Join on indexed columns
- Use appropriate join types

**Example:**
```sql
-- Optimized join order
SELECT
    s.product_id,
    s.total_sales,
    p.product_name
FROM (
    -- Start with aggregated, smaller result set
    SELECT product_id, SUM(amount) as total_sales
    FROM sales
    WHERE sale_date >= '2024-01-01'
    GROUP BY product_id
) s
JOIN products p ON s.product_id = p.id;
```

### 3. Aggregation Best Practices

**Group by only necessary columns:**
- Minimize columns in GROUP BY
- Use HAVING for aggregate filters (not WHERE)
- Consider pre-aggregation for repeated queries

**Example:**
```sql
-- Efficient aggregation
SELECT
    DATE_TRUNC('month', order_date) as month,
    category,
    COUNT(*) as order_count,
    SUM(total) as revenue
FROM orders
WHERE order_date >= '2024-01-01'
GROUP BY 1, 2
HAVING SUM(total) > 1000;
```

## Common Optimization Patterns

### Pattern 1: Avoid SELECT *

**Why:** Retrieving unnecessary columns wastes I/O and memory.

```sql
-- Bad
SELECT * FROM large_table WHERE id = 123;

-- Good
SELECT id, name, email FROM large_table WHERE id = 123;
```

### Pattern 2: Use EXISTS Instead of IN for Large Subqueries

**Why:** EXISTS can short-circuit, IN materializes full subquery.

```sql
-- Less efficient
SELECT * FROM customers
WHERE id IN (SELECT customer_id FROM orders WHERE total > 1000);

-- More efficient
SELECT * FROM customers c
WHERE EXISTS (
    SELECT 1 FROM orders o
    WHERE o.customer_id = c.id AND o.total > 1000
);
```

### Pattern 3: Limit Result Sets Early

**Why:** Reduces memory and processing overhead.

```sql
-- Good practice
SELECT name, email
FROM users
WHERE active = true
  AND created_at >= '2024-01-01'
ORDER BY created_at DESC
LIMIT 100;
```

### Pattern 4: Use UNION ALL Instead of UNION When Possible

**Why:** UNION removes duplicates (expensive), UNION ALL doesn't.

```sql
-- If you know there are no duplicates or duplicates are OK
SELECT product_id FROM sales_2023
UNION ALL
SELECT product_id FROM sales_2024;
```

## Performance Analysis

### Identifying Slow Queries

**Key metrics to check:**
1. Execution time
2. Rows scanned vs rows returned (should be close)
3. Index usage
4. Join algorithm used

**In DuckDB:**
```sql
EXPLAIN ANALYZE
SELECT ...;
```

### Red Flags

Watch for these indicators of poor performance:
- Full table scans on large tables
- High ratio of scanned/returned rows
- Multiple nested subqueries
- Cartesian products (missing JOIN conditions)
- Functions on indexed columns

## Best Practices

1. **Index strategically**: Index columns used in WHERE, JOIN, and ORDER BY
2. **Test with realistic data**: Performance characteristics change with data volume
3. **Use query analyzers**: EXPLAIN ANALYZE is your friend
4. **Avoid premature optimization**: Optimize queries that are actually slow
5. **Consider query caching**: For frequently-run identical queries
6. **Batch operations**: Insert/update in batches, not row-by-row
7. **Use appropriate data types**: Smaller types = better performance
8. **Partition large tables**: When queries typically filter by date/category

## Common Anti-Patterns

### Anti-Pattern 1: N+1 Queries

**Problem:** Running one query per item instead of one query for all items.

```sql
-- Bad: Loop calling this query N times
SELECT * FROM products WHERE id = ?;

-- Good: Single query
SELECT * FROM products WHERE id IN (?, ?, ?, ...);
```

### Anti-Pattern 2: Correlated Subqueries

**Problem:** Subquery executes once per outer row.

```sql
-- Bad: Correlated subquery
SELECT
    p.name,
    (SELECT COUNT(*) FROM orders WHERE product_id = p.id) as order_count
FROM products p;

-- Good: JOIN with aggregation
SELECT
    p.name,
    COUNT(o.id) as order_count
FROM products p
LEFT JOIN orders o ON o.product_id = p.id
GROUP BY p.id, p.name;
```

### Anti-Pattern 3: Using OR on Different Columns

**Problem:** Prevents index usage.

```sql
-- Bad: Can't use indexes effectively
SELECT * FROM users
WHERE email = 'test@example.com' OR phone = '555-0100';

-- Better: Use UNION when appropriate
SELECT * FROM users WHERE email = 'test@example.com'
UNION
SELECT * FROM users WHERE phone = '555-0100';
```

## Warnings

⚠️ **Don't over-optimize**: Premature optimization adds complexity. Profile first.

⚠️ **Index overhead**: Too many indexes slow down writes. Balance read vs write performance.

⚠️ **Query complexity**: Overly complex queries are hard to maintain. Sometimes simpler is better.

⚠️ **Statistics matter**: Query optimizers rely on table statistics. Keep them updated.

⚠️ **Different databases, different rules**: Optimization techniques vary by database engine.

## Resources

- DuckDB Performance Guide: https://duckdb.org/docs/guides/performance/
- SQL Query Optimization Tutorial
- Understanding EXPLAIN ANALYZE output
