# Tool System - Agent-Native Architecture

This directory contains the tool system implementation for AI Spreadsheets' agent-native architecture.

## Quick Links

- 📚 [Full Architecture Documentation](../../../docs/AGENT_NATIVE_ARCHITECTURE.md)
- 🚀 [Quick Start Guide](../../../docs/AGENT_NATIVE_QUICKSTART.md)
- 📊 [Implementation Summary](../../../docs/AGENT_NATIVE_IMPLEMENTATION_SUMMARY.md)

## Directory Structure

```
app/tools/
├── __init__.py              # Package exports
├── README.md               # This file
├── base_tool.py            # Base tool interface
├── catalog.py              # Tool registry and discovery
├── tool_router.py          # Intelligent tool routing
├── initialize.py           # System initialization
└── primitives/             # Atomic tool implementations
    ├── __init__.py
    ├── read_dataset.py     # Read dataset metadata
    ├── execute_sql.py      # Execute SQL queries
    ├── calculate_stats.py  # Calculate statistics
    └── generate_chart.py   # Generate visualizations
```

## What Are Tools?

Tools are **atomic primitives** that provide specific capabilities. Unlike agents, tools don't make decisions - they execute capabilities.

### Principles

1. **Single Responsibility**: Each tool does ONE thing well
2. **Clear Contracts**: Explicit input/output schemas
3. **Composable**: Can be used alone or in combination
4. **Discoverable**: Tools describe their capabilities
5. **Safe**: Validation and error handling built-in

## Available Tools

### Data Access
- **read_dataset**: Read dataset metadata, schema, and basic info
- **execute_sql**: Execute SQL queries safely with DuckDB

### Computation
- **calculate_stats**: Calculate statistical metrics (mean, median, std, etc.)

### Visualization
- **generate_chart**: Generate chart specifications (Vega-Lite)

## Usage

### Direct Tool Usage

```python
from app.tools.primitives import ReadDatasetTool
from app.schemas.tool import ToolInvocation

tool = ReadDatasetTool()
result = await tool.invoke(ToolInvocation(
    tool_name="read_dataset",
    parameters={"dataset_id": "123", "include_schema": True},
    invoked_by="user"
))

if result.success:
    print(f"Dataset: {result.data['name']}")
    print(f"Columns: {result.data['column_count']}")
```

### Tool Discovery

```python
from app.tools.catalog import get_tool_catalog
from app.schemas.tool import ToolDiscoveryRequest

catalog = get_tool_catalog()
discovery = catalog.discover_tools(ToolDiscoveryRequest(
    task_description="Calculate average of a numeric column"
))

print(f"Found {len(discovery.tools)} tools")
print(f"Reasoning: {discovery.reasoning}")
```

### Tool Routing

```python
from app.tools.tool_router import get_tool_router

router = get_tool_router()
response = await router.route(
    task_description="Find products with above-average prices",
    context={"dataset_id": "123"}
)

# Use the suggested tool
if response.tools:
    tool = catalog.get_tool(response.tools[0].schema.name)
    result = await tool.invoke(...)
```

## Creating a New Tool

### Step 1: Create Tool Class

```python
# File: primitives/my_tool.py

from app.tools.base_tool import BaseTool
from app.schemas.tool import (
    ToolSchema, ToolParameter, ToolParameterType,
    ToolResult, ToolCapability
)

class MyTool(BaseTool):
    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name="my_tool",
            description="What this tool does",
            category="computation",
            parameters=[
                ToolParameter(
                    name="param1",
                    type=ToolParameterType.STRING,
                    description="What param1 is",
                    required=True
                )
            ],
            returns={"type": "object", "properties": {...}},
            estimated_duration_ms=500
        )

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="My Capability",
            description="What this enables",
            use_cases=["Use case 1", "Use case 2"]
        )

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        # Your implementation
        return ToolResult(
            tool_name="my_tool",
            success=True,
            data={"result": "..."}
        )
```

### Step 2: Register Tool

```python
# File: initialize.py

from app.tools.primitives.my_tool import MyTool

def initialize_tools():
    # ... existing code ...

    catalog.register_tool(
        MyTool(),
        enabled=True,
        access_level="public",
        cost_credits=1
    )
```

### Step 3: Add to Exports

