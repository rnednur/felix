"""
Skill Context Builder - formats skills for LLM injection

This module takes discovered skills and formats them into concise,
token-efficient context strings that can be injected into LLM prompts.
"""
from typing import List, Optional, Dict, Any
import logging

from app.schemas.skill import Skill, SkillScope


logger = logging.getLogger("skill.context")


class SkillContextBuilder:
    """
    Builds LLM-ready context from skills

    Takes skills and formats them into compact, structured text
    that can be injected into agent prompts to enhance capabilities.
    """

    def __init__(self, max_tokens: int = 2000):
        """
        Initialize context builder

        Args:
            max_tokens: Maximum tokens to use for skill context
        """
        self.max_tokens = max_tokens
        self.logger = logging.getLogger("skill.context")

    def build_context(
        self,
        skills: List[Skill],
        include_examples: bool = True,
        include_best_practices: bool = True,
        include_warnings: bool = True,
        prioritize_scope: Optional[SkillScope] = None
    ) -> str:
        """
        Build formatted context string from skills

        Args:
            skills: List of skills to include
            include_examples: Include example sections
            include_best_practices: Include best practices
            include_warnings: Include warnings
            prioritize_scope: Prioritize skills with this scope

        Returns:
            Formatted context string
        """
        if not skills:
            return ""

        # Sort skills by priority
        sorted_skills = self._sort_skills_by_priority(skills, prioritize_scope)

        # Build context sections
        sections = []
        sections.append("# Available Skills\n")
        sections.append("You have access to the following skills to enhance your capabilities:\n")

        remaining_tokens = self.max_tokens
        skills_added = 0

        for skill in sorted_skills:
            # Format individual skill
            skill_text = self._format_skill(
                skill,
                include_examples=include_examples,
                include_best_practices=include_best_practices,
                include_warnings=include_warnings
            )

            # Rough token estimate (4 chars per token)
            estimated_tokens = len(skill_text) // 4

            if estimated_tokens > remaining_tokens:
                self.logger.warning(
                    f"Reached token limit. Added {skills_added}/{len(sorted_skills)} skills"
                )
                break

            sections.append(skill_text)
            remaining_tokens -= estimated_tokens
            skills_added += 1

        if skills_added < len(sorted_skills):
            sections.append(
                f"\n*Note: {len(sorted_skills) - skills_added} additional skills "
                f"available but omitted due to context length limits.*\n"
            )

        context = "\n".join(sections)
        self.logger.info(
            f"Built skill context: {skills_added} skills, "
            f"~{len(context) // 4} tokens"
        )

        return context

    def _format_skill(
        self,
        skill: Skill,
        include_examples: bool = True,
        include_best_practices: bool = True,
        include_warnings: bool = True
    ) -> str:
        """
        Format a single skill for LLM context

        Args:
            skill: Skill to format
            include_examples: Include examples
            include_best_practices: Include best practices
            include_warnings: Include warnings

        Returns:
            Formatted skill text
        """
        parts = []

        # Header
        parts.append(f"## {skill.metadata.display_name or skill.metadata.name}")
        parts.append(f"**Scope**: {skill.metadata.scope.value}")
        parts.append(f"**Tags**: {', '.join(skill.metadata.tags)}")
        parts.append(f"\n{skill.metadata.description}\n")

        # Instructions (most important)
        if skill.content.instructions:
            parts.append("**Instructions:**")
            for section in skill.content.instructions:
                parts.append(f"\n### {section.title}")
                parts.append(section.content)

        # Examples (if requested and available)
        if include_examples and skill.content.examples:
            parts.append("\n**Examples:**")
            # Limit to 2 most relevant examples
            for example in skill.content.examples[:2]:
                parts.append(f"\n- **Goal**: {example.goal}")
                if example.code:
                    parts.append(f"  ```{example.language or 'python'}")
                    parts.append(f"  {example.code[:200]}...")  # Truncate long code
                    parts.append("  ```")
                if example.explanation:
                    parts.append(f"  *{example.explanation}*")

        # Best Practices (if requested)
        if include_best_practices and skill.content.best_practices:
            parts.append("\n**Best Practices:**")
            for practice in skill.content.best_practices[:3]:  # Top 3
                parts.append(f"- {practice}")

        # Warnings (if requested)
        if include_warnings and skill.content.warnings:
            parts.append("\n**⚠️ Warnings:**")
            for warning in skill.content.warnings:
                parts.append(f"- {warning}")

        parts.append("\n---\n")

        return "\n".join(parts)

    def _sort_skills_by_priority(
        self,
        skills: List[Skill],
        prioritize_scope: Optional[SkillScope] = None
    ) -> List[Skill]:
        """
        Sort skills by priority

        Args:
            skills: Skills to sort
            prioritize_scope: Scope to prioritize

        Returns:
            Sorted skills list
        """
        def priority_key(skill: Skill) -> tuple:
            # Higher priority = lower number (for sorting)
            scope_priority = 0
            if prioritize_scope and skill.metadata.scope == prioritize_scope:
                scope_priority = -100  # Very high priority

            # Scope-based priority
            scope_weights = {
                SkillScope.GLOBAL: -50,
                SkillScope.AGENT: -30,
                SkillScope.WORKFLOW: -20,
                SkillScope.TASK: -10,
            }
            scope_weight = scope_weights.get(skill.metadata.scope, 0)

            return (scope_priority + scope_weight, skill.metadata.name)

        return sorted(skills, key=priority_key)

    def build_compact_context(self, skills: List[Skill]) -> str:
        """
        Build ultra-compact context (names and descriptions only)

        Useful when token budget is very limited.

        Args:
            skills: Skills to include

        Returns:
            Compact context string
        """
        if not skills:
            return ""

        lines = ["# Available Skills\n"]

        for skill in skills:
            lines.append(
                f"- **{skill.metadata.name}**: {skill.metadata.description} "
                f"(tags: {', '.join(skill.metadata.tags[:3])})"
            )

        return "\n".join(lines)

    def build_skill_list(self, skills: List[Skill]) -> str:
        """
        Build simple skill list (for selection UI)

        Args:
            skills: Skills to list

        Returns:
            Formatted skill list
        """
        if not skills:
            return "No skills available."

        lines = []

        for i, skill in enumerate(skills, 1):
            lines.append(
                f"{i}. **{skill.metadata.display_name or skill.metadata.name}** "
                f"({skill.metadata.scope.value})"
            )
            lines.append(f"   {skill.metadata.description}")
            lines.append(f"   Tags: {', '.join(skill.metadata.tags)}")
            lines.append("")

        return "\n".join(lines)

    def build_system_prompt_enhancement(
        self,
        skills: List[Skill],
        agent_role: str = "data analyst"
    ) -> str:
        """
        Build a system prompt enhancement that integrates skills

        This is meant to be appended to an agent's system prompt.

        Args:
            skills: Available skills
            agent_role: The agent's role (for context)

        Returns:
            System prompt addition
        """
        if not skills:
            return ""

        skill_names = [skill.metadata.name for skill in skills]

        prompt = f"""
# Enhanced Capabilities

You are a {agent_role} with access to specialized skills that enhance your capabilities.

## Available Skills

You can apply the following skills when relevant to the user's request:

{', '.join(skill_names)}

## Skill Usage Guidelines

1. **Automatic Application**: Apply skills automatically when you detect they're relevant to the task
2. **Combine Skills**: You can use multiple skills together when appropriate
3. **Follow Instructions**: Each skill has specific instructions and best practices - follow them carefully
4. **Acknowledge Usage**: When you use a skill, briefly mention it in your response
5. **Warnings**: Pay attention to skill warnings to avoid common mistakes

## Skill Details

"""

        # Add compact skill descriptions
        for skill in skills:
            prompt += f"\n### {skill.metadata.name}\n"
            prompt += f"{skill.metadata.description}\n"

            # Add key instructions (first section only)
            if skill.content.instructions:
                first_instruction = skill.content.instructions[0]
                prompt += f"\n**{first_instruction.title}**\n"
                prompt += f"{first_instruction.content[:300]}...\n"  # Truncate

        return prompt

    def build_context_with_examples(
        self,
        skills: List[Skill],
        task_description: str
    ) -> Dict[str, Any]:
        """
        Build context with task-specific examples

        Selects most relevant examples based on task description.

        Args:
            skills: Available skills
            task_description: Current task description

        Returns:
            Dict with 'context' and 'examples' keys
        """
        task_lower = task_description.lower()

        context_parts = []
        relevant_examples = []

        for skill in skills:
            context_parts.append(
                f"**{skill.metadata.name}**: {skill.metadata.description}"
            )

            # Find relevant examples
            for example in skill.content.examples:
                if example.goal and any(
                    word in task_lower
                    for word in example.goal.lower().split()
                    if len(word) > 3
                ):
                    relevant_examples.append({
                        "skill": skill.metadata.name,
                        "goal": example.goal,
                        "code": example.code,
                        "language": example.language,
                        "explanation": example.explanation
                    })

        return {
            "context": "\n".join(context_parts),
            "examples": relevant_examples[:5]  # Top 5 most relevant
        }


# Global instance
_context_builder: Optional[SkillContextBuilder] = None


def get_context_builder(max_tokens: int = 2000) -> SkillContextBuilder:
    """Get the global context builder instance"""
    global _context_builder
    if _context_builder is None:
        _context_builder = SkillContextBuilder(max_tokens=max_tokens)
    return _context_builder
