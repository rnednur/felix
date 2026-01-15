"""
Skill Database Model - persistent storage for skills
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class SkillSourceType(str, enum.Enum):
    """Source of the skill"""
    BUILTIN = "builtin"  # Shipped with system
    USER = "user"        # Created by user
    IMPORTED = "imported"  # Imported from external source
    COMMUNITY = "community"  # From community repository


class SkillStatus(str, enum.Enum):
    """Skill status"""
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class SkillModel(Base):
    """
    Persistent storage for skills

    Stores skills in database for:
    - User-created custom skills
    - Modified builtin skills
    - Versioning and audit trail
    - Usage tracking
    """

    __tablename__ = "skills"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Metadata
    name = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(200), nullable=True)
    description = Column(Text, nullable=False)
    version = Column(String(20), nullable=False, default="1.0.0")

    # Scope
    scope = Column(String(20), nullable=False, index=True)  # global, agent, workflow, task

    # Content
    raw_content = Column(Text, nullable=False)  # Full SKILL.md content
    parsed_content = Column(JSON, nullable=True)  # Parsed structure

    # Tags for discovery
    tags = Column(JSON, nullable=False, default=list)  # List of strings

    # Source and ownership
    source_type = Column(SQLEnum(SkillSourceType), nullable=False, default=SkillSourceType.USER)
    author_id = Column(String, ForeignKey("users.id"), nullable=True)

    # Status
    status = Column(SQLEnum(SkillStatus), nullable=False, default=SkillStatus.DRAFT)
    enabled = Column(Boolean, nullable=False, default=True)

    # Timestamps (following codebase pattern)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    published_at = Column(DateTime, nullable=True)
    deprecated_at = Column(DateTime, nullable=True)

    # Usage tracking
    usage_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    helpful_count = Column(Integer, nullable=False, default=0)
    not_helpful_count = Column(Integer, nullable=False, default=0)

    # Additional metadata (renamed to avoid SQLAlchemy reserved word)
    extra_metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<Skill(name='{self.name}', scope='{self.scope}', version='{self.version}')>"

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count

    @property
    def helpfulness_score(self) -> float:
        """Calculate helpfulness score"""
        total_feedback = self.helpful_count + self.not_helpful_count
        if total_feedback == 0:
            return 0.0
        return self.helpful_count / total_feedback

    def record_usage(self, success: bool, helpful: bool = None):
        """Record a usage event"""
        self.usage_count += 1
        if success:
            self.success_count += 1
        if helpful is True:
            self.helpful_count += 1
        elif helpful is False:
            self.not_helpful_count += 1

    def publish(self):
        """Publish the skill"""
        self.status = SkillStatus.PUBLISHED
        self.published_at = datetime.utcnow()

    def deprecate(self):
        """Mark skill as deprecated"""
        self.status = SkillStatus.DEPRECATED
        self.deprecated_at = datetime.utcnow()


class SkillVersion(Base):
    """
    Skill version history

    Tracks changes to skills over time.
    """

    __tablename__ = "skill_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Reference to skill
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False)
    skill = relationship("SkillModel", backref="versions")

    # Version details
    version = Column(String(20), nullable=False)
    raw_content = Column(Text, nullable=False)
    parsed_content = Column(JSON, nullable=True)

    # Metadata
    author_id = Column(String, ForeignKey("users.id"), nullable=True)
    change_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SkillVersion(skill_id='{self.skill_id}', version='{self.version}')>"


class SkillUsageEvent(Base):
    """
    Individual skill usage events

    Detailed tracking of when and how skills are used.
    """

    __tablename__ = "skill_usage_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # References
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False, index=True)
    skill = relationship("SkillModel", backref="usage_events")

    user_id = Column(String, ForeignKey("users.id"), nullable=True)

    session_id = Column(String(100), nullable=True, index=True)
    agent_name = Column(String(100), nullable=True)

    # Outcome
    success = Column(Boolean, nullable=False)
    helpful = Column(Boolean, nullable=True)  # User feedback

    # Context
    task_description = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)

    # Additional metadata (renamed to avoid SQLAlchemy reserved word)
    extra_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SkillUsageEvent(skill_id='{self.skill_id}', success={self.success})>"
