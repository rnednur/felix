# Agent-Native Architecture

This document describes the agent-native architecture implemented in AI Spreadsheets, following best practices from industry leaders (Anthropic, Every.to, Composio).

## Overview

The agent-native architecture transforms AI Spreadsheets from a traditional "agentic workflow" system into a truly composable, transparent, and evaluable agent platform.

### Key Principles

1. **Parity**: Agents can do anything users can do
2. **Granularity**: Tools are atomic primitives, not features
3. **Composability**: New capabilities emerge from tool composition
4. **Transparency**: Agent reasoning is explicit and observable
5. **Evaluability**: Systematic testing with measurable metrics

## Architecture Components

### 1. Tool System (`app/tools/`)

The foundation of the agent-native approach.

#### Base Tool (`base_tool.py`)

All tools inherit from `BaseTool`:
- Define clear input/output schemas
- Provide capability descriptions
- Handle parameter validation
- Support confidence scoring

```python
from app.tools.base_tool import BaseTool
from app.schemas.tool import ToolSchema, ToolCapability, ToolResult

class MyTool(BaseTool):
    def get_schema(self) -> ToolSchema:
        # Define tool interface
        pass

    def get_capability(self) -> ToolCapability:
        # Describe what the tool can do
        pass

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        # Execute the tool
        pass
```

#### Tool Catalog (`catalog.py`)

Central registry for tool discovery:
- Register tools with metadata
- Discover tools by task description
- Filter by category, access level
- Enable/disable tools dynamically

```python
from app.tools.catalog import get_tool_catalog

catalog = get_tool_catalog()
catalog.register_tool(my_tool, enabled=True, access_level="public")

# Discover tools for a task
discovery = catalog.discover_tools(ToolDiscoveryRequest(
    task_description="Calculate statistics for sales data"
))
```

#### Tool Router (`tool_router.py`)

Intelligent tool selection:
- Fast path: Keyword-based matching
- Slow path: LLM-based reasoning
- Multi-step task breakdown
- Context-aware routing

```python
from app.tools.tool_router import get_tool_router

router = get_tool_router()
response = await router.route(
    task_description="Find average sales by region",
    context={"dataset_id": "123"}
)
```

### 2. Atomic Tool Primitives (`app/tools/primitives/`)

The building blocks that agents compose:

#### Data Access Tools
- **ReadDatasetTool**: Read dataset metadata and schema
- **ExecuteSQLTool**: Execute SQL queries safely

#### Computation Tools
- **CalculateStatsTool**: Statistical calculations (mean, median, std, etc.)

#### Visualization Tools
- **GenerateChartTool**: Create chart specifications (Vega-Lite)

Each tool:
- Does ONE thing well
- Has clear input/output contracts
- Is fully composable
- Can be used independently or in sequences

### 3. Agent Loop (`app/services/agents/agent_loop.py`)

Explicit reasoning cycle: **Observe → Think → Act → Reflect**

#### Loop Structure

```
┌─────────────┐
│  OBSERVE    │  What's the current state?
└──────┬──────┘
       │
┌──────▼──────┐
│   THINK     │  What should I do next?
└──────┬──────┘
       │
┌──────▼──────┐
│    ACT      │  Execute the action
└──────┬──────┘
       │
┌──────▼──────┐
│  REFLECT    │  Did it work? What did I learn?
└──────┬──────┘
       │
       └──────┐ Continue?
              │ Yes ──► (loop back to OBSERVE)
              │ No  ──► Complete
```

#### Loop State

The `LoopState` tracks:
- Goal and current status
- All iterations with full history
- Observations, thoughts, actions, reflections
- Metadata and context

#### Streaming Support

The loop can stream progress in real-time:
- `loop_start`: Loop begins
- `iteration_start`: New iteration begins
- `observation`: What the agent sees
- `thought`: Agent's reasoning
- `action_proposed`: What the agent plans to do
- `action_executing`: Action in progress
- `action_result`: Action completed
- `reflection`: Agent's learning
- `loop_complete`: Goal achieved

