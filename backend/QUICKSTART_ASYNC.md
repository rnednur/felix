# Quick Start: Async Deep Research

Get async research jobs running in 5 minutes.

## Prerequisites

- Python 3.9+
- PostgreSQL with database created
- Redis (for Celery)

## 1. Install Dependencies

```bash
pip install celery redis
```

## 2. Start Redis

### Option A: Docker
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

### Option B: Local Install
```bash
# macOS
brew install redis
redis-server

# Ubuntu
sudo apt install redis-server
sudo systemctl start redis
```

### Verify Redis
```bash
redis-cli ping
# Should return: PONG
```

## 3. Run Database Migration

```bash
# This creates the research_jobs table
python setup_database.py
```

## 4. Start Services

### Option A: Start All (Recommended)
```bash
./start_all.sh
```

This starts:
- FastAPI server (port 8000)
- Celery worker

### Option B: Start Separately

Terminal 1 - API Server:
```bash
python run_server.py
```

Terminal 2 - Celery Worker:
```bash
celery -A app.core.celery_app worker --loglevel=info
```

## 5. Test It Out

### Using Frontend

1. Navigate to a dataset
2. Enter a research question
3. Click "Run Research"
4. Job runs in background
5. Get notification when complete

### Using API

```bash
# Submit job
curl -X POST http://localhost:8000/api/v1/deep-research/jobs/submit \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "your-dataset-id",
    "question": "What are the key insights?",
    "verbose": 1
  }'

# Response: {"job_id": "xyz789", ...}

# Check status
curl http://localhost:8000/api/v1/deep-research/jobs/xyz789

# List all jobs
curl http://localhost:8000/api/v1/deep-research/jobs
```

## Monitoring

### Celery Flower (Web UI)

```bash
pip install flower
celery -A app.core.celery_app flower

# Open http://localhost:5555
```

### View Logs

```bash
# Worker logs
tail -f logs/celery.log

# API logs
tail -f logs/api.log
```

### Database Queries

```sql
-- View all jobs
SELECT id, dataset_id, main_question, status, progress_percentage, created_at
FROM research_jobs
ORDER BY created_at DESC
LIMIT 10;

-- Count by status
SELECT status, COUNT(*)
FROM research_jobs
GROUP BY status;

-- Running jobs
SELECT id, main_question, current_stage, progress_percentage
FROM research_jobs
WHERE status = 'running';
```

## Troubleshooting

### Jobs stuck in "pending"

**Problem**: Job status stays "pending" and never starts

**Solutions**:
1. Check if Celery worker is running:
   ```bash
   ps aux | grep celery
   ```

2. Check worker logs for errors:
   ```bash
   celery -A app.core.celery_app worker --loglevel=debug
   ```

3. Verify Redis connection:
   ```bash
   redis-cli ping
   ```

4. Check `.env` has correct `REDIS_URL`:
   ```bash
   REDIS_URL=redis://localhost:6379/0
   ```

### Worker crashes

**Problem**: Celery worker exits unexpectedly

**Solutions**:
1. Check for import errors:
   ```bash
   python -c "from app.tasks.research_tasks import run_deep_research"
   ```

2. Verify database connection in worker

3. Check memory usage (workers have 1GB limit per task)

### No notifications

**Problem**: Frontend doesn't show notifications

**Solutions**:
1. Check browser notification permissions
2. Verify ToastProvider wraps App
3. Check polling interval in useJobStatus hook
4. Open browser console for errors

## Performance Tips

### Multiple Workers

Run multiple workers for parallel job execution:

```bash
# 4 workers
celery -A app.core.celery_app worker --concurrency=4

# Or 4 separate worker processes
for i in {1..4}; do
  celery -A app.core.celery_app worker --loglevel=info &
done
```

### Production Setup

Use a process manager like Supervisor:

```ini
; /etc/supervisor/conf.d/celery.conf
[program:celery-worker]
command=celery -A app.core.celery_app worker --loglevel=info
directory=/path/to/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery-worker.log
```

## What's Next?

- See [ASYNC_RESEARCH.md](./ASYNC_RESEARCH.md) for detailed API docs
- Check [run_worker.py](./run_worker.py) for worker startup
- Review [migrations/004_add_research_jobs.sql](./migrations/004_add_research_jobs.sql) for schema

## Common Commands

```bash
# Start everything
./start_all.sh

# Stop everything
pkill -f 'run_server.py'
pkill -f 'celery.*worker'

# Restart worker only
pkill -f 'celery.*worker'
celery -A app.core.celery_app worker --loglevel=info &

# View active jobs
celery -A app.core.celery_app inspect active

# Purge all pending jobs
celery -A app.core.celery_app purge
```
