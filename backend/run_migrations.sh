#!/bin/bash
# Helper script to run SQL migrations with schema support
#
# Usage:
#   ./run_migrations.sh                    # Run all migrations in default schema (public)
#   ./run_migrations.sh myapp              # Run all migrations in 'myapp' schema
#   ./run_migrations.sh myapp 001          # Run specific migration (001) in 'myapp' schema
#
# Note: This uses the psql variable 'schema_name' internally
#       which is different from the Python .env variable 'DB_SCHEMA'

set -e

# Load DATABASE_URL from .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | grep DATABASE_URL | xargs)
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL not set"
    echo "Set it in .env file or export DATABASE_URL=..."
    exit 1
fi

# Parse arguments
SCHEMA_NAME=${1:-aispreadsheets}
MIGRATION_NUM=${2:-}

echo "=========================================="
echo "Running Migrations"
echo "=========================================="
echo "Schema: $SCHEMA_NAME"
echo "Database: $DATABASE_URL"
echo ""

# Create schema if it doesn't exist
if [ "$SCHEMA_NAME" != "public" ]; then
    echo "Creating schema '$SCHEMA_NAME' if not exists..."
    psql "$DATABASE_URL" -c "CREATE SCHEMA IF NOT EXISTS $SCHEMA_NAME;"
    echo ""
fi

# Run migrations
if [ -z "$MIGRATION_NUM" ]; then
    # Run all migrations
    echo "Running all migrations..."
    for file in migrations/*.sql; do
        if [ -f "$file" ]; then
            echo "Running $(basename $file)..."
            psql "$DATABASE_URL" -v schema_name="$SCHEMA_NAME" -f "$file"
            echo "✓ $(basename $file) completed"
            echo ""
        fi
    done
else
    # Run specific migration
    MIGRATION_FILE="migrations/${MIGRATION_NUM}_*.sql"
    if ls $MIGRATION_FILE 1> /dev/null 2>&1; then
        for file in $MIGRATION_FILE; do
            echo "Running $(basename $file)..."
            psql "$DATABASE_URL" -v schema_name="$SCHEMA_NAME" -f "$file"
            echo "✓ $(basename $file) completed"
        done
    else
        echo "Error: Migration file not found: $MIGRATION_FILE"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "✅ Migrations completed successfully!"
echo "=========================================="