```python
from app.services.agents.agent_loop import AgentLoop

loop = AgentLoop(llm_service, tool_router, tool_catalog)

async for chunk in loop.run_streaming(
    session_id="123",
    agent_name="query_agent",
    goal="Find the top 10 products by sales",
    context={"dataset_id": "456"}
):
    print(f"Event: {chunk.type}, Data: {chunk.data}")
```

### 4. Evaluation Framework (`app/evals/`)

Systematic testing based on Anthropic's best practices.

#### Eval Harness (`harness.py`)

Features:
- **pass@k**: Probability of success in k attempts
- **pass^k**: Probability of consistent success across k attempts
- Task registration and management
- Automatic grading
- Performance metrics

#### Creating Eval Tasks

```python
from app.evals import EvalHarness, EvalTask

harness = EvalHarness()

task = EvalTask(
    id="query_average",
    name="Calculate Average",
    description="Calculate average of a numeric column",
    input={
        "query": "What's the average price?",
        "dataset_id": "123"
    },
    expected_output={"average": 99.5},
    grader=threshold_grader(0.01),  # Allow 0.01 tolerance
    category="computation",
    difficulty="easy"
)

harness.register_task(task)
```

#### Running Evaluations

```python
# Run single task
result = await harness.run_task(
    task_id="query_average",
    agent_fn=my_agent_function
)

# Run with k attempts for pass@k
results = await harness.run_task_multiple_times(
    task_id="query_average",
    agent_fn=my_agent_function,
    k=3
)

# Run full eval suite
report = await harness.run_eval_suite(
    agent_fn=my_agent_function,
    task_ids=["query_average", "filter_data", "generate_chart"],
    k=3
)

print(f"Overall pass@3: {report['summary']['overall_pass_at_k']}")
print(f"Overall pass^3: {report['summary']['overall_pass_power_k']}")
```

## Usage Examples

### Example 1: Using Tools Directly

```python
from app.tools.primitives import ReadDatasetTool, ExecuteSQLTool
from app.schemas.tool import ToolInvocation

# Read dataset schema
read_tool = ReadDatasetTool()
result = await read_tool.invoke(ToolInvocation(
    tool_name="read_dataset",
    parameters={"dataset_id": "123", "include_schema": True},
    invoked_by="user"
))

print(f"Dataset has {result.data['column_count']} columns")

# Execute SQL query
sql_tool = ExecuteSQLTool()
result = await sql_tool.invoke(ToolInvocation(
    tool_name="execute_sql",
    parameters={
        "dataset_id": "123",
        "sql": "SELECT category, AVG(price) FROM dataset GROUP BY category"
    },
    invoked_by="user"
))

print(f"Query returned {result.data['row_count']} rows")
```

### Example 2: Agent Loop with Tool Composition

```python
from app.services.agents.agent_loop import AgentLoop
from app.tools.initialize import get_initialized_catalog
from app.tools.tool_router import get_tool_router
from app.services.agents.llm_service import LLMService

# Initialize
catalog = get_initialized_catalog()
router = get_tool_router()
llm = LLMService()

# Create loop
loop = AgentLoop(llm, router, catalog)

# Run with streaming
async for event in loop.run_streaming(
    session_id="abc123",
    agent_name="analyst",
    goal="Find products with above-average prices and create a bar chart",
    context={"dataset_id": "dataset_123"}
):
    if event.type == "thought":
        print(f"Agent thinking: {event.data['reasoning']}")
    elif event.type == "action_proposed":
        print(f"Agent wants to: {event.data['rationale']}")
    elif event.type == "action_result":
        print(f"Result: {event.data['result']}")
```

### Example 3: Tool Discovery

```python
from app.tools.tool_router import get_tool_router

router = get_tool_router()

# Discover tools for a complex task
response = await router.route(
    task_description="Calculate correlation between price and quantity, then visualize",
    context={"dataset_id": "123"}
)

print(f"Suggested tools: {[t.schema.name for t in response.tools]}")
print(f"Reasoning: {response.reasoning}")
print(f"Confidence: {response.confidence}")
```

## Integration with Existing System

### Backward Compatibility

The new tool-based system coexists with existing agents:

1. **Existing agents** continue to work as-is
2. **New agents** can be built using tools and the agent loop
3. **Gradual migration** path from monolithic to tool-based agents

