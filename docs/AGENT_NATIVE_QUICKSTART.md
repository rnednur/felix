# Agent-Native Architecture - Quick Start Guide

Get started with the new agent-native architecture in 5 minutes.

## What Changed?

### Before (Monolithic Agents)
```
User Query → Agent (black box) → Result
```
- Agents contained all logic
- No visibility into reasoning
- Hard to test
- Limited composability

### After (Agent-Native)
```
User Query → Agent Loop:
  1. Observe (what do I see?)
  2. Think (what should I do?)
  3. Act (use tools to accomplish task)
  4. Reflect (did it work?)
→ Transparent, testable, composable
```

## Key Concepts

### 1. Tools = Atomic Primitives
Tools do ONE thing well:
- `read_dataset` - Read dataset info
- `execute_sql` - Run SQL queries
- `calculate_stats` - Compute statistics
- `generate_chart` - Create visualizations

### 2. Agent Loop = Explicit Reasoning
The loop makes agent thinking transparent:
- You can see what the agent is thinking
- You can see what tools it's using
- You can see why it made decisions
- You can intervene if needed

### 3. Evals = Systematic Testing
Test your agents like you test code:
- Define expected behavior
- Run automated tests
- Measure success rates
- Track regressions

## Quick Start: Use Tools Directly

### Example 1: Read Dataset

```python
from app.tools.primitives import ReadDatasetTool
from app.schemas.tool import ToolInvocation

tool = ReadDatasetTool()
result = await tool.invoke(ToolInvocation(
    tool_name="read_dataset",
    parameters={
        "dataset_id": "your-dataset-id",
        "include_schema": True
    },
    invoked_by="user"
))

if result.success:
    print(f"Dataset: {result.data['name']}")
    print(f"Columns: {result.data['column_count']}")
    print(f"Schema: {result.data['schema']}")
else:
    print(f"Error: {result.error}")
```

### Example 2: Execute SQL Query

```python
from app.tools.primitives import ExecuteSQLTool

tool = ExecuteSQLTool()
result = await tool.invoke(ToolInvocation(
    tool_name="execute_sql",
    parameters={
        "dataset_id": "your-dataset-id",
        "sql": "SELECT category, AVG(price) FROM dataset GROUP BY category",
        "limit": 100
    },
    invoked_by="user"
))

if result.success:
    print(f"Columns: {result.data['columns']}")
    print(f"Rows: {result.data['rows']}")
    print(f"Count: {result.data['row_count']}")
```

### Example 3: Calculate Statistics

```python
from app.tools.primitives import CalculateStatsTool

tool = CalculateStatsTool()
result = await tool.invoke(ToolInvocation(
    tool_name="calculate_stats",
    parameters={
        "dataset_id": "your-dataset-id",
        "columns": ["price", "quantity"],
        "metrics": ["mean", "median", "std", "min", "max"]
    },
    invoked_by="user"
))

if result.success:
    stats = result.data['statistics']
    print(f"Price - Mean: {stats['price']['mean']}")
    print(f"Price - Std: {stats['price']['std']}")
```

## Quick Start: Use Agent Loop

### Basic Usage

```python
from app.services.agents.agent_loop import AgentLoop
from app.services.agents.llm_service import LLMService
from app.tools.initialize import get_initialized_catalog
from app.tools.tool_router import get_tool_router

# Initialize
catalog = get_initialized_catalog()
router = get_tool_router()
llm = LLMService()

# Create loop
loop = AgentLoop(
    llm_service=llm,
    tool_router=router,
    tool_catalog=catalog
)

# Run
result = await loop.run(
    session_id="session-123",
    agent_name="analyst",
    goal="Find products with above-average prices",
    context={"dataset_id": "your-dataset-id"}
)

# Check results
print(f"Status: {result.status}")
print(f"Iterations: {result.current_iteration}")

for iteration in result.iterations:
    print(f"\nIteration {iteration.iteration_number}:")
    print(f"  Thought: {iteration.thought.reasoning}")
    print(f"  Action: {iteration.action.rationale}")
    print(f"  Result: {iteration.reflection.learned}")
```

### Streaming Usage

```python
# Stream progress in real-time
async for chunk in loop.run_streaming(
    session_id="session-123",
    agent_name="analyst",
    goal="Calculate average sales by region and create a chart",
    context={"dataset_id": "your-dataset-id"}
):
    print(f"Event: {chunk.type}")

    if chunk.type == "thought":
        print(f"  Agent thinking: {chunk.data['reasoning']}")

    elif chunk.type == "action_proposed":
        print(f"  Agent wants to: {chunk.data['rationale']}")
        print(f"  Using tool: {chunk.data['tool_name']}")

    elif chunk.type == "action_result":
        print(f"  Result: {chunk.data['result']}")

    elif chunk.type == "reflection":
        print(f"  Agent learned: {chunk.data['learned']}")
        print(f"  Continue? {chunk.data['should_continue']}")
```

## Quick Start: Create Evaluations

### Define a Test

```python
from app.evals import EvalHarness, EvalTask

# Create harness
harness = EvalHarness()

# Define a task
task = EvalTask(
    id="test_average_calculation",
    name="Calculate Average",
    description="Test that agent can calculate average correctly",
    input={
        "query": "What is the average price?",
        "dataset_id": "test_dataset"
    },
    expected_output={"average": 99.5},
    grader=lambda output, expected: (
        abs(output.get("average", 0) - expected["average"]) < 0.1,
        1.0 if abs(output.get("average", 0) - expected["average"]) < 0.1 else 0.0
    ),
    category="computation",
    difficulty="easy"
)

# Register task
harness.register_task(task)
```

### Run Evaluation

