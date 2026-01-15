"""
Skill schemas for Anthropic-style skills framework

Skills are self-contained instruction sets that enhance agent capabilities
by providing domain-specific knowledge and workflows.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class SkillType(str, Enum):
    """Types of skills"""
    BUILTIN = "builtin"
    USER_CREATED = "user_created"
    COMMUNITY = "community"


class SkillScope(str, Enum):
    """Scope of skill applicability"""
    DATA_ANALYSIS = "data_analysis"
    VISUALIZATION = "visualization"
    SQL = "sql"
    BUSINESS_INTELLIGENCE = "business_intelligence"
    DATA_QUALITY = "data_quality"
    GENERAL = "general"


class SkillMetadata(BaseModel):
    """Metadata from YAML frontmatter"""
    name: str
    description: str
    tags: List[str] = Field(default_factory=list)
    version: str = "1.0.0"
    author: Optional[str] = None
    scope: SkillScope = SkillScope.GENERAL
    prerequisites: List[str] = Field(default_factory=list)
    related_skills: List[str] = Field(default_factory=list)
    recommended_tools: List[str] = Field(default_factory=list)


class SkillSection(BaseModel):
    """A section within a skill"""
    title: str
    content: str
    subsections: List['SkillSection'] = Field(default_factory=list)


class SkillExample(BaseModel):
    """An example within a skill"""
    title: str
    goal: str
    steps: List[str]
    expected_outcome: Optional[str] = None


class SkillContent(BaseModel):
    """Parsed skill content"""
    overview: str
    workflow: Optional[str] = None
    sections: List[SkillSection] = Field(default_factory=list)
    examples: List[SkillExample] = Field(default_factory=list)
    best_practices: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class Skill(BaseModel):
    """Complete skill definition"""
    metadata: SkillMetadata
    content: SkillContent
    raw_content: str  # Full markdown content
    type: SkillType = SkillType.BUILTIN
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_context_string(self, include_examples: bool = True, max_tokens: int = 2000) -> str:
        """
        Convert skill to string for LLM context injection

        Args:
            include_examples: Whether to include examples
            max_tokens: Approximate token limit (1 token ≈ 4 chars)

        Returns:
            Formatted skill content for LLM
        """
        parts = []

        # Header
        parts.append(f"# {self.metadata.name}")
        parts.append(f"\n{self.metadata.description}\n")

        # Overview
        if self.content.overview:
            parts.append(f"## Overview\n{self.content.overview}\n")

        # Workflow
        if self.content.workflow:
            parts.append(f"## Workflow\n{self.content.workflow}\n")

        # Sections
        for section in self.content.sections:
            parts.append(f"## {section.title}\n{section.content}\n")

        # Examples (if requested)
        if include_examples and self.content.examples:
            parts.append("## Examples\n")
            for example in self.content.examples[:2]:  # Limit to 2 examples
                parts.append(f"### {example.title}")
                parts.append(f"**Goal**: {example.goal}")
                parts.append("**Steps**:")
                for i, step in enumerate(example.steps, 1):
                    parts.append(f"{i}. {step}")
                if example.expected_outcome:
                    parts.append(f"**Expected**: {example.expected_outcome}")
                parts.append("")

        # Best practices
        if self.content.best_practices:
            parts.append("## Best Practices\n")
            for practice in self.content.best_practices:
                parts.append(f"- {practice}")
            parts.append("")

        # Warnings
        if self.content.warnings:
            parts.append("## Important Warnings\n")
            for warning in self.content.warnings:
                parts.append(f"⚠️  {warning}")
            parts.append("")

        # Combine and truncate
        result = "\n".join(parts)
        max_chars = max_tokens * 4  # Rough approximation

        if len(result) > max_chars:
            # Truncate intelligently at section boundary
            result = result[:max_chars].rsplit('\n##', 1)[0]
            result += "\n\n... (skill content truncated for brevity)"

        return result


class SkillDiscoveryRequest(BaseModel):
    """Request for skill discovery"""
    task_description: str
    scope: Optional[SkillScope] = None
    context: Optional[Dict[str, Any]] = None
    required_tags: List[str] = Field(default_factory=list)


class SkillDiscoveryResponse(BaseModel):
    """Response with discovered skills"""
    skills: List[Skill]
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)


class SkillUsageEvent(BaseModel):
    """Event tracking skill usage"""
    skill_name: str
    session_id: str
    agent_name: str
    task_description: str
    success: bool
    helpful: Optional[bool] = None
    feedback: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SkillEvaluation(BaseModel):
    """Evaluation of skill effectiveness"""
    skill_name: str
    total_uses: int
    successful_uses: int
    success_rate: float
    average_confidence: float
    helpful_count: int
    not_helpful_count: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Update SkillSection to handle recursive type
SkillSection.model_rebuild()
