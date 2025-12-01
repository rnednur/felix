from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from app.core.database import Base


class ExecutionMode(str, enum.Enum):
    SQL = "sql"
    PYTHON = "python"
    ML = "ml"
    WORKFLOW = "workflow"
    STATS = "stats"


class ExecutionStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class CodeExecution(Base):
    __tablename__ = "code_executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)

    # Input
    nl_input = Column(Text, nullable=False)  # Natural language query
    mode = Column(SQLEnum(ExecutionMode, values_callable=lambda x: [e.value for e in x]), nullable=False)

    # Generated code
    generated_code = Column(Text, nullable=True)
    generated_sql = Column(Text, nullable=True)  # For SQL mode fallback

    # Execution details
    execution_status = Column(SQLEnum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False)
    execution_time_ms = Column(Integer, nullable=True)

    # Results
    result_path = Column(String, nullable=True)  # Path to cached result
    result_summary = Column(JSON, nullable=True)  # Brief summary of results
    visualizations = Column(JSON, nullable=True)  # Visualization specs/images

    # Error handling
    error_message = Column(Text, nullable=True)
    error_trace = Column(Text, nullable=True)

    # Code metadata
    code_metadata = Column(JSON, nullable=True)  # Retrieved columns, confidence, steps, etc.

    # Workflow info
    workflow_id = Column(String, nullable=True)  # If part of multi-step workflow
    step_number = Column(Integer, nullable=True)  # Step number in workflow

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    dataset = relationship("Dataset", back_populates="code_executions")
    ml_models = relationship("MLModel", back_populates="code_execution")


class MLModel(Base):
    __tablename__ = "ml_models"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    code_execution_id = Column(String, ForeignKey("code_executions.id"), nullable=True)

    # Model info
    name = Column(String, nullable=True)  # User-friendly name
    model_type = Column(String, nullable=False)  # 'regression', 'classification', 'clustering', etc.
    framework = Column(String, nullable=True)  # 'scikit-learn', 'statsmodels', etc.

    # Training details
    features = Column(JSON, nullable=False)  # List of feature column names
    target_column = Column(String, nullable=True)  # Target column (null for unsupervised)
    training_info = Column(JSON, nullable=True)  # Training parameters, config

    # Model performance
    metrics = Column(JSON, nullable=False)  # R², accuracy, RMSE, etc.
    feature_importance = Column(JSON, nullable=True)  # Feature importance scores

    # Persistence
    model_artifact_path = Column(String, nullable=False)  # Path to pickled model
    model_metadata_path = Column(String, nullable=True)  # Path to metadata JSON

    # Status
    status = Column(String, default='active', nullable=False)  # 'active', 'archived', 'deprecated'

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    dataset = relationship("Dataset", back_populates="ml_models")
    code_execution = relationship("CodeExecution", back_populates="ml_models")
