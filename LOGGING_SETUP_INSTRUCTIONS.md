# Logging Setup Instructions

## What Was Changed

Added comprehensive logging to the agent system to debug why agents aren't being fully called.

### Files Modified

1. **`backend/app/main.py`**
   - Added logging configuration on startup
   - Configured INFO level for agent-related loggers
   - Added test endpoint `/test-logging`

2. **`backend/app/api/endpoints/agents.py`**
   - Added detailed logging throughout chat endpoint

3. **`backend/app/services/agents/agent_orchestrator.py`**
   - Added logging to all orchestration steps
   - Shows agent discovery, selection, and execution

4. **`backend/app/services/agents/agent_factory.py`**
   - Added logging during agent system initialization

## How to Test

### Step 1: Restart Your Server

```bash
cd backend
python run_server.py  # or however you start your server
```

### Step 2: Test Logging Configuration

Visit: `http://localhost:8000/test-logging`

You should see in your server console:
```
2024-01-10 10:30:45 - api.agents - INFO - 🧪 TEST: This is an INFO log from api.agents
2024-01-10 10:30:45 - api.agents - WARNING - ⚠️  TEST: This is a WARNING log
2024-01-10 10:30:45 - api.agents - ERROR - ❌ TEST: This is an ERROR log
2024-01-10 10:30:45 - orchestrator - INFO - 🧪 TEST: This is from orchestrator logger
```

**If you don't see these logs**: Your logging isn't configured correctly.

### Step 3: Test Agent Request

Make the same query again:
```
"Can you identify which countries are more prone to natural disasters"
```

### Step 4: Check Server Logs

You should now see detailed logs like:

```
2024-01-10 10:31:00 - api.agents - INFO - 🎯 AGENT CHAT REQUEST: query='Can you identify which countries are more prone to natural disasters', dataset_id=abc123, agent_name=None
2024-01-10 10:31:00 - api.agents - INFO - ✅ Got orchestrator and context manager
2024-01-10 10:31:00 - api.agents - INFO - 📝 Session ID: session-xyz-789
2024-01-10 10:31:00 - api.agents - INFO - 🆕 Creating new session: session-xyz-789
2024-01-10 10:31:00 - api.agents - INFO - 🤖 Orchestrated mode: auto-selecting agent
2024-01-10 10:31:00 - api.agents - INFO - 🚀 Calling orchestrator.process_query()...
2024-01-10 10:31:00 - orchestrator - INFO - 🎯 ORCHESTRATOR.process_query: query='Can you identify which countries are more prone to natural disasters', dataset_id=abc123, session_id=session-xyz-789
2024-01-10 10:31:00 - orchestrator - INFO - 📦 Getting context for session session-xyz-789...
2024-01-10 10:31:00 - orchestrator - INFO - ✅ Got context with 0 history messages
2024-01-10 10:31:00 - orchestrator - INFO - 💬 Added user message to history
2024-01-10 10:31:00 - orchestrator - INFO - 🧠 Creating execution plan...
2024-01-10 10:31:00 - orchestrator.plan - INFO - 🔍 Finding agents for task: 'Can you identify which countries are more prone to natural disasters'
2024-01-10 10:31:00 - orchestrator.plan - INFO - 📊 Found 3 candidate agents
2024-01-10 10:31:00 - orchestrator.plan - INFO -   - query_agent (SQL Query Agent): 0.75
2024-01-10 10:31:00 - orchestrator.plan - INFO -   - geospatial_agent (Geospatial Agent): 0.65
2024-01-10 10:31:00 - orchestrator.plan - INFO -   - statistical_agent (Statistical Agent): 0.40
2024-01-10 10:31:00 - orchestrator.plan - INFO - ✅ Fast path: Using query_agent with confidence 0.75
2024-01-10 10:31:00 - orchestrator - INFO - 📋 Plan created: mode=single, agents=['query_agent'], reasoning='High confidence match (0.75) with SQL Query Agent'
2024-01-10 10:31:00 - orchestrator - INFO - ⚡ Executing plan without streaming
2024-01-10 10:31:00 - orchestrator.execute - INFO - 🎯 Executing single agent: query_agent
2024-01-10 10:31:00 - orchestrator.execute - INFO - ✅ Found agent: SQL Query Agent
2024-01-10 10:31:00 - orchestrator.execute - INFO - 📦 Request: query='Can you identify which countries are more prone to natural disasters', dataset_id=abc123
2024-01-10 10:31:00 - orchestrator.execute - INFO - 🚀 Calling agent.process()...
[... agent execution ...]
2024-01-10 10:31:02 - orchestrator.execute - INFO - ✅ Agent completed: success=True, has_code=True
2024-01-10 10:31:02 - orchestrator.execute - INFO - 💾 Saved results to context
2024-01-10 10:31:02 - orchestrator - INFO - ✅ Plan execution complete: success=True, agent=query_agent
2024-01-10 10:31:02 - api.agents - INFO - ✅ Orchestrator returned: success=True, agent=query_agent
```

## What to Look For

### ✅ Good Signs
- See `🎯 AGENT CHAT REQUEST`
- See `🤖 Orchestrated mode` or `🎭 Direct agent mode`
- See `📊 Found X candidate agents` with list
- See agent confidence scores (should be > 0.3)
- See `🚀 Calling agent.process()`
- See `✅ Agent completed: success=True`

### ❌ Problem Indicators
- **No logs at all**: Logging not configured
- **`📊 Found 0 candidate agents`**: No agents match the query
- **`❌ Agent not found`**: Agent not registered
- **`❌ Agent execution failed`**: Agent crashed (will show error)
- **Confidence scores all < 0.3**: Query doesn't match any agent keywords

## Troubleshooting

### Issue 1: No Logs Appearing

**Solution**: Make sure you restarted the server after adding logging config.

```bash
# Kill the server
pkill -f "python run_server.py"

# Restart
cd backend
python run_server.py
```

### Issue 2: Only See Uvicorn Logs

**Solution**: Logging is configured but agents aren't being called. Check:
1. Is the request reaching `/api/v1/agents/chat`?
2. Are you using the correct endpoint?
3. Check frontend console for errors

### Issue 3: See "Agent system not initialized"

**Solution**: Check startup logs for:
```
✅ Redis connection successful
🔧 Initializing agent system from config: agents_config.json
✅ Agent system initialized with X agents
```

If not present, check:
- Redis is running
- `agents_config.json` exists in project root
- Config path is correct in `main.py`

### Issue 4: SQL Syntax Error "near duckdb"

This is a separate issue from logging. Once logging is working, we'll see exactly where this error originates.

## Next Steps

1. **Restart server**
2. **Test `/test-logging` endpoint**
3. **Make agent request**
4. **Share full logs from server console**

Then we can diagnose:
- Why multi-agent isn't working as expected
- Why SQL execution is failing
- How to improve agent responses

## Quick Reference

**Log Emojis**:
- 🎯 = Entry point / Main action
- ✅ = Success
- ❌ = Error
- 🤖 = Automated action
- 🎭 = Direct agent selection
- 📊 = Statistics
- 🚀 = Executing
- 💾 = Saving

**Logger Names**:
- `api.agents` - API endpoint
- `orchestrator` - Main orchestrator
- `orchestrator.plan` - Agent selection
- `orchestrator.execute` - Agent execution
- `agent.factory` - System initialization
