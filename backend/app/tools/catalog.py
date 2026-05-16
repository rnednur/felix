"""
Tool Catalog - registry and discovery system for tools
"""
from typing import Dict, List, Optional, Tuple
from app.tools.base_tool import BaseTool
from app.schemas.tool import (
    ToolCatalogEntry,
    ToolDiscoveryRequest,
    ToolDiscoveryResponse,
    ToolSchema
)
import logging


class ToolCatalog:
    """
    Central registry for tool discovery and management

    The catalog maintains all available tools and provides:
    - Tool registration
    - Dynamic tool discovery based on task descriptions
    - Access control and rate limiting
    - Tool metadata and capabilities
    """

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.catalog_entries: Dict[str, ToolCatalogEntry] = {}
        self.logger = logging.getLogger("tool.catalog")

    def register_tool(
        self,
        tool: BaseTool,
        enabled: bool = True,
        access_level: str = "public",
        rate_limit_per_minute: Optional[int] = None,
        cost_credits: int = 1
    ):
        """
        Register a tool in the catalog

        Args:
            tool: Tool instance to register
            enabled: Whether the tool is enabled
            access_level: Access level (public, premium, admin)
            rate_limit_per_minute: Rate limit per minute
            cost_credits: Cost in credits per invocation
        """
        schema = tool.get_schema()
        capability = tool.get_capability()

        entry = ToolCatalogEntry(
            schema=schema,
            capability=capability,
            enabled=enabled,
            access_level=access_level,
            rate_limit_per_minute=rate_limit_per_minute,
            cost_credits=cost_credits
        )

        self.tools[schema.name] = tool
        self.catalog_entries[schema.name] = entry

        self.logger.info(f"Registered tool: {schema.name}")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self.tools.get(name)

    def get_catalog_entry(self, name: str) -> Optional[ToolCatalogEntry]:
        """
        Get catalog entry for a tool

        Args:
            name: Tool name

        Returns:
            ToolCatalogEntry or None
        """
        return self.catalog_entries.get(name)

    def list_tools(
        self,
        category: Optional[str] = None,
        enabled_only: bool = True,
        access_level: Optional[str] = None
    ) -> List[ToolCatalogEntry]:
        """
        List tools with optional filtering

        Args:
            category: Filter by category
            enabled_only: Only return enabled tools
            access_level: Filter by access level

        Returns:
            List of catalog entries
        """
        entries = list(self.catalog_entries.values())

        # Filter by enabled status
        if enabled_only:
            entries = [e for e in entries if e.enabled]

        # Filter by category
        if category:
            entries = [e for e in entries if e.schema.category == category]

        # Filter by access level
        if access_level:
            entries = [e for e in entries if e.access_level == access_level]

        return entries

    def discover_tools(self, request: ToolDiscoveryRequest) -> ToolDiscoveryResponse:
        """
        Discover tools that can handle a task

        Uses keyword matching and capability descriptions to find suitable tools.

        Args:
            request: Discovery request with task description

        Returns:
            ToolDiscoveryResponse with ranked tools
        """
        candidates: List[Tuple[ToolCatalogEntry, float]] = []

        # Get enabled tools
        enabled_entries = [e for e in self.catalog_entries.values() if e.enabled]

        # Score each tool
        for entry in enabled_entries:
            tool = self.tools[entry.schema.name]
            confidence = tool.can_handle_task(request.task_description)

            # Boost confidence if required capabilities match
            if request.required_capabilities:
                capability_matches = sum(
                    1 for cap in request.required_capabilities
                    if cap in entry.capability.use_cases
                )
                if capability_matches > 0:
                    confidence = min(1.0, confidence + (capability_matches * 0.2))

            if confidence > 0.3:  # Threshold for inclusion
                candidates.append((entry, confidence))

        # Sort by confidence descending
        candidates.sort(key=lambda x: x[1], reverse=True)

        # Build response
        tools = [entry for entry, _ in candidates]
        overall_confidence = candidates[0][1] if candidates else 0.0

        reasoning = self._generate_reasoning(request, candidates)

        return ToolDiscoveryResponse(
            tools=tools,
            reasoning=reasoning,
            confidence=overall_confidence
        )

    def _generate_reasoning(
        self,
        request: ToolDiscoveryRequest,
        candidates: List[Tuple[ToolCatalogEntry, float]]
    ) -> str:
        """Generate reasoning for tool selection"""
        if not candidates:
            return "No suitable tools found for this task."

        top_tools = candidates[:3]
        tool_names = [entry.schema.name for entry, _ in top_tools]

        reasoning = f"Found {len(candidates)} potential tools. "
        reasoning += f"Top candidates: {', '.join(tool_names)}. "

        if request.required_capabilities:
            reasoning += f"Required capabilities: {', '.join(request.required_capabilities)}."

        return reasoning

    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """
        Get all tools in a category

        Args:
            category: Category name

        Returns:
            List of tools
        """
        return [
            self.tools[entry.schema.name]
            for entry in self.catalog_entries.values()
            if entry.schema.category == category and entry.enabled
        ]

    def get_tool_count(self) -> int:
        """Get total number of registered tools"""
        return len(self.tools)

    def get_enabled_count(self) -> int:
        """Get number of enabled tools"""
        return sum(1 for entry in self.catalog_entries.values() if entry.enabled)

    def get_categories(self) -> List[str]:
        """Get list of all tool categories"""
        return list(set(
            entry.schema.category
            for entry in self.catalog_entries.values()
        ))

    def enable_tool(self, name: str):
        """Enable a tool"""
        if name in self.catalog_entries:
            self.catalog_entries[name].enabled = True
            self.logger.info(f"Enabled tool: {name}")

    def disable_tool(self, name: str):
        """Disable a tool"""
        if name in self.catalog_entries:
            self.catalog_entries[name].enabled = False
            self.logger.info(f"Disabled tool: {name}")


# Global tool catalog instance
_tool_catalog: Optional[ToolCatalog] = None


def get_tool_catalog() -> ToolCatalog:
    """Get the global tool catalog instance"""
    global _tool_catalog
    if _tool_catalog is None:
        _tool_catalog = ToolCatalog()
    return _tool_catalog


def init_tool_catalog() -> ToolCatalog:
    """Initialize and return a new tool catalog"""
    global _tool_catalog
    _tool_catalog = ToolCatalog()
    return _tool_catalog