```python
# File: primitives/__init__.py

from app.tools.primitives.my_tool import MyTool

__all__ = [..., "MyTool"]
```

## Tool Categories

Tools are organized by category:

- **data_access**: Reading and querying data
- **computation**: Calculations and transformations
- **visualization**: Charts and visual outputs
- **ml**: Machine learning operations
- **geospatial**: Geographic analysis

## Best Practices

### ✅ Do

- Keep tools atomic and focused
- Validate parameters thoroughly
- Provide clear error messages
- Document use cases and limitations
- Use type hints
- Handle errors gracefully

### ❌ Don't

- Bundle decision logic in tools
- Make tools depend on each other
- Skip parameter validation
- Return unclear error messages
- Mix multiple responsibilities

## Testing Tools

Use the evaluation framework:

```python
from app.evals import EvalHarness, EvalTask

harness = EvalHarness()

task = EvalTask(
    id="test_my_tool",
    name="Test My Tool",
    description="Test that my tool works correctly",
    input={"tool_name": "my_tool", "parameters": {...}},
    expected_output={...},
    grader=lambda output, expected: (output == expected, 1.0)
)

harness.register_task(task)
result = await harness.run_task("test_my_tool", my_tool_function)
```

## Performance Considerations

### Tool Selection Performance

- **Fast Path** (keyword matching): ~5-10ms
- **Slow Path** (LLM routing): ~500-2000ms
- Use fast path when confidence > 0.8

### Tool Execution

- Tools should complete in < 5 seconds
- Use streaming for long operations
- Implement timeouts
- Cache expensive computations

### Optimization Tips

1. **Cache tool schemas** (loaded once)
2. **Reuse connections** (database, HTTP)
3. **Batch operations** when possible
4. **Use async/await** throughout

## Troubleshooting

### Tool Not Found

```python
# Make sure tools are initialized
from app.tools.initialize import initialize_tools
initialize_tools()
```

### Parameter Validation Errors

```python
# Check parameter types match schema
tool = MyTool()
schema = tool.get_schema()
print(f"Required params: {[p.name for p in schema.parameters if p.required]}")
```

### Low Confidence Scores

```python
# Override can_handle_task for better matching
class MyTool(BaseTool):
    def can_handle_task(self, task_description: str) -> float:
        # Custom matching logic
        if "my specific keyword" in task_description.lower():
            return 0.9
        return 0.0
```

## Integration with Agent Loop

Tools are designed to work seamlessly with the agent loop:

```python
from app.services.agents.agent_loop import AgentLoop

loop = AgentLoop(llm_service, tool_router, tool_catalog)

# The loop will:
# 1. Discover appropriate tools based on goal
# 2. Invoke tools with proper parameters
# 3. Handle tool results
# 4. Compose multiple tools as needed

result = await loop.run(
    session_id="123",
    agent_name="analyst",
    goal="Calculate average sales and create chart",
    context={"dataset_id": "456"}
)
```

## Security Considerations

### Tool Access Control

```python
catalog.register_tool(
    SensitiveTool(),
    enabled=True,
    access_level="admin",  # Restrict access
    requires_approval=True  # Require approval
)
```

### Parameter Sanitization

```python
# Tools validate all parameters
# SQL injection prevention
if "DROP" in sql.upper() or "DELETE" in sql.upper():
    return ToolResult(success=False, error="Forbidden operation")
```

### Rate Limiting

```python
catalog.register_tool(
    ExpensiveTool(),
    rate_limit_per_minute=10  # Limit invocations
)
```

## Monitoring

Tools automatically track:
- Execution time
- Success/failure rates
- Error messages
- Invocation counts

Access via tool metadata:

```python
result = await tool.invoke(invocation)
print(f"Execution time: {result.execution_time_ms}ms")
print(f"Success: {result.success}")
```

## Future Enhancements

Planned features:
- [ ] Tool learning (track which tools work best)
- [ ] Tool composition patterns
- [ ] Tool marketplace
- [ ] Advanced caching
- [ ] Tool metrics dashboard

## Support

For questions or issues:
1. Check the [architecture documentation](../../../docs/AGENT_NATIVE_ARCHITECTURE.md)
2. Review [example tools](./primitives/)
3. See [evaluation tests](../evals/test_suites/tool_evals.py)

## License

Part of AI Spreadsheets - see main project LICENSE
