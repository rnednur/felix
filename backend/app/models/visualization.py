from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class Visualization(Base):
    __tablename__ = "visualizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id = Column(String, ForeignKey("queries.id"), nullable=False)

    name = Column(String, nullable=False)
    chart_type = Column(String, nullable=False)  # bar, line, scatter, heatmap, etc.
    vega_spec = Column(JSON, nullable=False)
    thumbnail_path = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    query = relationship("Query", back_populates="visualizations")
