from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base


class DatasetRole(str, enum.Enum):
    """Roles for dataset members (team collaboration)"""
    OWNER = "OWNER"         # Full control, can delete dataset, manage members
    ADMIN = "ADMIN"         # Can edit, query, and manage members (except owner)
    EDITOR = "EDITOR"       # Can edit metadata, run queries, view results
    ANALYST = "ANALYST"     # Can run queries and view results
    VIEWER = "VIEWER"       # Read-only access


class DatasetMember(Base):
    """
    Team members who are part of the dataset workspace.
    This is different from sharing - members are collaborators with defined roles.
    """
    __tablename__ = "dataset_members"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Role in the dataset
    role = Column(SQLEnum(DatasetRole), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    removed_at = Column(DateTime, nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="members")
    user = relationship("User", back_populates="dataset_memberships")

    # Ensure one user has only one role per dataset
    __table_args__ = (
        UniqueConstraint('dataset_id', 'user_id', name='uix_dataset_user'),
    )

    def __repr__(self):
        return f"<DatasetMember(dataset_id={self.dataset_id}, user_id={self.user_id}, role={self.role})>"


class DatasetGroupMember(Base):
    """
    Team members who are part of the dataset group workspace.
    """
    __tablename__ = "dataset_group_members"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String, ForeignKey("dataset_groups.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Role in the group
    role = Column(SQLEnum(DatasetRole), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    removed_at = Column(DateTime, nullable=True)

    # Relationships
    group = relationship("DatasetGroup", back_populates="members")
    user = relationship("User", back_populates="group_memberships")

    # Ensure one user has only one role per group
    __table_args__ = (
        UniqueConstraint('group_id', 'user_id', name='uix_group_user'),
    )

    def __repr__(self):
        return f"<DatasetGroupMember(group_id={self.group_id}, user_id={self.user_id}, role={self.role})>"
