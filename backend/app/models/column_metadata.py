from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, JSON, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class ColumnMetadata(Base):
    """Extended metadata for dataset columns"""
    __tablename__ = "column_metadata"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    column_name = Column(String, nullable=False)

    # User-defined metadata
    display_name = Column(String, nullable=True)  # Friendly name for display
    description = Column(Text, nullable=True)  # What this column represents
    business_definition = Column(Text, nullable=True)  # Business context

    # Data semantics
    semantic_type = Column(String, nullable=True)  # e.g., "email", "phone", "currency", "date"
    data_format = Column(String, nullable=True)  # e.g., "MM/DD/YYYY", "$#,##0.00"
    unit = Column(String, nullable=True)  # e.g., "USD", "meters", "seconds"

    # Constraints and validation
    is_pii = Column(Boolean, default=False)  # Personally Identifiable Information
    is_required = Column(Boolean, default=False)  # Should not be null
    valid_values = Column(JSON, nullable=True)  # List of allowed values
    validation_rules = Column(JSON, nullable=True)  # Custom validation rules

    # Query hints
    default_aggregation = Column(String, nullable=True)  # e.g., "SUM", "AVG", "COUNT"
    is_dimension = Column(Boolean, default=False)  # Good for GROUP BY
    is_measure = Column(Boolean, default=False)  # Good for aggregation

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class QueryRule(Base):
    """Business rules applied automatically to queries"""
    __tablename__ = "query_rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)

    # Rule definition
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(String, nullable=False)  # "filter", "exclude_column", "always_include"

    # Rule configuration
    condition = Column(JSON, nullable=False)  # Rule parameters
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher priority rules apply first

    # Examples:
    # Filter rule: {"column": "status", "operator": "=", "value": "active"}
    # Exclude column: {"column": "ssn"}
    # Always include: {"column": "created_at", "operator": ">=", "value": "2023-01-01"}
    # Date range: {"column": "date", "operator": "between", "value": ["2023-01-01", "2023-12-31"]}

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