### Migration Strategy

To migrate an existing agent to use tools:

1. Identify the agent's capabilities
2. Break them into atomic tool primitives
3. Implement each primitive as a `BaseTool`
4. Register tools in the catalog
5. Refactor agent to use tools via the loop

Example:

**Before (Monolithic Agent):**
```python
class QueryAgent(BaseAgent):
    async def process(self, request, context):
        # All logic in one place
        schema = self.get_schema(request.dataset_id)
        sql = self.generate_sql(request.query, schema)
        result = self.execute_sql(sql)
        return result
```

**After (Tool-Based Agent):**
```python
class QueryAgent(BaseAgent):
    async def process(self, request, context):
        # Use agent loop to compose tools
        loop = AgentLoop(self.llm, self.router, self.catalog)

        result = await loop.run(
            session_id=context.session_id,
            agent_name=self.config.name,
            goal=request.query,
            context={"dataset_id": request.dataset_id}
        )

        return result
```

## Best Practices

### Tool Design

1. **Single Responsibility**: Each tool does ONE thing
2. **Clear Contracts**: Explicit input/output schemas
3. **Composable**: Can be used alone or in combination
4. **Idempotent**: Same input → same output
5. **Safe**: No side effects unless explicitly documented

### Agent Loop Usage

1. **Set Clear Goals**: Define what success looks like
2. **Limit Iterations**: Prevent infinite loops (default: 10)
3. **Enable Streaming**: For transparency and UX
4. **Save Checkpoints**: Support pause/resume
5. **Log Everything**: For debugging and improvement

### Evaluation

1. **Start Early**: Create evals during development
2. **Cover Edge Cases**: Test positive and negative scenarios
3. **Track Metrics**: Monitor pass@k, latency, cost
4. **Automate**: Run evals in CI/CD
5. **Learn from Failures**: Convert failures to test cases

## Performance Considerations

### Tool Selection

- **Fast Path**: Keyword matching (< 10ms)
- **Slow Path**: LLM routing (500-2000ms)
- Use fast path when confidence > 0.8

### Caching

- Cache tool schemas and capabilities
- Cache LLM responses for identical queries
- Cache dataset metadata

### Parallelization

- Tools can be executed in parallel when independent
- Use `asyncio.gather()` for concurrent tool calls
- Agent loop iterations are sequential

## Monitoring and Observability

### Metrics to Track

1. **Success Rates**
   - Overall pass@k across eval suite
   - Per-category success rates
   - Regression detection

2. **Performance**
   - Average loop iterations per goal
   - Tool execution times
   - LLM latency

3. **Costs**
   - Token usage per request
   - Tool invocation costs
   - Total cost per session

4. **User Experience**
   - Time to first result
   - Transparency of reasoning
   - User approval rates

## Future Enhancements

### Planned Features

1. **Tool Marketplace**: User-contributed tools
2. **Tool Learning**: Agents learn which tools work best
3. **Multi-Agent Collaboration**: Agents use each other as tools
4. **Human-in-the-Loop**: Interactive approval flows
5. **Advanced Evals**: Model-based graders, A/B testing

### Extension Points

- Custom tool categories
- Domain-specific tool libraries
- Alternative loop architectures
- Custom graders for evaluations

## References

- [Agent-Native Principles (Every.to)](https://every.to/guides/agent-native)
- [Composio Data Analyst Agent](https://github.com/composiohq/data-analyst-agent)
- [Anthropic's Evals Guide](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

## Getting Started

1. **Initialize the Tool System**
   ```python
   from app.tools.initialize import initialize_tools
   initialize_tools()
   ```

2. **Create Your First Tool**
   - Copy a primitive as a template
   - Implement the three required methods
   - Register in `initialize.py`

3. **Test with Evals**
   - Create eval tasks for your tool
   - Run `harness.run_task()`
   - Iterate based on results

4. **Integrate with Agent**
   - Use `AgentLoop` to compose tools
   - Enable streaming for transparency
   - Monitor metrics

## Support

For questions or issues:
- Check examples in `app/tools/primitives/`
- Review eval examples in `app/evals/`
- See API integration in `app/api/endpoints/agents.py`
