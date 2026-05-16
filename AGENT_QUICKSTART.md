# Multi-Agent System Quick Start Guide

## Prerequisites

The multi-agent system requires **Redis** for session management and context storage.

### Check if Redis is needed

Your backend will still work without Redis, but **agent endpoints will not be available**.

```bash
# When you start the backend, look for this message:
✅ Redis connection successful
✅ Agent system initialized with 2 agents

# OR (if Redis is not running):
⚠️  Warning: Could not initialize agent system: Error 61 connecting to localhost:6379
   Agent endpoints will not be available
```

---

## Starting Redis

### **Option 1: Docker (Recommended)**

**Easiest and most reliable method.**

#### Step 1: Start Docker Desktop
- Open Docker Desktop application
- Wait for it to fully start (whale icon should be steady)

#### Step 2: Run the setup script
```bash
cd backend
./start_redis.sh
```

That's it! Redis will be running on `localhost:6379`.

---

### **Option 2: Homebrew (macOS)**

If you prefer native installation:

```bash
# Install Redis
brew install redis

# Start Redis service
brew services start redis

# Verify it's running
redis-cli ping  # Should return "PONG"
```

---

### **Option 3: Manual Docker Command**

If you prefer manual control:

```bash
# Start Redis container
docker run -d \
  --name redis-agent \
  -p 6379:6379 \
  --restart unless-stopped \
  redis:alpine

# Verify it's running
docker exec redis-agent redis-cli ping  # Should return "PONG"
```

---

## Starting the Backend

Once Redis is running:

```bash
cd backend

# Activate virtual environment (if using one)
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Expected Output

```
INFO:     Will watch for changes in these directories: ['/Users/.../backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
✅ Redis connection successful
✅ Agent system initialized with 2 agents
INFO:     Application startup complete.
```

---

## Testing the Agent System

### 1. Check Available Agents

```bash
curl http://localhost:8000/api/v1/agents
```

**Expected Response:**
```json
{
  "agents": [
    {
      "name": "query_agent",
      "display_name": "SQL Query Agent",
      "description": "Translates natural language to SQL queries using DuckDB",
      "capabilities": ["sql_generation", "aggregations", "filtering", "joins"],
      "tier": "free",
      "enabled": true
    },
    {
      "name": "data_scouting_agent",
      "display_name": "Data Scouting Agent",
      "description": "Profiles data and detects quality issues, patterns, and PII",
      "capabilities": ["pattern_detection", "pii_detection", "quality_assessment"],
      "tier": "free",
      "enabled": true
    }
  ]
}
```

### 2. Chat with an Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is in this dataset?",
    "dataset_id": "your-dataset-id-here"
  }'
```

**Response:**
```json
{
  "session_id": "generated-session-uuid",
  "agent": "data_scouting_agent",
  "response": {
    "summary": "Found 10 observations about the data",
    "observations": [...],
    "discrepancies": [...],
    "type": "data_profiling"
  },
  "metadata": {...}
}
```

### 3. Check API Documentation

Visit: http://localhost:8000/docs

You'll see all agent endpoints under the **agents** tag:
- `GET /api/v1/agents` - List agents
- `POST /api/v1/agents/chat` - Chat with agents
- `POST /api/v1/agents/chat/stream` - Streaming chat
- `GET /api/v1/agents/sessions` - List sessions
- And more...

---

## Troubleshooting

### Issue: "Error 61 connecting to localhost:6379"

**Solution:** Redis is not running.

```bash
# If using Docker:
./start_redis.sh

# If using Homebrew:
brew services start redis

# Verify:
redis-cli ping  # Should return "PONG"
```

### Issue: Docker command fails

**Solution:** Docker Desktop is not running.

1. Open Docker Desktop app
2. Wait for it to fully start
3. Try again: `./start_redis.sh`

### Issue: Agent endpoints return 500 errors

**Solution:** Agent system not initialized.

1. Check backend logs for initialization errors
2. Verify Redis is running: `redis-cli ping`
3. Restart backend server
4. Check that you see: `✅ Agent system initialized`

### Issue: "Agent system not initialized" error

**Solution:** The agent registry/orchestrator wasn't set up.

This usually means Redis connection failed during startup. Fix Redis connection and restart backend.

---

## Managing Redis

### View Redis Data

```bash
# Connect to Redis CLI
redis-cli

# Or via Docker:
docker exec -it redis-agent redis-cli

# List all keys
127.0.0.1:6379> KEYS *

# Get a session
127.0.0.1:6379> GET agent_context:session-uuid-here

# Exit
127.0.0.1:6379> EXIT
```

### Clear All Agent Sessions

```bash
redis-cli FLUSHDB
```

### Stop Redis

```bash
# Docker:
docker stop redis-agent

# Homebrew:
brew services stop redis
```

### Remove Redis Container

```bash
docker rm redis-agent
```

---

## Environment Variables

The agent system uses these settings from `.env`:

```bash
# Redis connection
REDIS_URL=redis://localhost:6379/0

# OpenRouter for LLM calls
OPENROUTER_API_KEY=your-key-here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Optional: Agent-specific settings
# (These have defaults, but can be customized)
```

---

## Next Steps

Once the backend is running with agents:

1. **Frontend Integration**: Follow `AGENT_FRONTEND_INTEGRATION.md`
2. **Add More Agents**: See `MULTI_AGENT_ARCHITECTURE.md` Phase 3
3. **Test with Real Data**: Upload a dataset and try queries
4. **Monitor Performance**: Check `/agents/sessions` for execution metrics

---

## Agent Capabilities

### Query Agent
**Best for:**
- "Show me the first 10 rows"
- "What's the average price?"
- "Count records by category"
- "Filter where sales > 1000"

**Returns:** SQL query + results preview

### Data Scouting Agent
**Best for:**
- "Profile this dataset"
- "Check data quality"
- "Find PII in the data"
- "What patterns exist?"

**Returns:** Observations, quality issues, PII warnings, profiling data

---

## Quick Reference

```bash
# Start everything
./start_redis.sh          # Start Redis
uvicorn app.main:app --reload  # Start backend

# Stop everything
docker stop redis-agent   # Stop Redis
# Ctrl+C in backend terminal

# Check status
redis-cli ping                    # Redis health
curl http://localhost:8000/health # Backend health
curl http://localhost:8000/api/v1/agents  # Agents available

# View logs
docker logs redis-agent          # Redis logs
# Backend logs are in terminal
```

---

## Support

For issues or questions:
1. Check logs: backend terminal + `docker logs redis-agent`
2. Verify Redis: `redis-cli ping`
3. Check API docs: http://localhost:8000/docs
4. Review architecture: `MULTI_AGENT_ARCHITECTURE.md`
