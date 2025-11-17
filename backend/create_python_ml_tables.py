#!/usr/bin/env python3
"""
Create code_executions and ml_models tables
Run this instead of SQL migration if you prefer
"""

from app.core.database import engine, Base
from app.models.code_execution import CodeExecution, MLModel

print("🚀 Creating Python/ML tables...")

try:
    # Create only the new tables
    Base.metadata.create_all(
        bind=engine,
        tables=[CodeExecution.__table__, MLModel.__table__],
        checkfirst=True
    )
    print("✅ Tables created successfully!")
    print("   - code_executions")
    print("   - ml_models")

except Exception as e:
    print(f"❌ Error creating tables: {e}")
    print("\nIf you see enum-related errors, you need to run the SQL migration instead:")
    print("  psql -U postgres -d your_db -f migrations/002_add_code_execution_ml_models.sql")
