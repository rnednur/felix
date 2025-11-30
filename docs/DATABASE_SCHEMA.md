# Database Schema Configuration

This application supports configurable database schemas via environment variables.

## Variable Naming Clarification

**Two different variables for different purposes:**

1. **`DB_SCHEMA`** (in `.env`) - Used by Python/SQLAlchemy
   - Controls where Python code creates/queries tables
   - Set once in `.env` file
   - Example: `DB_SCHEMA=aispreadsheets`

2. **`schema_name`** (in SQL scripts) - Used by psql command
   - Only used when running SQL migrations manually
   - Passed as command-line argument to migration scripts
   - Example: `./run_migrations.sh aispreadsheets`

**Most users only need to set `DB_SCHEMA` in `.env`**

## Configuration

Add to your `.env` file:

```bash
# Use default 'public' schema (leave commented or blank)
# DB_SCHEMA=

# Or specify a custom schema
DB_SCHEMA=aispreadsheets
```

## Usage

### Option 1: Using Python Setup Script (Recommended)

#### 1. Set Schema in `.env`

```bash
DB_SCHEMA=myapp
```

#### 2. Run Setup Script

The setup script will automatically:
- Create the schema if it doesn't exist
- Create all tables in that schema

```bash
python setup_database.py
```

### Option 2: Using SQL Migrations

#### 1. Run Migration Script

```bash
# Run all migrations in default schema (public)
./run_migrations.sh

# Run all migrations in custom schema
./run_migrations.sh myapp

# Run specific migration in custom schema
./run_migrations.sh myapp 001
```

#### 2. Manual psql Execution

```bash
# With custom schema
psql $DATABASE_URL -v schema_name=myapp -f migrations/001_initial_schema.sql

# With default schema (public)
psql $DATABASE_URL -f migrations/001_initial_schema.sql
```

### 3. All Tables Use the Schema

Example output:
```
Creating schema 'myapp'...
Schema 'myapp' created successfully!

Creating tables...
Created tables:
  - myapp.datasets
  - myapp.dataset_versions
  - myapp.dataset_groups
  - myapp.dataset_group_memberships
  - myapp.queries
  - myapp.visualizations
  ...
```

## Benefits

- **Multi-tenant**: Run multiple instances in the same database
- **Organization**: Separate application data from other schemas
- **Security**: Better isolation with schema-level permissions
- **Deployment**: Different schemas for dev/staging/prod in same DB

## Migration Notes

If you already have tables in the `public` schema and want to move to a custom schema:

```sql
-- Create new schema
CREATE SCHEMA myapp;

-- Move tables (example)
ALTER TABLE datasets SET SCHEMA myapp;
ALTER TABLE queries SET SCHEMA myapp;
-- ... repeat for all tables
```

Or simply export/import:
```bash
# Export from public schema
pg_dump -n public -d ai_analytics > backup.sql

# Update schema in backup
sed -i 's/public\./myapp\./g' backup.sql

# Import to new schema
psql -d ai_analytics -f backup.sql
```
