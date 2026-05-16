# Skills System Documentation

## Overview

The Skills System is an implementation of Anthropic's skills framework that enhances agent capabilities through instruction-based expertise. Skills are modular, reusable instruction sets that agents can dynamically discover and apply to improve their performance on specific tasks.

## What Are Skills?

**Skills** are structured documents (SKILL.md files) that contain:
- **Instructions**: Step-by-step guidance for specific tasks
- **Examples**: Code examples with explanations
- **Best Practices**: Proven approaches and patterns
- **Warnings**: Common pitfalls to avoid

Skills are **not** tools or functions—they are **knowledge** that gets injected into the LLM's context to enhance its capabilities.

## Architecture

### Components

```
Skills System
├── Skill Files (*.md)          # YAML frontmatter + markdown content
├── SkillLoader                 # Parses SKILL.md files
├── SkillCatalog                # Registry and discovery
├── SkillContextBuilder         # Formats for LLM injection
├── SkillTool                   # Agent loop integration
└── Skills API                  # REST endpoints for management
```

### Data Flow

```
1. Startup → Load SKILL.md files → Parse → Register in Catalog

2. Agent Request → Discover relevant skills → Build context → Inject into prompt

3. Agent Execution → Apply skill instructions → Track usage → Record feedback
```

## Skill File Format

### Structure

Skills are markdown files with YAML frontmatter:

```markdown
---
name: skill-name
display_name: Human Readable Name
version: 1.0.0
scope: task
tags: [tag1, tag2, tag3]
description: Brief description of what this skill provides
author: Author Name
---

# Skill Title

## Overview

Brief overview of the skill and when to use it.

## Instructions

### Step 1: Do This

Detailed instructions...

### Step 2: Do That

More instructions...

## Examples

### Example 1: Common Use Case

**Goal:** What we're trying to achieve

```python
# Example code
def example():
    pass
```

**Explanation:** Why this works...

## Best Practices

- Practice 1
- Practice 2
- Practice 3

## Warnings

⚠️ **Warning 1**: Description of potential pitfall

⚠️ **Warning 2**: Another important caution
```

### Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Unique identifier (kebab-case) |
| `display_name` | string | No | Human-readable name |
| `version` | string | Yes | Semantic version (e.g., 1.0.0) |
| `scope` | enum | Yes | global, agent, workflow, or task |
| `tags` | array | Yes | Keywords for discovery |
| `description` | string | Yes | Brief description |
| `author` | string | No | Author name |

### Skill Scopes

| Scope | Description | Usage |
|-------|-------------|-------|
| **global** | System-wide principles | Applied to all agents always |
| **agent** | Agent-specific behavior | Applied to specific agent types |
| **workflow** | Multi-step processes | Applied to complex workflows |
| **task** | Single task guidance | Applied to specific tasks |

## Usage

### For Developers

#### 1. Creating a New Skill

Create a new `.md` file in `backend/skills/`:

```bash
cd backend/skills/
touch my-new-skill.md
```

Write your skill following the format above. The skill will be automatically loaded on server restart.

#### 2. Loading Skills Programmatically

```python
from app.skills import setup_skills

# Initialize skills system (called in main.py on startup)
catalog = setup_skills(skills_dir="backend/skills")

# Access catalog
from app.skills.catalog import get_skill_catalog

catalog = get_skill_catalog()
print(f"Loaded {catalog.get_enabled_count()} skills")
```

#### 3. Discovering Skills

```python
from app.skills.catalog import get_skill_catalog
from app.schemas.skill import SkillDiscoveryRequest, SkillScope

catalog = get_skill_catalog()

# Discover skills relevant to a task
request = SkillDiscoveryRequest(
    task_description="optimize SQL query performance",
    scope=SkillScope.TASK
)

response = catalog.discover_skills(request)

print(f"Found {len(response.skills)} relevant skills:")
for skill in response.skills:
    print(f"  - {skill.metadata.name}: {skill.metadata.description}")
```

#### 4. Building LLM Context

```python
from app.skills.context_builder import get_context_builder

context_builder = get_context_builder(max_tokens=2000)

# Build formatted context
context = context_builder.build_context(
    skills=response.skills,
    include_examples=True,
    include_best_practices=True
)

# Add to LLM prompt
prompt = f"""
{base_prompt}

{context}

Now apply the above skills to solve this problem...
"""
```

#### 5. Agent Loop Integration

The agent loop automatically discovers and applies skills:

```python
from app.services.agents.agent_loop import AgentLoop

# Skills are enabled by default
loop = AgentLoop(
    llm_service=llm,
    tool_router=router,
    tool_catalog=catalog,
    enable_skills=True  # Default
)

# Skills are automatically discovered and injected during _think()
state = await loop.run(
    session_id="session-123",
    agent_name="query_agent",
    goal="Find countries with highest earthquake risk",
    context={"dataset_id": "abc-123"}
)
```

