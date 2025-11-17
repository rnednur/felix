from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, Text, BigInteger, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base


class QueryStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Query(Base):
    __tablename__ = "queries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=True)

    # Query content
    nl_input = Column(Text, nullable=True)  # Natural language query
    generated_sql = Column(Text, nullable=False)  # Actual SQL

    # Execution info
    execution_time_ms = Column(Integer, nullable=True)
    result_rows = Column(Integer, default=0)
    result_bytes = Column(BigInteger, default=0)
    result_path = Column(String, nullable=True)  # Path to cached Parquet result

    # Status
    status = Column(SQLEnum(QueryStatus), default=QueryStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)

    # Query metadata (retrieved columns, confidence, etc.)
    query_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    dataset = relationship("Dataset", back_populates="queries")
    visualizations = relationship("Visualization", back_populates="query")
