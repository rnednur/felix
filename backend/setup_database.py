#!/usr/bin/env python
"""
Database setup script - creates database and tables
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app.core.config import settings
from app.core.database import engine, Base
from app.models import (
    Dataset,
    DatasetVersion,
    Query,
    Visualization,
    SemanticMetric,
    AuditLog,
)
from app.models.column_metadata import ColumnMetadata, QueryRule


def create_database():
    """Create the database if it doesn't exist"""
    # Parse DATABASE_URL to get connection params
    # Format: postgresql://user:password@host:port/dbname
    url_parts = settings.DATABASE_URL.replace('postgresql://', '').split('@')
    user_pass = url_parts[0].split(':')
    host_port_db = url_parts[1].split('/')
    host_port = host_port_db[0].split(':')

    user = user_pass[0]
    password = user_pass[1] if len(user_pass) > 1 else ''
    host = host_port[0]
    port = host_port[1] if len(host_port) > 1 else '5432'
    dbname = host_port_db[1].split('?')[0]  # Remove any query params

    print(f"Connecting to PostgreSQL at {host}:{port}...")

    # Connect to PostgreSQL server (default postgres database)
    conn = psycopg2.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database='postgres'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    cursor = conn.cursor()

    # Check if database exists
    cursor.execute(
        "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
        (dbname,)
    )
    exists = cursor.fetchone()

    if not exists:
        print(f"Creating database '{dbname}'...")
        cursor.execute(f'CREATE DATABASE {dbname}')
        print(f"Database '{dbname}' created successfully!")
    else:
        print(f"Database '{dbname}' already exists.")

    cursor.close()
    conn.close()


def create_tables():
    """Create all tables"""
    print("\nCreating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

    # Print created tables
    print("\nCreated tables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


def main():
    print("=" * 60)
    print("AI Analytics Platform - Database Setup")
    print("=" * 60)

    try:
        create_database()
        create_tables()

        print("\n" + "=" * 60)
        print("✅ Database setup completed successfully!")
        print("=" * 60)
        print("\nYou can now start the server with:")
        print("  uvicorn app.main:app --reload")

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ Database setup failed!")
        print("=" * 60)
        print(f"\nError: {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running (docker-compose up -d)")
        print("  2. .env file has correct DATABASE_URL")
        print("  3. PostgreSQL user has CREATE DATABASE permission")
        raise


if __name__ == "__main__":
    main()
