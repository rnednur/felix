# Database Migrations

SQL migration scripts for the AI Analytics Platform.

## Quick Start

### Using the Helper Script (Recommended)

```bash
# Run all migrations in default schema (public)
./run_migrations.sh

# Run all migrations in custom schema
./run_migrations.sh myapp

# Run specific migration
./run_migrations.sh myapp 001
```

### Manual Execution

```bash
# With custom schema
psql $DATABASE_URL -v schema_name=myapp -f migrations/001_initial_schema.sql

# With default schema
psql $DATABASE_URL -f migrations/001_initial_schema.sql
```

## Migration Files

| File | Description |
|------|-------------|
| `001_initial_schema.sql` | Initial schema: datasets, queries, visualizations, semantic_metrics, audit_logs |
| `002_add_code_execution_ml_models.sql` | Add code execution and ML models tables |
| `003_add_dataset_groups.sql` | Add dataset groups and memberships for multi-dataset queries |

## Schema Support

All migrations support custom schemas via the `:schema_name` variable:

```sql
-- In each migration file:
SET search_path TO :schema_name, public;
```

When you run with `-v schema_name=myapp`, all tables are created in the `myapp` schema.

## Creating New Migrations

1. Create a new file: `00X_description.sql`
2. Add schema support at the top:

```sql
-- Migration: Description
-- Created: YYYY-MM-DD
--
-- Usage with custom schema:
--   psql -v schema_name=myapp -f 00X_description.sql
-- Usage with default schema (public):
--   psql -f 00X_description.sql

-- Set schema (defaults to public if not provided)
SET search_path TO :schema_name, public;

-- Your migration SQL here
CREATE TABLE ...
```

3. Make the script executable and test it:

```bash
./run_migrations.sh myapp 00X
```

## Notes

- Migrations use `CREATE TABLE IF NOT EXISTS` for idempotency
- The `run_migrations.sh` script automatically creates the schema if needed
- Always test migrations on a dev database first
- Enum types are created in the schema automatically with `SET search_path`
