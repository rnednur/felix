# Agent System Debug Logging

## Overview

Comprehensive logging has been added throughout the agent system to help debug agent execution flow.

## Log Locations

### 1. API Endpoint (`app/api/endpoints/agents.py`)

**Logger**: `api.agents`

**Logs**:
- 🎯 Request received with query, dataset_id, agent_name
- ✅ Successfully got orchestrator and context manager
- 📝 Session ID (new or existing)
- 🆕 Creating new session
- ♻️  Using existing session
- 🎭 Direct agent mode vs 🤖 Orchestrated mode
- 📋 Agent registry stats (total agents, enabled agents)
- ❌ Agent not found (with available agents list)
- ✅ Found agent with display name
- 📦 Context retrieved with message count
- 🚀 Calling agent.process()
- ✅ Agent returned with success status

### 2. Agent Orchestrator (`app/services/agents/agent_orchestrator.py`)

**Loggers**:
- `orchestrator` - Main orchestrator
- `orchestrator.plan` - Plan creation
- `orchestrator.execute` - Agent execution

**Logs**:
- 🎯 ORCHESTRATOR.process_query with all parameters
- 📦 Getting context
- ✅ Got context with history count
- 💬 Added user message to history
- 🧠 Creating execution plan
- 📋 Plan created with mode, agents, reasoning
- 📡 Executing with streaming
- ⚡ Executing without streaming
- ✅ Plan execution complete
- 🔍 Finding agents for task
- 📊 Found N candidate agents
- List of top candidates with confidence scores
- ✅ Fast path selected agent
- 🤔 Using LLM for plan (low confidence)
- 🎯 Executing single agent
- ❌ Agent not found (with available list)
- ✅ Found agent
- 📦 Request details
- 🚀 Calling agent.process()
- ✅ Agent completed with status
- 💾 Saved results to context
- ❌ Agent execution failed with stack trace

### 3. Agent Factory (`app/services/agents/agent_factory.py`)

**Logger**: `agent.factory`

**Logs**:
- 🔧 Initializing agent system
- ✅ Created core services
- 📖 Loading agent configs
- 📋 Loaded N configurations
- ⏭️  Skipping disabled agents
- 🔨 Creating each agent
- ✅ Registered agent
- ⚠️  Could not create agent
- ✅ Successfully created N agents
- ⚠️  Config file not found
- 🎭 Creating orchestrator
- ✅ Initialization complete
- 📊 Total and enabled agent counts

## How to Use

### Enable Debug Logging

Add to your logging configuration:

```python
import logging

# Enable all agent-related logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Or be more specific
logging.getLogger("api.agents").setLevel(logging.INFO)
logging.getLogger("orchestrator").setLevel(logging.INFO)
logging.getLogger("orchestrator.plan").setLevel(logging.INFO)
logging.getLogger("orchestrator.execute").setLevel(logging.INFO)
logging.getLogger("agent.factory").setLevel(logging.INFO)
```

### Reading the Logs

**Typical Successful Flow**:
```
[API] 🎯 AGENT CHAT REQUEST: query='What is the average price?'
[API] ✅ Got orchestrator and context manager
[API] 📝 Session ID: abc-123
[API] 🤖 Orchestrated mode: auto-selecting agent
[API] 🚀 Calling orchestrator.process_query()...
[ORCH] 🎯 ORCHESTRATOR.process_query: query='What is the average price?'
[ORCH] 📦 Getting context for session abc-123...
[ORCH] ✅ Got context with 2 history messages
[ORCH] 💬 Added user message to history
[ORCH] 🧠 Creating execution plan...
[PLAN] 🔍 Finding agents for task: 'What is the average price?'
[PLAN] 📊 Found 3 candidate agents
[PLAN]   - query_agent (SQL Query Agent): 0.85
[PLAN]   - statistical_agent (Statistical Agent): 0.45
[PLAN]   - data_scouting_agent (Data Scout): 0.30
[PLAN] ✅ Fast path: Using query_agent with confidence 0.85
[ORCH] 📋 Plan created: mode=single, agents=['query_agent']
[ORCH] ⚡ Executing plan without streaming
[EXEC] 🎯 Executing single agent: query_agent
[EXEC] ✅ Found agent: SQL Query Agent
[EXEC] 📦 Request: query='What is the average price?', dataset_id=xyz-789
[EXEC] 🚀 Calling agent.process()...
[EXEC] ✅ Agent completed: success=True, has_code=True
[EXEC] 💾 Saved results to context
[ORCH] ✅ Plan execution complete: success=True, agent=query_agent
[API] ✅ Orchestrator returned: success=True, agent=query_agent
```

