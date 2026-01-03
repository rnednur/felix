#!/usr/bin/env python
"""
Run migration 005 to add group_id to queries table
"""
import psycopg2
from app.core.config import settings

def run_migration():
    # Parse DATABASE_URL
    url_parts = settings.DATABASE_URL.replace('postgresql://', '').split('@')
    user_pass = url_parts[0].split(':')
    host_port_db = url_parts[1].split('/')
    host_port = host_port_db[0].split(':')

    user = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ''
    host = host_port[0]
    port = host_port[1] if len(host_port) > 1 else '5432'
    dbname = host_port_db[1].split('?')[0]

    print(f"Connecting to {dbname} at {host}:{port}...")

    conn = psycopg2.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=dbname
    )

    cursor = conn.cursor()

    # Read and execute migration
    print("Running migration 005: Add group_id to queries table...")

    migration_sql = """
    -- Add group_id column to queries table
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'queries' AND column_name = 'group_id'
        ) THEN
            ALTER TABLE queries ADD COLUMN group_id VARCHAR REFERENCES dataset_groups(id);
            CREATE INDEX idx_queries_group_id ON queries(group_id);
        END IF;
    END $$;
    """

    cursor.execute(migration_sql)
    conn.commit()

    print("✓ Migration 005 completed successfully!")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    run_migration()
