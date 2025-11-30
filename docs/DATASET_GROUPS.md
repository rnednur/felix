# Dataset Groups - Multi-Dataset Query Support

This document explains how to use Dataset Groups to query multiple datasets together using JOINs and multi-table operations.

## Overview

Dataset Groups allow you to:
- Group multiple datasets together for combined analysis
- Run SQL queries that JOIN across multiple tables
- Use natural language queries that span multiple datasets
- Maintain organized collections of related datasets

## Getting Started

### 1. Apply the Database Migration

Run the migration to create the necessary tables:

```bash
# From the backend directory
psql -U your_user -d your_database -f migrations/003_add_dataset_groups.sql
```

Or use your preferred database migration tool.

### 2. Create a Dataset Group

#### Via API

```bash
curl -X POST http://localhost:8000/api/v1/dataset-groups/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sales Analysis",
    "description": "Customer and order datasets for sales analysis"
  }'
```

#### Via Frontend

1. Navigate to the Dataset Groups section
2. Click "Create New Group"
3. Enter a name and optional description
4. Click "Create"

### 3. Add Datasets to the Group

#### Via API

```bash
curl -X POST http://localhost:8000/api/v1/dataset-groups/{group_id}/datasets \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "your-dataset-id",
    "alias": "customers",
    "display_order": 0
  }'
```

The `alias` field is important - it determines the table name used in SQL queries.

#### Via Frontend

1. Select your dataset group
2. Click "Add Dataset"
3. Choose a dataset from the list
4. The dataset will be added to the group

### 4. Query the Dataset Group

#### Natural Language Query

```bash
curl -X POST http://localhost:8000/api/v1/queries/nl \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": "your-group-id",
    "query": "Show total sales by customer name"
  }'
```

The LLM will automatically:
- Understand which tables to use
- Generate appropriate JOIN conditions
- Use the correct table aliases

#### SQL Query

```bash
curl -X POST http://localhost:8000/api/v1/queries/sql \
  -H "Content-Type: application/json" \
  -d '{
    "group_id": "your-group-id",
    "sql": "SELECT c.name, SUM(o.amount) as total FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.name"
  }'
```

## Example Use Cases

### E-commerce Analysis

Create a group with:
- `customers` - Customer information
- `orders` - Order transactions
- `products` - Product catalog

Example queries:
- "Which customers bought the most expensive products?"
- "Show me monthly sales trends by product category"
- "Find customers who haven't ordered in the last 90 days"

### Multi-Region Analysis

Create a group with:
- `north_sales` - Northern region sales
- `south_sales` - Southern region sales
- `west_sales` - Western region sales

Example queries:
- "Compare total sales across all regions"
- "Which region had the highest growth rate?"
- "Show products that sell well in one region but not others"

### Time-Series Analysis

Create a group with:
- `daily_metrics` - Daily aggregated metrics
- `events` - Event log data
- `predictions` - Forecasted values

Example queries:
- "Compare actual vs predicted values for last month"
- "Show events that correlated with metric spikes"
- "Find days where predictions were most accurate"

## Architecture Details

### Backend Components

1. **Database Models** (`app/models/dataset.py`)
   - `DatasetGroup` - Stores group metadata
   - `DatasetGroupMembership` - Links datasets to groups with aliases

2. **API Endpoints** (`app/api/endpoints/dataset_groups.py`)
   - `POST /dataset-groups/` - Create group
   - `GET /dataset-groups/` - List all groups
   - `GET /dataset-groups/{id}` - Get group details
   - `POST /dataset-groups/{id}/datasets` - Add dataset to group
   - `DELETE /dataset-groups/{id}/datasets/{dataset_id}` - Remove dataset

3. **NLToSQLService** (`app/services/nl_to_sql_service.py`)
   - `_generate_sql_for_group()` - Multi-table SQL generation
   - `build_group_prompt()` - Specialized LLM prompt for multi-table queries

4. **DuckDBService** (`app/services/duckdb_service.py`)
   - `get_connection_for_group()` - Creates DuckDB connection with multiple tables
   - `execute_query()` - Supports both single dataset and group execution

### Frontend Components

1. **DatasetGroupManager** (`frontend/src/components/datasets/DatasetGroupManager.tsx`)
   - Full UI for creating and managing dataset groups
   - Add/remove datasets from groups
   - View group membership

2. **DatasetOrGroupSelector** (`frontend/src/components/datasets/DatasetOrGroupSelector.tsx`)
   - Dropdown selector for choosing between single dataset or group
   - Used in query interfaces

3. **Hooks** (`frontend/src/hooks/useDatasetGroups.ts`)
   - React Query hooks for all dataset group operations
   - Automatic cache invalidation

## Best Practices

### Naming Aliases

Use clear, descriptive aliases that make SQL queries readable:

```sql
-- Good
SELECT c.name, o.total
FROM customers c
JOIN orders o ON c.id = o.customer_id

-- Avoid
SELECT t1.name, t2.total
FROM table1 t1
JOIN table2 t2 ON t1.id = t2.id
```

### Dataset Organization

- Keep related datasets together (e.g., all sales-related data)
- Don't create overly large groups (3-5 datasets is ideal)
- Use descriptive group names and descriptions

### Query Performance

- Dataset groups load all tables into DuckDB memory
- Very large datasets may impact performance
- Consider filtering/sampling before creating complex JOINs
- Use indexes and proper JOIN keys when possible

### Security

- Groups don't have separate permissions - users with access to all datasets in a group can query it
- Removing a dataset from a group doesn't delete the dataset
- Deleting a group doesn't delete the datasets

## Troubleshooting

### "Dataset group not found"
- Verify the group_id is correct
- Check that the group hasn't been soft-deleted

### "Cannot specify both dataset_id and group_id"
- You must choose either a single dataset OR a group, not both

### "Failed to generate SQL"
- Check that the group has at least one dataset
- Verify all datasets in the group are READY status
- Review the natural language query for clarity

### JOIN errors
- Ensure you're using the correct table aliases
- Verify column names exist in the respective tables
- Check that JOIN keys have compatible types

## API Reference

See the OpenAPI documentation at `http://localhost:8000/docs` for complete API reference.

## Migration Path

If you have existing queries on single datasets, they continue to work exactly as before. Dataset groups are purely additive - you can use them when needed while keeping all existing functionality.

To migrate a query to use a group:

```diff
# Before (single dataset)
{
  "dataset_id": "abc123",
  "query": "Show sales totals"
}

# After (dataset group)
{
  "group_id": "group456",
  "query": "Show sales totals by customer"
}
```