**Agent Not Found**:
```
[API] 🎭 Direct agent mode: invalid_agent
[API] 📋 Registry has 6 agents, 6 enabled
[API] ❌ Agent not found: invalid_agent
[API] Available agents: ['query_agent', 'statistical_agent', ...]
```

**No Agents Found**:
```
[PLAN] 🔍 Finding agents for task: 'impossible task'
[PLAN] 📊 Found 0 candidate agents
[ORCH] 📋 Plan created: mode=single, agents=[]
[EXEC] ❌ No agents available to handle this query
```

**Agent Execution Error**:
```
[EXEC] 🚀 Calling agent.process()...
[EXEC] ❌ Agent execution failed: Database connection timeout
  File "agent.py", line 123, in process
    result = await self.service.execute()
  [full stack trace]
```

## Debugging Checklist

When agents aren't being called, check logs for:

1. **Is the agent system initialized?**
   - Look for: `✅ Agent system initialized with N agents`
   - If missing: Agent system not set up on startup

2. **Is the agent registered?**
   - Look for: `✅ Registered agent: agent_name`
   - Check: `Available agents: [...]` list

3. **Is agent discovery working?**
   - Look for: `📊 Found N candidate agents`
   - Check confidence scores
   - If 0 candidates: Keywords don't match query

4. **Is the agent being selected?**
   - Look for: `✅ Fast path: Using agent_name`
   - Or: `🤔 Low confidence, using LLM`

5. **Is agent.process() being called?**
   - Look for: `🚀 Calling agent.process()...`
   - Look for: `✅ Agent completed` or `❌ Agent execution failed`

6. **Check for errors**:
   - Search logs for: `❌` or `ERROR`
   - Check stack traces for root cause

## Common Issues

### Issue: "Agent system not initialized"

**Symptom**: `RuntimeError: Agent system not initialized`

**Solution**: Make sure `setup_agent_system()` is called on app startup

```python
# In main.py or app startup
from app.services.agents import setup_agent_system
setup_agent_system(redis_client, "backend/agents_config.json")
```

### Issue: "No agents available"

**Symptom**: `📊 Found 0 candidate agents`

**Solution**:
1. Check agent config file exists
2. Check agents are enabled in config
3. Check keywords match query terms

### Issue: "Agent not found in registry"

**Symptom**: `❌ Agent not found: agent_name`

**Solution**:
1. Check agent name spelling
2. Check agent is registered at startup
3. Check available agents list in logs

### Issue: Low Confidence Scores

**Symptom**: All agents have confidence < 0.7

**Solution**:
1. Add more keywords to agent config
2. Improve query phrasing
3. Check intent_keywords in agents_config.json

## Log Emojis Reference

- 🎯 Entry point / Main action
- ✅ Success / Completed
- ❌ Error / Failed
- ⚠️  Warning
- 📝 Session / ID
- 🆕 New / Created
- ♻️  Reused / Existing
- 🎭 Agent selection
- 🤖 Automated action
- 📋 List / Registry
- 📦 Context / Data
- 💬 Message
- 🧠 Thinking / Planning
- 🔍 Finding / Searching
- 📊 Statistics / Count
- ⚡ Fast action
- 📡 Streaming
- 🚀 Executing / Starting
- 💾 Saving
- 🔧 Initialization
- 🔨 Creating / Building
- ⏭️  Skipping
- 📖 Loading

## Performance Tips

- Use structured logging for production
- Set log level to WARNING in production
- Use DEBUG only when actively debugging
- Consider log aggregation (ELK, CloudWatch, etc.)
