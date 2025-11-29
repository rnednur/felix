from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base


class SourceType(str, enum.Enum):
    CSV = "CSV"
    XLSX = "XLSX"
    GOOGLE_SHEETS = "GOOGLE_SHEETS"


class DatasetStatus(str, enum.Enum):
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # File paths
    parquet_path = Column(String, nullable=False)
    schema_path = Column(String, nullable=False)
    embedding_path = Column(String, nullable=True)

    # Source info
    source_type = Column(SQLEnum(SourceType), nullable=False)
    source_url = Column(String, nullable=True)

    # Status
    status = Column(SQLEnum(DatasetStatus), default=DatasetStatus.UPLOADING, nullable=False)

    # Stats
    row_count = Column(Integer, default=0)
    size_bytes = Column(BigInteger, default=0)
    dataset_version = Column(Integer, default=1)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    versions = relationship("DatasetVersion", back_populates="dataset")
    queries = relationship("Query", back_populates="dataset")
    code_executions = relationship("CodeExecution", back_populates="dataset")
    ml_models = relationship("MLModel", back_populates="dataset")


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    version = Column(Integer, nullable=False)

    # File paths
    parquet_path = Column(String, nullable=False)
    schema_path = Column(String, nullable=False)
    checksum = Column(String, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    dataset = relationship("Dataset", back_populates="versions")


class DatasetGroup(Base):
    __tablename__ = "dataset_groups"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    memberships = relationship("DatasetGroupMembership", back_populates="group")
    queries = relationship("Query", back_populates="group")


class DatasetGroupMembership(Base):
    __tablename__ = "dataset_group_memberships"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String, ForeignKey("dataset_groups.id"), nullable=False)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)

    # Alias for this dataset in the group (e.g., "sales", "customers")
    alias = Column(String, nullable=True)

    # Order for display purposes
    display_order = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    group = relationship("DatasetGroup", back_populates="memberships")
    dataset = relationship("Dataset")


class DatasetGroupRelationship(Base):
    __tablename__ = "dataset_group_relationships"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String, ForeignKey("dataset_groups.id"), nullable=False)

    # From table/column
    from_dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    from_column = Column(String, nullable=False)

    # To table/column
    to_dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    to_column = Column(String, nullable=False)

    # JOIN type
    join_type = Column(String, default="INNER", nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    group = relationship("DatasetGroup")
    from_dataset = relationship("Dataset", foreign_keys=[from_dataset_id])
    to_dataset = relationship("Dataset", foreign_keys=[to_dataset_id])
