"""
Skill Tool - bridges skills with the agent tool system

This tool allows agents to dynamically discover and apply skills
during the agent loop execution.
"""
from typing import Dict, Any, List, Optional
import logging

from app.tools.base_tool import BaseTool, ToolResult, ToolCapability
from app.schemas.tool import ToolSchema, ToolParameter
from app.schemas.skill import (
    Skill,
    SkillDiscoveryRequest,
    SkillScope,
    SkillUsageEvent
)
from app.skills.catalog import get_skill_catalog
from app.skills.context_builder import get_context_builder


logger = logging.getLogger("tool.skill")


class SkillTool(BaseTool):
    """
    Tool for skill discovery and application

    This tool allows agents to:
    1. Discover relevant skills for a task
    2. Get skill context for LLM prompts
    3. Track skill usage
    """

    def __init__(self):
        self.catalog = get_skill_catalog()
        self.context_builder = get_context_builder()
        self.logger = logging.getLogger("tool.skill")

    def get_schema(self) -> ToolSchema:
        """Get tool schema"""
        return ToolSchema(
            name="skill_tool",
            description=(
                "Discover and apply specialized skills to enhance agent capabilities. "
                "Skills are instruction sets that provide domain expertise, best practices, "
                "and examples for specific types of tasks."
            ),
            category="enhancement",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description=(
                        "Action to perform: 'discover' (find relevant skills), "
                        "'get_context' (get formatted skill context), "
                        "'list' (list all skills), "
                        "'track_usage' (record skill usage)"
                    ),
                    required=True
                ),
                ToolParameter(
                    name="task_description",
                    type="string",
                    description="Description of the task (for 'discover' action)",
                    required=False
                ),
                ToolParameter(
                    name="skill_names",
                    type="array",
                    description="List of skill names (for 'get_context' action)",
                    required=False
                ),
                ToolParameter(
                    name="scope",
                    type="string",
                    description="Skill scope filter: global, agent, workflow, task",
                    required=False
                ),
                ToolParameter(
                    name="required_tags",
                    type="array",
                    description="Required tags for skill discovery",
                    required=False
                ),
                ToolParameter(
                    name="include_examples",
                    type="boolean",
                    description="Include examples in context (default: true)",
                    required=False
                ),
                ToolParameter(
                    name="usage_event",
                    type="object",
                    description="Usage event data (for 'track_usage' action)",
                    required=False
                )
            ],
            returns={
                "type": "object",
                "properties": {
                    "skills": {
                        "type": "array",
                        "description": "List of relevant skills"
                    },
                    "context": {
                        "type": "string",
                        "description": "Formatted skill context for LLM"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Reasoning for skill selection"
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence in skill selection (0.0-1.0)"
                    }
                }
            },
            requires_approval=False
        )

    def get_capability(self) -> ToolCapability:
        """Get tool capability description"""
        return ToolCapability(
            keywords=[
                "skill", "skills", "enhance", "capability", "instruction",
                "best practices", "examples", "expertise", "guidance"
            ],
            description=(
                "Discovers and applies specialized skills to enhance agent capabilities "
                "with domain expertise, best practices, and examples."
            ),
            examples=[
                "Find skills relevant to SQL query optimization",
                "Get context for data visualization skills",
                "List all available data analysis skills"
            ]
        )

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute skill tool action

        Args:
            parameters: Tool parameters

        Returns:
            ToolResult with skill data
        """
        try:
            self._validate_parameters(parameters)

            action = parameters.get("action")

            if action == "discover":
                return await self._discover_skills(parameters)
            elif action == "get_context":
                return await self._get_context(parameters)
            elif action == "list":
                return await self._list_skills(parameters)
            elif action == "track_usage":
                return await self._track_usage(parameters)
            else:
                return ToolResult(
                    tool_name="skill_tool",
                    success=False,
                    data={},
                    error=f"Unknown action: {action}"
                )

        except Exception as e:
            self.logger.error(f"Skill tool execution failed: {str(e)}", exc_info=True)
            return ToolResult(
                tool_name="skill_tool",
                success=False,
                data={},
                error=f"Execution failed: {str(e)}"
            )

    async def _discover_skills(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Discover relevant skills for a task

        Args:
            parameters: Parameters with task_description

        Returns:
            ToolResult with discovered skills
        """
        task_description = parameters.get("task_description")
        if not task_description:
            return ToolResult(
                tool_name="skill_tool",
                success=False,
                data={},
                error="task_description is required for 'discover' action"
            )

        # Parse optional filters
        scope_str = parameters.get("scope")
        scope = SkillScope(scope_str) if scope_str else None
        required_tags = parameters.get("required_tags", [])

        # Build discovery request
        request = SkillDiscoveryRequest(
            task_description=task_description,
            scope=scope,
            required_tags=required_tags
        )

        # Discover skills
        self.logger.info(f"Discovering skills for task: {task_description}")
        response = self.catalog.discover_skills(request)

        # Format skills for response
        skills_data = [
            {
                "name": skill.metadata.name,
                "display_name": skill.metadata.display_name,
                "description": skill.metadata.description,
                "scope": skill.metadata.scope.value,
                "tags": skill.metadata.tags,
                "version": skill.metadata.version
            }
            for skill in response.skills
        ]

        self.logger.info(
            f"Found {len(skills_data)} skills with confidence {response.confidence:.2f}"
        )

        return ToolResult(
            tool_name="skill_tool",
            success=True,
            data={
                "skills": skills_data,
                "reasoning": response.reasoning,
                "confidence": response.confidence,
                "count": len(skills_data)
            },
            metadata={
                "action": "discover",
                "task_description": task_description
            }
        )

    async def _get_context(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Get formatted context for skills

        Args:
            parameters: Parameters with skill_names

        Returns:
            ToolResult with formatted context
        """
        skill_names = parameters.get("skill_names")
        if not skill_names:
            return ToolResult(
                tool_name="skill_tool",
                success=False,
                data={},
                error="skill_names is required for 'get_context' action"
            )

        # Get skills from catalog
        skills = [
            self.catalog.get_skill(name)
            for name in skill_names
            if self.catalog.get_skill(name) is not None
        ]

        if not skills:
            return ToolResult(
                tool_name="skill_tool",
                success=False,
                data={},
                error=f"No skills found with names: {skill_names}"
            )

        # Build context
        include_examples = parameters.get("include_examples", True)
        scope_str = parameters.get("scope")
        prioritize_scope = SkillScope(scope_str) if scope_str else None

        context = self.context_builder.build_context(
            skills=skills,
            include_examples=include_examples,
            prioritize_scope=prioritize_scope
        )

        self.logger.info(f"Built context for {len(skills)} skills (~{len(context) // 4} tokens)")

        return ToolResult(
            tool_name="skill_tool",
            success=True,
            data={
                "context": context,
                "skill_count": len(skills),
                "estimated_tokens": len(context) // 4,
                "skills": [skill.metadata.name for skill in skills]
            },
            metadata={
                "action": "get_context",
                "include_examples": include_examples
            }
        )

    async def _list_skills(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        List all available skills

        Args:
            parameters: Optional filters (scope, tags)

        Returns:
            ToolResult with skill list
        """
        # Parse filters
        scope_str = parameters.get("scope")
        scope = SkillScope(scope_str) if scope_str else None
        tags = parameters.get("tags", [])

        # Get filtered skills
        skills = self.catalog.list_skills(
            scope=scope,
            tags=tags if tags else None,
            enabled_only=True
        )

        # Format skills
        skills_data = [
            {
                "name": skill.metadata.name,
                "display_name": skill.metadata.display_name,
                "description": skill.metadata.description,
                "scope": skill.metadata.scope.value,
                "tags": skill.metadata.tags,
                "version": skill.metadata.version,
                "author": skill.metadata.author
            }
            for skill in skills
        ]

        self.logger.info(f"Listed {len(skills_data)} skills")

        return ToolResult(
            tool_name="skill_tool",
            success=True,
            data={
                "skills": skills_data,
                "count": len(skills_data),
                "total_skills": self.catalog.get_skill_count(),
                "enabled_skills": self.catalog.get_enabled_count()
            },
            metadata={
                "action": "list",
                "filters": {
                    "scope": scope.value if scope else None,
                    "tags": tags
                }
            }
        )

    async def _track_usage(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Track skill usage event

        Args:
            parameters: Parameters with usage_event

        Returns:
            ToolResult confirming tracking
        """
        usage_data = parameters.get("usage_event")
        if not usage_data:
            return ToolResult(
                tool_name="skill_tool",
                success=False,
                data={},
                error="usage_event is required for 'track_usage' action"
            )

        try:
            event = SkillUsageEvent(**usage_data)
            self.catalog.track_usage(event)

            self.logger.info(
                f"Tracked usage: {event.skill_name} (success={event.success})"
            )

            return ToolResult(
                tool_name="skill_tool",
                success=True,
                data={
                    "tracked": True,
                    "skill_name": event.skill_name,
                    "success": event.success
                },
                metadata={
                    "action": "track_usage"
                }
            )

        except Exception as e:
            return ToolResult(
                tool_name="skill_tool",
                success=False,
                data={},
                error=f"Failed to track usage: {str(e)}"
            )


class SkillEnhancedTool(BaseTool):
    """
    Base class for tools enhanced with skills

    Tools that inherit from this can automatically discover and apply
    relevant skills during execution.
    """

    def __init__(self):
        super().__init__()
        self.skill_tool = SkillTool()
        self.logger = logging.getLogger(f"tool.{self.__class__.__name__}")

    async def discover_relevant_skills(
        self,
        task_description: str,
        scope: Optional[SkillScope] = None
    ) -> List[Skill]:
        """
        Discover skills relevant to current task

        Args:
            task_description: Description of the task
            scope: Optional scope filter

        Returns:
            List of relevant skills
        """
        result = await self.skill_tool.execute({
            "action": "discover",
            "task_description": task_description,
            "scope": scope.value if scope else None
        })

        if not result.success:
            self.logger.warning(f"Skill discovery failed: {result.error}")
            return []

        # Get full skill objects
        skill_names = [s["name"] for s in result.data.get("skills", [])]
        catalog = get_skill_catalog()

        skills = [
            catalog.get_skill(name)
            for name in skill_names
            if catalog.get_skill(name) is not None
        ]

        return skills

    async def get_skill_context(
        self,
        skills: List[Skill],
        include_examples: bool = True
    ) -> str:
        """
        Get formatted context for skills

        Args:
            skills: Skills to format
            include_examples: Include examples

        Returns:
            Formatted context string
        """
        if not skills:
            return ""

        result = await self.skill_tool.execute({
            "action": "get_context",
            "skill_names": [skill.metadata.name for skill in skills],
            "include_examples": include_examples
        })

        if not result.success:
            self.logger.warning(f"Failed to get skill context: {result.error}")
            return ""

        return result.data.get("context", "")

    async def track_skill_usage(
        self,
        skill_name: str,
        success: bool,
        helpful: Optional[bool] = None,
        feedback: Optional[str] = None
    ):
        """
        Track skill usage

        Args:
            skill_name: Name of skill used
            success: Whether skill application was successful
            helpful: Whether skill was helpful (user feedback)
            feedback: Additional feedback
        """
        await self.skill_tool.execute({
            "action": "track_usage",
            "usage_event": {
                "skill_name": skill_name,
                "success": success,
                "helpful": helpful,
                "feedback": feedback
            }
        })
