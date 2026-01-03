"""
Research job tracking model for async deep research execution
"""
from sqlalchemy import Column, String, DateTime, Integer, JSON, Text, Enum as SQLEnum
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class ResearchJobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchJob(Base):
    __tablename__ = "research_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Job info
    dataset_id = Column(String, nullable=False)
    main_question = Column(Text, nullable=False)
    verbose_mode = Column(Integer, default=0, nullable=False)  # 0=off, 1=on

    # Celery task info
    celery_task_id = Column(String, nullable=True)

    # Status tracking
    status = Column(SQLEnum(ResearchJobStatus), default=ResearchJobStatus.PENDING, nullable=False)
    current_stage = Column(String, nullable=True)  # e.g., "Stage 3/7: Executing queries"
    progress_percentage = Column(Integer, default=0)  # 0-100

    # Results
    result = Column(JSON, nullable=True)  # Full DeepResearchResponse JSON
    error_message = Column(Text, nullable=True)

    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    execution_time_seconds = Column(Integer, nullable=True)

    # Additional context (renamed from 'metadata' to avoid SQLAlchemy conflict)
    job_metadata = Column(JSON, nullable=True)
