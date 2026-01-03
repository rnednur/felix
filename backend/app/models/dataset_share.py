from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base


class SharePermission(str, enum.Enum):
    VIEW = "VIEW"           # Can view dataset and query results
    QUERY = "QUERY"         # Can view and run queries
    EDIT = "EDIT"           # Can view, query, and modify dataset metadata
    ADMIN = "ADMIN"         # Full control including sharing


class ShareType(str, enum.Enum):
    PRIVATE = "PRIVATE"     # Only owner can access
    USER = "USER"           # Shared with specific users
    PUBLIC = "PUBLIC"       # Anyone can view (read-only)


class DatasetShare(Base):
    __tablename__ = "dataset_shares"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Permission level
    permission = Column(SQLEnum(SharePermission), default=SharePermission.VIEW, nullable=False)

    # Expiration
    expires_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="shares")
    user = relationship("User", back_populates="shared_datasets")

    def __repr__(self):
        return f"<DatasetShare(dataset_id={self.dataset_id}, user_id={self.user_id}, permission={self.permission})>"


class DatasetGroupShare(Base):
    __tablename__ = "dataset_group_shares"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String, ForeignKey("dataset_groups.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Permission level
    permission = Column(SQLEnum(SharePermission), default=SharePermission.VIEW, nullable=False)

    # Expiration
    expires_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    # Relationships
    group = relationship("DatasetGroup", back_populates="shares")
    user = relationship("User")

    def __repr__(self):
        return f"<DatasetGroupShare(group_id={self.group_id}, user_id={self.user_id}, permission={self.permission})>"


class PublicDataset(Base):
    """Track publicly accessible datasets"""
    __tablename__ = "public_datasets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False, unique=True)

    # Public link settings
    allow_download = Column(Boolean, default=False)
    allow_query = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    # Relationships
    dataset = relationship("Dataset")

    def __repr__(self):
        return f"<PublicDataset(dataset_id={self.dataset_id}, allow_query={self.allow_query})>"
