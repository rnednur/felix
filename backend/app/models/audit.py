from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # User who performed the action
    user_id = Column(String, ForeignKey("users.id"), nullable=True)

    # Action details
    action = Column(String, nullable=False)  # upload, query, export, delete, share, login, etc.
    resource_type = Column(String, nullable=False)  # dataset, query, visualization, user
    resource_id = Column(String, nullable=True)

    # Request metadata
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    audit_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
