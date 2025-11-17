from sqlalchemy import Column, String, DateTime, JSON
from datetime import datetime
import uuid
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    action = Column(String, nullable=False)  # upload, query, export, delete
    resource_type = Column(String, nullable=False)  # dataset, query, visualization
    resource_id = Column(String, nullable=True)

    audit_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