### For API Users

#### List All Skills

```bash
GET /api/v1/skills

# With filters
GET /api/v1/skills?scope=task&enabled_only=true
```

Response:
```json
{
  "skills": [...],
  "total_count": 10,
  "enabled_count": 8
}
```

#### Get Single Skill

```bash
GET /api/v1/skills/{skill_name}
```

#### Discover Skills

```bash
POST /api/v1/skills/discover

{
  "task_description": "optimize SQL queries",
  "scope": "task",
  "required_tags": ["sql", "performance"]
}
```

Response:
```json
{
  "skills": [...],
  "reasoning": "Found 2 potential skills...",
  "confidence": 0.85
}
```

#### Get Formatted Context

```bash
POST /api/v1/skills/context

{
  "skill_names": ["sql-query-optimization", "data-visualization-best-practices"],
  "include_examples": true,
  "include_best_practices": true,
  "max_tokens": 2000
}
```

#### Search Skills

```bash
# By tags
GET /api/v1/skills/search/tags?tags=sql&tags=performance

# By name
GET /api/v1/skills/search/name?query=optimization
```

#### Enable/Disable Skills

```bash
PATCH /api/v1/skills/{skill_name}/enable

{
  "enabled": false
}
```

#### Get Statistics

```bash
GET /api/v1/skills/stats
```

Response:
```json
{
  "total_skills": 10,
  "enabled_skills": 8,
  "scopes": ["global", "task", "workflow"],
  "scope_distribution": {
    "task": 6,
    "workflow": 2,
    "global": 2
  },
  "top_tags": [["sql", 3], ["visualization", 2], ...]
}
```

## Builtin Skills

The system ships with 5 builtin data analysis skills:

### 1. SQL Query Optimization
- **Scope**: task
- **Tags**: sql, performance, optimization, query, database
- **Focus**: Writing efficient SQL queries, identifying bottlenecks

### 2. Data Visualization Best Practices
- **Scope**: task
- **Tags**: visualization, charts, graphs, design, communication
- **Focus**: Creating clear, effective, honest visualizations

### 3. Statistical Analysis Fundamentals
- **Scope**: task
- **Tags**: statistics, analysis, data-science, hypothesis-testing
- **Focus**: Applying statistical methods correctly

### 4. Data Cleaning and Preparation
- **Scope**: task
- **Tags**: data-cleaning, preprocessing, quality, transformation
- **Focus**: Identifying and resolving data quality issues

### 5. Exploratory Data Analysis
- **Scope**: workflow
- **Tags**: eda, exploration, analysis, visualization, statistics
- **Focus**: Systematic approach to exploring new datasets

## Database Integration

Skills can be persisted in the database for:
- User-created custom skills
- Version history
- Usage tracking
- Performance metrics

### Database Models

**SkillModel**: Main skill storage
- Metadata (name, description, version, tags)
- Content (raw markdown + parsed JSON)
- Status (draft, published, deprecated, archived)
- Usage metrics (usage_count, success_count, helpful_count)

**SkillVersion**: Version history
- Tracks changes over time
- Links to skill and author
- Includes change notes

**SkillUsageEvent**: Detailed usage tracking
- Individual usage events
- Success/failure tracking
- User feedback
- Context and metadata

## Best Practices

### Creating Skills

1. **Be specific**: Focus on one task or domain
2. **Include examples**: Show, don't just tell
3. **Add context**: Explain the "why", not just "how"
4. **Test thoroughly**: Verify instructions work as described
5. **Update regularly**: Keep skills current with best practices

### Organizing Skills

- **Task-level**: Specific techniques (SQL optimization)
- **Workflow-level**: Multi-step processes (EDA)
- **Agent-level**: Agent-specific behaviors
- **Global**: Universal principles (rarely needed)

### Tagging Strategy

- Use 3-7 tags per skill
- Include domain tags (sql, statistics)
- Include action tags (optimization, analysis)
- Include technology tags (python, duckdb)
- Keep tags lowercase and consistent

### Performance Considerations

- **Token limits**: Skills consume prompt tokens
- **Discovery speed**: Use clear tags for fast matching
- **Context size**: Limit injected skills to 2-3 most relevant
- **Caching**: Frequently-used skills can be cached

## Advanced Topics

### Custom Skill Discovery

Implement custom discovery logic:

```python
class CustomSkillCatalog(SkillCatalog):
    def discover_skills(self, request):
        # Custom discovery logic
        # Could use embeddings, LLM, or domain-specific rules
        pass
```

