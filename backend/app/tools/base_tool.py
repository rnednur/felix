"""
Base Tool class - all tools inherit from this
Tools are atomic primitives that provide specific capabilities
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from app.schemas.tool import (
    ToolSchema,
    ToolResult,
    ToolCapability,
    ToolInvocation
)


class BaseTool(ABC):
    """
    Base class for all tools in the agent-native system

    Tools are atomic primitives that:
    - Have clear input/output schemas
    - Do one thing well
    - Are composable
    - Can be discovered dynamically
    - Have clear error handling

    Unlike agents, tools don't make decisions - they execute capabilities.
    """

    def __init__(self):
        self.logger = logging.getLogger(f"tool.{self.get_schema().name}")

    @abstractmethod
    def get_schema(self) -> ToolSchema:
        """
        Return the tool's schema definition

        This defines the tool's interface: name, parameters, return type, etc.
        """
        pass

    @abstractmethod
    def get_capability(self) -> ToolCapability:
        """
        Describe what this tool can do

        This is used for tool discovery and selection.
        """
        pass

    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool with given parameters

        Args:
            parameters: Tool parameters matching the schema

        Returns:
            ToolResult with execution outcome
        """
        pass

    async def invoke(self, invocation: ToolInvocation) -> ToolResult:
        """
        Invoke the tool (wrapper around execute with validation and logging)

        Args:
            invocation: Tool invocation details

        Returns:
            ToolResult
        """
        start_time = datetime.utcnow()

        try:
            self.logger.info(
                f"Invoking tool: {invocation.tool_name}",
                extra={
                    "parameters": invocation.parameters,
                    "invoked_by": invocation.invoked_by
                }
            )

            # Validate parameters against schema
            self._validate_parameters(invocation.parameters)

            # Execute tool
            result = await self.execute(invocation.parameters)

            # Calculate execution time
            end_time = datetime.utcnow()
            result.execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

            self.logger.info(
                f"Tool executed successfully: {invocation.tool_name}",
                extra={
                    "success": result.success,
                    "execution_time_ms": result.execution_time_ms
                }
            )

            return result

        except Exception as e:
            self.logger.error(
                f"Tool execution failed: {invocation.tool_name}",
                exc_info=True
            )

            end_time = datetime.utcnow()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

            return ToolResult(
                tool_name=invocation.tool_name,
                success=False,
                data={},
                error=str(e),
                execution_time_ms=execution_time_ms
            )

    def _validate_parameters(self, parameters: Dict[str, Any]):
        """
        Validate parameters against the tool schema

        Args:
            parameters: Parameters to validate

        Raises:
            ValueError: If validation fails
        """
        schema = self.get_schema()

        # Check required parameters
        for param in schema.parameters:
            if param.required and param.name not in parameters:
                raise ValueError(f"Missing required parameter: {param.name}")

        # Check parameter types
        for param_name, param_value in parameters.items():
            # Find parameter definition
            param_def = next(
                (p for p in schema.parameters if p.name == param_name),
                None
            )

            if not param_def:
                self.logger.warning(f"Unknown parameter: {param_name}")
                continue

            # Basic type checking
            self._validate_parameter_type(param_name, param_value, param_def)

    def _validate_parameter_type(self, name: str, value: Any, param_def):
        """Validate a single parameter type"""
        from app.schemas.tool import ToolParameterType

        # Type checking
        if param_def.type == ToolParameterType.STRING and not isinstance(value, str):
            raise ValueError(f"Parameter {name} must be a string")
        elif param_def.type == ToolParameterType.INTEGER and not isinstance(value, int):
            raise ValueError(f"Parameter {name} must be an integer")
        elif param_def.type == ToolParameterType.FLOAT and not isinstance(value, (int, float)):
            raise ValueError(f"Parameter {name} must be a number")
        elif param_def.type == ToolParameterType.BOOLEAN and not isinstance(value, bool):
            raise ValueError(f"Parameter {name} must be a boolean")
        elif param_def.type == ToolParameterType.ARRAY and not isinstance(value, list):
            raise ValueError(f"Parameter {name} must be an array")
        elif param_def.type == ToolParameterType.OBJECT and not isinstance(value, dict):
            raise ValueError(f"Parameter {name} must be an object")

        # Range checking for numbers
        if param_def.type in [ToolParameterType.INTEGER, ToolParameterType.FLOAT]:
            if param_def.min_value is not None and value < param_def.min_value:
                raise ValueError(f"Parameter {name} must be >= {param_def.min_value}")
            if param_def.max_value is not None and value > param_def.max_value:
                raise ValueError(f"Parameter {name} must be <= {param_def.max_value}")

        # Enum checking
        if param_def.enum and value not in param_def.enum:
            raise ValueError(f"Parameter {name} must be one of: {param_def.enum}")

    def can_handle_task(self, task_description: str) -> float:
        """
        Return confidence (0-1) that this tool can handle the task

        Args:
            task_description: Natural language description of task

        Returns:
            Confidence score (0.0 = cannot handle, 1.0 = perfect match)
        """
        # Simple keyword matching (can be overridden for more sophisticated matching)
        task_lower = task_description.lower()
        capability = self.get_capability()

        # Check if any use case matches
        matches = sum(1 for use_case in capability.use_cases
                     if use_case.lower() in task_lower or task_lower in use_case.lower())

        if matches == 0:
            return 0.0

        return min(1.0, matches * 0.3)
