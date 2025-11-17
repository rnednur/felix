from sqlalchemy import Column, String, DateTime, JSON, LargeBinary, Text
from datetime import datetime
import uuid
from app.core.database import Base


class SemanticMetric(Base):
    __tablename__ = "semantic_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    formula = Column(Text, nullable=False)  # SQL expression

    grain = Column(JSON, nullable=True)  # ["date", "region"]
    allowed_aggs = Column(JSON, nullable=True)  # ["SUM", "AVG"]
    default_filters = Column(JSON, nullable=True)

    # Binary embedding
    embedding_bytes = Column(LargeBinary, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