### Skill Context Optimization

Optimize context for token efficiency:

```python
# Ultra-compact context (names only)
compact = context_builder.build_compact_context(skills)

# System prompt enhancement
enhancement = context_builder.build_system_prompt_enhancement(
    skills,
    agent_role="data analyst"
)
```

### Skill Usage Tracking

Track and analyze skill effectiveness:

```python
from app.schemas.skill import SkillUsageEvent

catalog.track_usage(SkillUsageEvent(
    skill_name="sql-query-optimization",
    success=True,
    helpful=True,
    feedback="Great guidance on index usage"
))

# Get evaluation metrics
eval = catalog.get_skill_evaluation("sql-query-optimization")
print(f"Success rate: {eval.success_rate:.2%}")
print(f"Helpful: {eval.helpful_count}/{eval.total_uses}")
```

### SkillTool Integration

Use SkillTool in custom tools:

```python
from app.tools.skill_tool import SkillEnhancedTool

class MyCustomTool(SkillEnhancedTool):
    async def execute(self, parameters):
        # Discover relevant skills
        skills = await self.discover_relevant_skills(
            task_description=parameters['task'],
            scope=SkillScope.TASK
        )

        # Get formatted context
        context = await self.get_skill_context(skills)

        # Use in LLM prompt
        prompt = f"{context}\n\nNow solve: {parameters['task']}"

        # Track usage
        await self.track_skill_usage(
            skill_name=skills[0].metadata.name,
            success=True
        )
```

## Troubleshooting

### Skills Not Loading

**Problem**: Skills directory not found or empty

**Solution**:
1. Check `backend/skills/` directory exists
2. Verify `.md` files are present
3. Check server logs for parsing errors
4. Validate YAML frontmatter syntax

### Skills Not Discovered

**Problem**: Relevant skills not being found

**Solution**:
1. Check tags match task keywords
2. Verify skill is enabled (`enabled: true`)
3. Lower discovery threshold in catalog
4. Add more descriptive tags

### Context Too Large

**Problem**: Too many tokens in injected context

**Solution**:
1. Reduce `max_tokens` in context builder
2. Limit to top 1-2 skills instead of 3
3. Disable examples (`include_examples=False`)
4. Use compact context format

### Poor Skill Application

**Problem**: Agent not following skill instructions

**Solution**:
1. Make instructions more explicit
2. Add more examples
3. Improve skill description
4. Check if correct skills are being discovered

## Migration Guide

### From Manual Instructions to Skills

**Before:**
```python
prompt = """
When writing SQL queries:
1. Start with most selective filters
2. Use indexed columns in WHERE
3. Avoid functions on indexed columns
...
"""
```

**After:**
```python
# Create skill file: sql-query-optimization.md
# Loads automatically on startup
# Discovered and injected when relevant
```

### From Hardcoded Examples to Skills

**Before:**
```python
EXAMPLES = [
    "Example 1: ...",
    "Example 2: ...",
]
prompt = f"{instructions}\n\nExamples:\n{EXAMPLES}"
```

**After:**
```markdown
<!-- In skill file -->
## Examples

### Example 1: ...
...

### Example 2: ...
...
```

## Future Enhancements

### Planned Features

1. **Skill Marketplace**: Share and discover community skills
2. **Version Management**: Automatic skill versioning and updates
3. **A/B Testing**: Test skill variations for effectiveness
4. **Skill Chains**: Combine multiple skills automatically
5. **Dynamic Skill Generation**: AI-generated skills from examples
6. **Skill Embeddings**: Semantic search for better discovery
7. **Skill Analytics Dashboard**: Visualize skill performance
8. **Collaborative Editing**: Team-based skill creation

### Experimental Features

- **Skill Learning**: Improve skills based on usage feedback
- **Cross-Agent Skill Transfer**: Share learnings across agents
- **Adaptive Context**: Dynamically adjust skill detail level
- **Skill Recommendations**: Suggest skills to users

## References

- [Anthropic Skills Framework](https://github.com/anthropics/skills)
- [Agent-Native Architecture Guide](docs/AGENT_NATIVE_ARCHITECTURE.md)
- [Skills API Documentation](backend/app/api/endpoints/skills.py)
- [Skill Schema Reference](backend/app/schemas/skill.py)

## Support

For issues or questions:
1. Check server logs for errors
2. Validate skill file format
3. Test with `/api/v1/skills` endpoint
4. Review builtin skills as examples

## Changelog

### Version 1.0.0 (2024-01-11)
- Initial skills system implementation
- 5 builtin data analysis skills
- Agent loop integration
- REST API endpoints
- Database models for persistence
- Comprehensive documentation
