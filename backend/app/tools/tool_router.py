"""
Tool Router - intelligent tool selection and routing

Routes tasks to appropriate tools using both keyword matching and LLM-based reasoning.
"""
from typing import List, Optional, Dict, Any
import logging
from app.tools.catalog import ToolCatalog
from app.schemas.tool import (
    ToolDiscoveryRequest,
    ToolDiscoveryResponse,
    ToolCatalogEntry
)
from app.services.agents.llm_service import LLMService
import json


class ToolRouter:
    """
    Intelligent router for tool selection

    Uses a hybrid approach:
    1. Fast path: Keyword-based matching for simple cases
    2. Slow path: LLM-based reasoning for complex cases
    """

    def __init__(self, catalog: ToolCatalog, llm_service: Optional[LLMService] = None):
        self.catalog = catalog
        self.llm_service = llm_service or LLMService()
        self.logger = logging.getLogger("tool.router")

    async def route(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
        use_llm: bool = True
    ) -> ToolDiscoveryResponse:
        """
        Route a task to appropriate tools

        Args:
            task_description: Natural language task description
            context: Additional context (dataset_id, previous results, etc.)
            use_llm: Whether to use LLM for routing (fallback to keyword matching)

        Returns:
            ToolDiscoveryResponse with selected tools and reasoning
        """
        # Try fast path first
        fast_result = self._fast_path_route(task_description, context)

        if fast_result and fast_result.confidence > 0.8:
            self.logger.info(f"Fast path routing successful: {task_description}")
            return fast_result

        # Fall back to LLM-based routing
        if use_llm:
            self.logger.info(f"Using LLM for tool routing: {task_description}")
            return await self._llm_route(task_description, context)

        # Return fast path result even if confidence is low
        return fast_result or ToolDiscoveryResponse(
            tools=[],
            reasoning="No suitable tools found",
            confidence=0.0
        )

    def _fast_path_route(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ToolDiscoveryResponse]:
        """
        Fast keyword-based routing

        Args:
            task_description: Task description
            context: Optional context

        Returns:
            ToolDiscoveryResponse or None
        """
        request = ToolDiscoveryRequest(
            task_description=task_description,
            context=context
        )

        return self.catalog.discover_tools(request)

    async def _llm_route(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ToolDiscoveryResponse:
        """
        LLM-based routing for complex cases

        Args:
            task_description: Task description
            context: Optional context

        Returns:
            ToolDiscoveryResponse
        """
        # Get all available tools
        available_tools = self.catalog.list_tools(enabled_only=True)

        # Build tool descriptions for LLM
        tools_info = []
        for entry in available_tools:
            tools_info.append({
                "name": entry.schema.name,
                "description": entry.schema.description,
                "category": entry.schema.category,
                "use_cases": entry.capability.use_cases,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type.value,
                        "description": p.description,
                        "required": p.required
                    }
                    for p in entry.schema.parameters
                ]
            })

        # Build prompt
        prompt = f"""You are a tool selection expert. Given a task description and available tools,
select the most appropriate tools to accomplish the task.

Task: {task_description}

Context: {json.dumps(context) if context else "None"}

Available Tools:
{json.dumps(tools_info, indent=2)}

Analyze the task and select the appropriate tools. Consider:
1. What capabilities are needed?
2. What is the sequence of operations?
3. Which tools provide those capabilities?

Respond with JSON in this format:
{{
  "selected_tools": ["tool_name1", "tool_name2"],
  "reasoning": "Explanation of why these tools were selected",
  "confidence": 0.95,
  "execution_order": ["tool_name1", "tool_name2"]
}}

Response (JSON only):"""

        try:
            # Call LLM
            response = await self.llm_service.generate(
                prompt,
                response_format="json",
                temperature=0.2,
                max_tokens=500
            )

            # Parse response
            result = json.loads(response)

            # Build tool entries
            selected_tools = []
            for tool_name in result.get("selected_tools", []):
                entry = self.catalog.get_catalog_entry(tool_name)
                if entry:
                    selected_tools.append(entry)

            return ToolDiscoveryResponse(
                tools=selected_tools,
                reasoning=result.get("reasoning", "LLM-based tool selection"),
                confidence=result.get("confidence", 0.5)
            )

        except Exception as e:
            self.logger.error(f"LLM routing failed: {str(e)}")

            # Fallback to fast path
            fallback = self._fast_path_route(task_description, context)
            return fallback or ToolDiscoveryResponse(
                tools=[],
                reasoning=f"Tool routing failed: {str(e)}",
                confidence=0.0
            )

    async def route_multi_step(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ToolDiscoveryResponse]:
        """
        Route a multi-step task to a sequence of tool invocations

        Args:
            task_description: Complex task description
            context: Optional context

        Returns:
            List of ToolDiscoveryResponse (one per step)
        """
        # Use LLM to break down into steps and route each
        available_tools = self.catalog.list_tools(enabled_only=True)

        tools_info = [
            {
                "name": e.schema.name,
                "description": e.schema.description,
                "category": e.schema.category
            }
            for e in available_tools
        ]

        prompt = f"""Break down this task into a sequence of tool invocations:

Task: {task_description}

Available Tools:
{json.dumps(tools_info, indent=2)}

Create a step-by-step execution plan. For each step, specify:
1. What needs to be done
2. Which tool to use
3. Why this tool

Respond with JSON:
{{
  "steps": [
    {{
      "step_number": 1,
      "description": "What to do",
      "tool_name": "tool_name",
      "reasoning": "Why this tool"
    }}
  ]
}}

Response (JSON only):"""

        try:
            response = await self.llm_service.generate(
                prompt,
                response_format="json",
                temperature=0.2,
                max_tokens=800
            )

            result = json.loads(response)
            steps = []

            for step in result.get("steps", []):
                tool_name = step.get("tool_name")
                entry = self.catalog.get_catalog_entry(tool_name)

                if entry:
                    steps.append(ToolDiscoveryResponse(
                        tools=[entry],
                        reasoning=step.get("reasoning", ""),
                        confidence=0.8
                    ))

            return steps

        except Exception as e:
            self.logger.error(f"Multi-step routing failed: {str(e)}")

            # Fallback to single-step routing
            single_result = await self.route(task_description, context)
            return [single_result] if single_result.tools else []

    def get_tools_by_category(self, category: str) -> List[ToolCatalogEntry]:
        """Get all tools in a category"""
        return self.catalog.list_tools(category=category)

    def get_tool_by_name(self, name: str) -> Optional[ToolCatalogEntry]:
        """Get a specific tool by name"""
        return self.catalog.get_catalog_entry(name)


# Global tool router instance
_tool_router: Optional[ToolRouter] = None


def get_tool_router() -> ToolRouter:
    """Get the global tool router instance"""
    global _tool_router
    if _tool_router is None:
        from app.tools.catalog import get_tool_catalog
        _tool_router = ToolRouter(get_tool_catalog())
    return _tool_router


def init_tool_router(catalog: ToolCatalog) -> ToolRouter:
    """Initialize and return a new tool router"""
    global _tool_router
    _tool_router = ToolRouter(catalog)
    return _tool_router