```python
# Define your agent function
async def my_agent(input_data, context):
    # Your agent implementation
    return {"average": 99.52, "success": True}

# Run single test
result = await harness.run_task(
    task_id="test_average_calculation",
    agent_fn=my_agent
)

print(f"Success: {result.success}")
print(f"Score: {result.score}")
print(f"Time: {result.execution_time_ms}ms")
```

### Run Test Suite (pass@k)

```python
# Run 3 times to get pass@3 metric
results = await harness.run_task_multiple_times(
    task_id="test_average_calculation",
    agent_fn=my_agent,
    k=3
)

pass_at_3 = harness.calculate_pass_at_k(results)
pass_power_3 = harness.calculate_pass_power_k(results)

print(f"pass@3: {pass_at_3}")  # At least one success
print(f"pass^3: {pass_power_3}")  # All successes
```

## Quick Start: Create a New Tool

### 1. Create Tool Class

```python
# File: app/tools/primitives/my_tool.py

from typing import Dict, Any
from app.tools.base_tool import BaseTool
from app.schemas.tool import (
    ToolSchema,
    ToolParameter,
    ToolParameterType,
    ToolResult,
    ToolCapability
)

class MyTool(BaseTool):
    """My custom tool description"""

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name="my_tool",
            description="What this tool does",
            category="computation",  # or data_access, visualization, ml
            parameters=[
                ToolParameter(
                    name="param1",
                    type=ToolParameterType.STRING,
                    description="What param1 is",
                    required=True
                ),
                ToolParameter(
                    name="param2",
                    type=ToolParameterType.INTEGER,
                    description="What param2 is",
                    required=False,
                    default=10
                )
            ],
            returns={
                "type": "object",
                "properties": {
                    "result": {"type": "string"}
                }
            },
            requires_approval=False,
            is_destructive=False,
            estimated_duration_ms=500
        )

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="My Capability",
            description="What this tool enables",
            use_cases=[
                "Use case 1",
                "Use case 2"
            ],
            limitations=[
                "Limitation 1"
            ]
        )

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute the tool"""
        param1 = parameters["param1"]
        param2 = parameters.get("param2", 10)

        try:
            # Your tool logic here
            result = f"Processed {param1} with {param2}"

            return ToolResult(
                tool_name="my_tool",
                success=True,
                data={"result": result},
                metadata={"param1": param1, "param2": param2}
            )

        except Exception as e:
            return ToolResult(
                tool_name="my_tool",
                success=False,
                data={},
                error=str(e)
            )
```

### 2. Register Tool

```python
# File: app/tools/initialize.py

from app.tools.primitives.my_tool import MyTool

def initialize_tools():
    # ... existing code ...

    # Register your tool
    catalog.register_tool(
        MyTool(),
        enabled=True,
        access_level="public",
        rate_limit_per_minute=60,
        cost_credits=1
    )
```

### 3. Use Tool

```python
from app.tools.primitives.my_tool import MyTool

tool = MyTool()
result = await tool.invoke(ToolInvocation(
    tool_name="my_tool",
    parameters={"param1": "test", "param2": 20},
    invoked_by="user"
))
```

## Common Patterns

### Pattern 1: Sequential Tool Usage

```python
# Read schema, then query, then visualize
async def sequential_analysis(dataset_id: str):
    # Step 1: Read schema
    schema_result = await read_dataset_tool.invoke(...)

    # Step 2: Query based on schema
    query_result = await execute_sql_tool.invoke(...)

    # Step 3: Visualize results
    chart_result = await generate_chart_tool.invoke(...)

    return chart_result
```

### Pattern 2: Parallel Tool Usage

```python
# Calculate multiple statistics in parallel
async def parallel_stats(dataset_id: str):
    results = await asyncio.gather(
        calculate_stats_tool.invoke(...),  # Mean/median
        calculate_stats_tool.invoke(...),  # Min/max
        calculate_stats_tool.invoke(...)   # Quartiles
    )
    return results
```

### Pattern 3: Tool Discovery

```python
# Let the router find the right tool
from app.tools.tool_router import get_tool_router

router = get_tool_router()
discovery = await router.route(
    task_description="Calculate correlation between price and sales",
    context={"dataset_id": dataset_id}
)

# Use discovered tool
if discovery.tools:
    tool = catalog.get_tool(discovery.tools[0].schema.name)
    result = await tool.invoke(...)
```

## Troubleshooting

### Tool Not Found

```python
from app.tools.initialize import initialize_tools

# Make sure tools are initialized
initialize_tools()
```

### Agent Loop Not Converging

```python
# Increase max iterations
from app.schemas.loop import LoopConfig

config = LoopConfig(
    max_iterations=15,  # Default is 10
    verbose_reasoning=True
)

loop = AgentLoop(llm, router, catalog, config=config)
```

### Eval Task Failing

```python
# Add more detailed grader
def detailed_grader(output, expected):
    print(f"Output: {output}")
    print(f"Expected: {expected}")

    success = output == expected
    score = 1.0 if success else 0.0

    return success, score
```

## Next Steps

1. **Read Full Documentation**: See `AGENT_NATIVE_ARCHITECTURE.md`
2. **Explore Examples**: Check `app/tools/primitives/` for tool examples
3. **Run Evals**: See `app/evals/test_suites/` for test examples
4. **Create Custom Tools**: Follow the pattern in primitives
5. **Build Agents**: Use `AgentLoop` to compose tools

## Resources

- Architecture Doc: `docs/AGENT_NATIVE_ARCHITECTURE.md`
- Tool Primitives: `backend/app/tools/primitives/`
- Agent Loop: `backend/app/services/agents/agent_loop.py`
- Eval Framework: `backend/app/evals/`
- Test Suites: `backend/app/evals/test_suites/`

## Support

For questions:
1. Check the architecture documentation
2. Look at example tools and tests
3. Review the agent loop implementation
