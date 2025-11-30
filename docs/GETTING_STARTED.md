# Getting Started - Dataset Groups & New UI

This guide will walk you through setting up and using the new dataset grouping feature and revamped UI.

## Quick Start (5 minutes)

### 1. Apply Database Migration

```bash
# From the project root
cd backend
psql -U your_username -d your_database -f ../migrations/003_add_dataset_groups.sql
```

Or if you have the database service running:
```bash
PGPASSWORD=your_password psql -h localhost -U your_user -d aispreadsheets -f migrations/003_add_dataset_groups.sql
```

### 2. Start the Backend

```bash
# From backend directory
python run_server.py
```

The API should start on `http://localhost:8000`

### 3. Start the Frontend

```bash
# From frontend/app directory
npm run dev
```

The UI should start on `http://localhost:3000`

### 4. Test the New UI

1. Visit `http://localhost:3000`
2. You should see the new **Dataset Hub** with cards
3. Upload a dataset using the "Upload New Dataset" button
4. Watch it appear as a card with health indicator

## Creating Your First Dataset Group

### Step 1: Upload Multiple Datasets

Upload 2-3 related datasets. For example:
- `customers.csv` - Customer information
- `orders.csv` - Order transactions
- `products.csv` - Product catalog

### Step 2: Create a Group

1. Click **"Create Group"** button in the Dataset Hub
2. Enter a name: "E-commerce Analysis"
3. Add description: "Customer, orders, and products for sales analysis"
4. Click **"Create"**

### Step 3: Add Datasets to Group

1. In the group manager, click **"Add Dataset"**
2. Select `customers.csv` and click "Add"
3. Optionally set alias to "customers" (or leave blank to use filename)
4. Repeat for `orders.csv` (alias: "orders") and `products.csv` (alias: "products")

### Step 4: Query the Group

1. Click **"Analyze Now"** on your group card
2. In the query interface, select your dataset group
3. Ask a question: "Show me total sales by customer"
4. The system will automatically generate SQL with JOINs!

## Example Queries

### Natural Language (Recommended)

```
"Which customers bought the most expensive products?"
```

The LLM will generate:
```sql
SELECT c.name, p.name as product_name, p.price
FROM customers c
JOIN orders o ON c.id = o.customer_id
JOIN products p ON o.product_id = p.id
ORDER BY p.price DESC
LIMIT 1000
```

### Direct SQL

You can also write SQL directly:

```sql
SELECT
  c.name,
  COUNT(o.id) as order_count,
  SUM(o.total) as total_spent
FROM customers c
JOIN orders o ON c.id = o.customer_id
GROUP BY c.name
ORDER BY total_spent DESC
LIMIT 10
```

## Understanding the New UI

### Dataset Cards

Each card shows:
- **Health Score** - How complete/healthy the dataset is
  - 90-100% = Green (has description, data looks good)
  - 60-89% = Yellow (basic checks pass)
  - 0-59% = Red (missing data or errors)
- **Status Icon** - Ready ✓, Processing ⏱, Failed ✗
- **Stats** - Row count and file size
- **Actions** - Analyze or Delete

### Group Cards

Purple-themed cards that show:
- **Dataset Count** - How many datasets are in the group
- **Description** - What the group is for
- **Actions** - Analyze the entire group or delete it

### Filter Tabs

- **All Datasets** - Show everything (default)
- **Groups** - Only show dataset groups
- **Single Datasets** - Only show individual datasets

## Common Use Cases

### Use Case 1: Sales Analysis
**Datasets**: customers, orders, products
**Questions**:
- "What's our average order value by customer segment?"
- "Which products are frequently bought together?"
- "Show me monthly revenue trends"

### Use Case 2: Multi-Region Analysis
**Datasets**: north_region, south_region, west_region, east_region
**Questions**:
- "Compare sales across all regions"
- "Which region has the highest growth rate?"
- "Show products that sell well in one region but not others"

### Use Case 3: Time-Series Forecasting
**Datasets**: historical_data, current_data, predictions
**Questions**:
- "Compare actual vs predicted values"
- "Show prediction accuracy over time"
- "Find the largest forecast errors"

## Troubleshooting

### Migration fails
**Error**: `relation "datasets" does not exist`
**Fix**: Run the earlier migrations first (001, 002)

### Health score is low
**Cause**: Dataset might be missing description
**Fix**: Add a description via the API or database

### Can't find group option
**Cause**: Using old cached version
**Fix**: Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)

### Query fails with "table not found"
**Cause**: Alias might not match table name
**Fix**: Check the alias in group settings, use exact name in SQL

### Delete doesn't work
**Cause**: Permissions or soft delete issue
**Fix**: Check backend logs, verify API endpoint is accessible

## API Quick Reference

### Create Group
```bash
curl -X POST http://localhost:8000/api/v1/dataset-groups/ \
  -H "Content-Type: application/json" \
  -d '{"name": "My Group", "description": "Group description"}'
```

### Add Dataset to Group
```bash
curl -X POST http://localhost:8000/api/v1/dataset-groups/{group_id}/datasets \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": "abc123", "alias": "customers"}'
```

### Query a Group
```bash
curl -X POST http://localhost:8000/api/v1/queries/nl \
  -H "Content-Type: application/json" \
  -d '{"group_id": "group123", "query": "Show total sales"}'
```

### List All Groups
```bash
curl http://localhost:8000/api/v1/dataset-groups/
```

## Next Steps

1. **Explore the UI** - Try different filters, upload datasets, create groups
2. **Test Queries** - Ask natural language questions across multiple datasets
3. **Read the Docs** - Check `DATASET_GROUPS.md` for detailed architecture
4. **Customize** - Modify card colors, add features, extend functionality

## Need Help?

- Check `DATASET_GROUPS.md` for detailed documentation
- Check `UI_REVAMP_SUMMARY.md` for UI details
- Check `CLAUDE.md` for project overview
- Open an issue if you find bugs

## What's Next?

Optional enhancements you could add:
- [ ] Search/filter in Dataset Hub
- [ ] Drag-and-drop to reorder datasets in groups
- [ ] Export group configuration as JSON
- [ ] Share groups with other users
- [ ] Advanced health checks (data quality rules)
- [ ] Group templates (e.g., "E-commerce starter pack")
