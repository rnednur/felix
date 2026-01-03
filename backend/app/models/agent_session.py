"""
Agent Session models for database persistence
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class AgentSession(Base):
    """Agent chat session"""
    __tablename__ = "agent_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # Optional for now
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    name = Column(String, nullable=True)  # User-friendly name

    # Session metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    messages = relationship("AgentMessage", back_populates="session", cascade="all, delete-orphan")
    executions = relationship("AgentExecution", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AgentSession {self.id} - {self.name or 'Unnamed'}>"


class AgentMessage(Base):
    """Message in agent conversation"""
    __tablename__ = "agent_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("agent_sessions.id"), nullable=False)

    role = Column(String, nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)

    # Agent metadata
    agent_name = Column(String, nullable=True)  # Which agent responded
    code = Column(Text, nullable=True)  # Generated code
    result_data = Column(JSON, nullable=True)  # Result data

    # Tokens and cost tracking
    tokens_used = Column(Integer, default=0)
    execution_time_ms = Column(Integer, default=0)

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("AgentSession", back_populates="messages")

    def __repr__(self):
        return f"<AgentMessage {self.id} - {self.role}: {self.content[:50]}...>"


class AgentExecution(Base):
    """Track agent execution metrics"""
    __tablename__ = "agent_executions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("agent_sessions.id"), nullable=True)
    agent_name = Column(String, nullable=False)

    # Execution details
    query = Column(Text, nullable=False)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    execution_mode = Column(String, nullable=True)  # 'single', 'sequential', 'parallel'
    status = Column(String, nullable=False)  # 'success', 'failed', 'partial'

    # Performance metrics
    execution_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)

    # Results
    result_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    result_data = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("AgentSession", back_populates="executions")

    def __repr__(self):
        return f"<AgentExecution {self.id} - {self.agent_name}: {self.status}>"
