#!/usr/bin/env python
"""
Migration script to add spatial fields to datasets table
"""
import sys
from sqlalchemy import text
from app.core.database import engine

def run_migration():
    """Add spatial fields to datasets table"""
    print("=" * 60)
    print("Running Migration: Add Spatial Fields to Datasets")
    print("=" * 60)

    migration_sql = """
    -- Add spatial data flag
    ALTER TABLE aispreadsheets.datasets
    ADD COLUMN IF NOT EXISTS has_spatial_data BOOLEAN NOT NULL DEFAULT FALSE;

    -- Add spatial configuration (stores detected columns and Kepler.gl config)
    ALTER TABLE aispreadsheets.datasets
    ADD COLUMN IF NOT EXISTS spatial_config JSONB NULL;

    -- Create index for faster spatial dataset queries
    CREATE INDEX IF NOT EXISTS idx_datasets_has_spatial_data
    ON aispreadsheets.datasets(has_spatial_data)
    WHERE has_spatial_data = TRUE;

    -- Add comments
    COMMENT ON COLUMN aispreadsheets.datasets.has_spatial_data IS 'Indicates if dataset contains spatial data (lat/lng, addresses, etc.)';
    COMMENT ON COLUMN aispreadsheets.datasets.spatial_config IS 'Stores spatial column metadata and Kepler.gl configuration as JSON';
    """

    try:
        with engine.connect() as conn:
            # Execute migration
            print("\nExecuting migration SQL...")
            conn.execute(text(migration_sql))
            conn.commit()

            print("\n✅ Migration completed successfully!")
            print("\nAdded columns:")
            print("  - has_spatial_data (BOOLEAN)")
            print("  - spatial_config (JSONB)")
            print("\nCreated index:")
            print("  - idx_datasets_has_spatial_data")

            # Verify columns exist
            print("\nVerifying columns...")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'aispreadsheets'
                  AND table_name = 'datasets'
                  AND column_name IN ('has_spatial_data', 'spatial_config')
                ORDER BY column_name
            """))

            columns = result.fetchall()
            if columns:
                print("\nColumn verification:")
                for col in columns:
                    print(f"  ✓ {col[0]} ({col[1]}) - nullable: {col[2]}")
            else:
                print("\n⚠️  Warning: Could not verify columns")

        print("\n" + "=" * 60)
        print("Migration completed! You can now restart your server.")
        print("=" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ Migration failed!")
        print("=" * 60)
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running")
        print("  2. Database connection is correct in .env")
        print("  3. User has ALTER TABLE permissions")
        sys.exit(1)


if __name__ == "__main__":
    run_migration()
