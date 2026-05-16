"""
Skill Catalog - registry and discovery for skills

Similar to ToolCatalog but for Anthropic-style skills.
"""
from typing import Dict, List, Optional, Tuple
import logging

from app.schemas.skill import (
    Skill,
    SkillDiscoveryRequest,
    SkillDiscoveryResponse,
    SkillScope,
    SkillUsageEvent,
    SkillEvaluation
)


logger = logging.getLogger("skill.catalog")


class SkillCatalog:
    """
    Central registry for skill discovery and management

    The catalog maintains all available skills and provides:
    - Skill registration
    - Dynamic skill discovery based on task descriptions
    - Search by tags, scope, name
    - Usage tracking and analytics
    """

    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.usage_events: List[SkillUsageEvent] = []
        self.logger = logging.getLogger("skill.catalog")

    def register_skill(self, skill: Skill):
        """
        Register a skill in the catalog

        Args:
            skill: Skill to register
        """
        self.skills[skill.metadata.name] = skill
        self.logger.info(f"Registered skill: {skill.metadata.name}")

    def get_skill(self, name: str) -> Optional[Skill]:
        """
        Get a skill by name

        Args:
            name: Skill name

        Returns:
            Skill or None if not found
        """
        return self.skills.get(name)

    def list_skills(
        self,
        scope: Optional[SkillScope] = None,
        tags: Optional[List[str]] = None,
        enabled_only: bool = True
    ) -> List[Skill]:
        """
        List skills with optional filtering

        Args:
            scope: Filter by scope
            tags: Filter by tags (any match)
            enabled_only: Only return enabled skills

        Returns:
            List of skills
        """
        skills = list(self.skills.values())

        # Filter by enabled status
        if enabled_only:
            skills = [s for s in skills if s.enabled]

        # Filter by scope
        if scope:
            skills = [s for s in skills if s.metadata.scope == scope]

        # Filter by tags
        if tags:
            skills = [
                s for s in skills
                if any(tag in s.metadata.tags for tag in tags)
            ]

        return skills

    def discover_skills(self, request: SkillDiscoveryRequest) -> SkillDiscoveryResponse:
        """
        Discover skills that can help with a task

        Uses keyword matching and tag matching to find suitable skills.

        Args:
            request: Discovery request with task description

        Returns:
            SkillDiscoveryResponse with ranked skills
        """
        candidates: List[Tuple[Skill, float]] = []

        # Get enabled skills
        enabled_skills = [s for s in self.skills.values() if s.enabled]

        # Filter by scope if specified
        if request.scope:
            enabled_skills = [s for s in enabled_skills if s.metadata.scope == request.scope]

        # Score each skill
        for skill in enabled_skills:
            confidence = self._calculate_confidence(skill, request)

            if confidence > 0.3:  # Threshold for inclusion
                candidates.append((skill, confidence))

        # Sort by confidence descending
        candidates.sort(key=lambda x: x[1], reverse=True)

        # Build response
        skills = [skill for skill, _ in candidates]
        overall_confidence = candidates[0][1] if candidates else 0.0

        reasoning = self._generate_reasoning(request, candidates)

        return SkillDiscoveryResponse(
            skills=skills,
            reasoning=reasoning,
            confidence=overall_confidence
        )

    def _calculate_confidence(self, skill: Skill, request: SkillDiscoveryRequest) -> float:
        """
        Calculate confidence that skill is relevant

        Args:
            skill: Skill to evaluate
            request: Discovery request

        Returns:
            Confidence score 0.0-1.0
        """
        task_lower = request.task_description.lower()
        confidence = 0.0

        # Check name match
        if skill.metadata.name.replace('-', ' ') in task_lower:
            confidence += 0.4

        # Check description match
        desc_words = skill.metadata.description.lower().split()
        desc_matches = sum(1 for word in desc_words if word in task_lower and len(word) > 3)
        if desc_matches > 0:
            confidence += min(0.3, desc_matches * 0.1)

        # Check tag matches
        tag_matches = sum(1 for tag in skill.metadata.tags if tag.lower() in task_lower)
        if tag_matches > 0:
            confidence += min(0.4, tag_matches * 0.15)

        # Check required tags
        if request.required_tags:
            required_matches = sum(1 for tag in request.required_tags if tag in skill.metadata.tags)
            if required_matches == len(request.required_tags):
                confidence += 0.3
            elif required_matches > 0:
                confidence += 0.15

        # Check scope match
        if request.scope and skill.metadata.scope == request.scope:
            confidence += 0.2

        # Check example goals
        for example in skill.content.examples:
            if example.goal and any(word in task_lower for word in example.goal.lower().split() if len(word) > 3):
                confidence += 0.1
                break

        return min(1.0, confidence)

    def _generate_reasoning(
        self,
        request: SkillDiscoveryRequest,
        candidates: List[Tuple[Skill, float]]
    ) -> str:
        """Generate reasoning for skill selection"""
        if not candidates:
            return "No suitable skills found for this task."

        top_skills = candidates[:3]
        skill_names = [skill.metadata.name for skill, _ in top_skills]

        reasoning = f"Found {len(candidates)} potential skills. "
        reasoning += f"Top candidates: {', '.join(skill_names)}. "

        if request.scope:
            reasoning += f"Filtered by scope: {request.scope.value}. "

        if request.required_tags:
            reasoning += f"Required tags: {', '.join(request.required_tags)}."

        return reasoning

    def search_by_tags(self, tags: List[str], match_all: bool = False) -> List[Skill]:
        """
        Search skills by tags

        Args:
            tags: List of tags to search for
            match_all: If True, skill must have all tags. If False, any tag matches.

        Returns:
            List of matching skills
        """
        results = []

        for skill in self.skills.values():
            if not skill.enabled:
                continue

            if match_all:
                # Must have all tags
                if all(tag in skill.metadata.tags for tag in tags):
                    results.append(skill)
            else:
                # Must have at least one tag
                if any(tag in skill.metadata.tags for tag in tags):
                    results.append(skill)

        return results

    def search_by_name(self, query: str) -> List[Skill]:
        """
        Search skills by name (fuzzy match)

        Args:
            query: Search query

        Returns:
            List of matching skills
        """
        query_lower = query.lower()
        results = []

        for skill in self.skills.values():
            if not skill.enabled:
                continue

            name_lower = skill.metadata.name.lower()
            desc_lower = skill.metadata.description.lower()

            if query_lower in name_lower or query_lower in desc_lower:
                results.append(skill)

        return results

    def get_skills_by_scope(self, scope: SkillScope) -> List[Skill]:
        """
        Get all skills in a scope

        Args:
            scope: Skill scope

        Returns:
            List of skills
        """
        return [
            skill for skill in self.skills.values()
            if skill.metadata.scope == scope and skill.enabled
        ]

    def track_usage(self, event: SkillUsageEvent):
        """
        Track skill usage for analytics

        Args:
            event: Usage event
        """
        self.usage_events.append(event)
        self.logger.info(f"Tracked usage: {event.skill_name} (success={event.success})")

    def get_skill_evaluation(self, skill_name: str) -> Optional[SkillEvaluation]:
        """
        Get evaluation metrics for a skill

        Args:
            skill_name: Skill name

        Returns:
            SkillEvaluation or None
        """
        # Filter events for this skill
        events = [e for e in self.usage_events if e.skill_name == skill_name]

        if not events:
            return None

        total_uses = len(events)
        successful_uses = sum(1 for e in events if e.success)
        success_rate = successful_uses / total_uses if total_uses > 0 else 0.0

        # Calculate helpful count
        helpful_count = sum(1 for e in events if e.helpful is True)
        not_helpful_count = sum(1 for e in events if e.helpful is False)

        # Average confidence (placeholder - would need to track this separately)
        average_confidence = 0.75

        return SkillEvaluation(
            skill_name=skill_name,
            total_uses=total_uses,
            successful_uses=successful_uses,
            success_rate=success_rate,
            average_confidence=average_confidence,
            helpful_count=helpful_count,
            not_helpful_count=not_helpful_count
        )

    def get_skill_count(self) -> int:
        """Get total number of registered skills"""
        return len(self.skills)

    def get_enabled_count(self) -> int:
        """Get number of enabled skills"""
        return sum(1 for skill in self.skills.values() if skill.enabled)

    def get_scopes(self) -> List[SkillScope]:
        """Get list of all skill scopes"""
        return list(set(
            skill.metadata.scope
            for skill in self.skills.values()
        ))

    def enable_skill(self, name: str):
        """Enable a skill"""
        if name in self.skills:
            self.skills[name].enabled = True
            self.logger.info(f"Enabled skill: {name}")

    def disable_skill(self, name: str):
        """Disable a skill"""
        if name in self.skills:
            self.skills[name].enabled = False
            self.logger.info(f"Disabled skill: {name}")


# Global skill catalog instance
_skill_catalog: Optional[SkillCatalog] = None


def get_skill_catalog() -> SkillCatalog:
    """Get the global skill catalog instance"""
    global _skill_catalog
    if _skill_catalog is None:
        _skill_catalog = SkillCatalog()
    return _skill_catalog


def init_skill_catalog() -> SkillCatalog:
    """Initialize and return a new skill catalog"""
    global _skill_catalog
    _skill_catalog = SkillCatalog()
    return _skill_catalog
