# Database Setup Instructions

## Option 1: Python Setup Script (Recommended)

```bash
# Make sure PostgreSQL is running
docker-compose up -d

# Run setup script
python setup_database.py
```

This will:
1. Create the `ai_analytics` database if it doesn't exist
2. Create all tables with proper schema
3. Set up indexes

## Option 2: Manual SQL Migration

```bash
# Make sure PostgreSQL is running
docker-compose up -d

# Create database manually
psql -U postgres -h localhost -c "CREATE DATABASE ai_analytics;"

# Run migration
psql -U postgres -h localhost -d ai_analytics -f migrations/001_initial_schema.sql
```

## Option 3: Using psql directly

```bash
# Connect to PostgreSQL
psql -U postgres -h localhost

# In psql prompt:
CREATE DATABASE ai_analytics;
\c ai_analytics
\i migrations/001_initial_schema.sql
\q
```

## Verify Setup

```bash
# Check tables were created
psql -U postgres -h localhost -d ai_analytics -c "\dt"

# You should see:
# - datasets
# - dataset_versions
# - queries
# - visualizations
# - semantic_metrics
# - audit_logs
```

## Troubleshooting

### Database connection failed
- Make sure Docker is running: `docker ps`
- Check PostgreSQL container: `docker-compose ps`
- Check logs: `docker-compose logs postgres`

### Permission denied
If you get permission errors, make sure the PostgreSQL user has permissions:
```sql
GRANT ALL PRIVILEGES ON DATABASE ai_analytics TO postgres;
```

### Reset database
To start fresh:
```bash
psql -U postgres -h localhost -c "DROP DATABASE IF EXISTS ai_analytics;"
python setup_database.py
```
