from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Ownership
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Associated dataset or dataset group (optional)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=True)
    dataset_group_id = Column(String, ForeignKey("dataset_groups.id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="workspaces")
    dataset = relationship("Dataset")
    dataset_group = relationship("DatasetGroup")
    items = relationship("CanvasItem", back_populates="workspace", cascade="all, delete-orphan")


class CanvasItem(Base):
    __tablename__ = "canvas_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)

    # Item type (query-result, chart, insight-note, code-block, ml-model)
    type = Column(String(50), nullable=False)

    # Position and size
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    z_index = Column(Integer, default=0, nullable=False)

    # Content (flexible JSONB for different item types)
    content = Column(JSONB, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="items")
