# Async Deep Research

This document explains the asynchronous deep research job system.

## Overview

Deep research jobs can now run in the background using Celery, allowing users to:
- Submit research jobs and get immediate response
- Navigate away while research runs
- Get notifications when jobs complete
- Run multiple research jobs in parallel

## Architecture

```
User submits research → API returns job_id immediately
                       ↓
                  Celery worker executes in background
                       ↓
              Frontend polls for status updates
                       ↓
           Notification shown when complete
```

## Backend Setup

### 1. Install Dependencies

```bash
pip install celery redis
```

### 2. Start Redis (if not already running)

```bash
# Using Docker
docker run -d -p 6379:6379 redis:alpine

# Or using Docker Compose (add to docker-compose.yml)
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### 3. Run Database Migration

```bash
# Create research_jobs table
python setup_database.py

# Or run SQL migration
./run_migrations.sh 004
```

### 4. Start Celery Worker

```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info
```

## API Endpoints

### Submit Research Job

**POST** `/deep-research/jobs/submit`

Request:
```json
{
  "dataset_id": "abc123",
  "question": "What are the top sales trends?",
  "verbose": 1
}
```

Response:
```json
{
  "success": true,
  "job_id": "xyz789",
  "message": "Research job submitted successfully",
  "status": "pending"
}
```

### Get Job Status

**GET** `/deep-research/jobs/{job_id}`

Response:
```json
{
  "success": true,
  "job_id": "xyz789",
  "status": "running",
  "current_stage": "Stage 3/7: Executing queries",
  "progress_percentage": 35,
  "result": null,
  "error_message": null,
  "created_at": "2024-11-27T10:00:00",
  "started_at": "2024-11-27T10:00:01",
  "completed_at": null,
  "execution_time_seconds": null
}
```

When completed:
```json
{
  "success": true,
  "job_id": "xyz789",
  "status": "completed",
  "progress_percentage": 100,
  "result": {
    "main_question": "...",
    "direct_answer": "...",
    "key_findings": [...],
    "supporting_details": [...]
  },
  "execution_time_seconds": 45
}
```

### List Jobs

**GET** `/deep-research/jobs?dataset_id=abc123&status=completed&limit=50`

### Cancel Job

**DELETE** `/deep-research/jobs/{job_id}`

## Frontend Usage

### 1. Submit Job

```typescript
import { useSubmitResearchJob } from '@/hooks/useResearchJobs'

const submitJob = useSubmitResearchJob()

submitJob.mutate(
  { datasetId: 'abc123', question: 'What...', verbose: 1 },
  {
    onSuccess: (data) => {
      console.log('Job submitted:', data.job_id)
    }
  }
)
```

### 2. Poll for Status

```typescript
import { useJobStatus } from '@/hooks/useResearchJobs'

const { data: jobStatus } = useJobStatus(jobId, {
  refetchInterval: (data) => {
    if (data?.status === 'completed' || data?.status === 'failed') {
      return false // Stop polling
    }
    return 2000 // Poll every 2 seconds
  }
}
```

### 3. Use AsyncResearchManager Component

```typescript
import { AsyncResearchManager } from '@/components/research/AsyncResearchManager'

<AsyncResearchManager
  datasetId={datasetId}
  question={question}
  verbose={1}
  triggerSubmit={true}
  onComplete={(result) => {
    console.log('Research completed:', result)
  }}
  onError={(error) => {
    console.error('Research failed:', error)
  }}
  onSubmitted={() => {
    console.log('Job submitted successfully')
  }}
/>
```

## Notifications

### Browser Notifications

The system automatically requests permission for browser notifications and shows them when jobs complete.

### Toast Notifications

In-app toast notifications show:
- Job started (loading state)
- Progress updates (current stage + percentage)
- Completion (with "View Results" action)
- Errors

## Job Status Lifecycle

```
PENDING → RUNNING → COMPLETED
                 ↘ FAILED
                 ↘ CANCELLED
```

- **PENDING**: Job submitted, waiting for worker
- **RUNNING**: Worker executing the research
- **COMPLETED**: Research finished successfully
- **FAILED**: Error occurred during execution
- **CANCELLED**: User cancelled the job

## Progress Stages

Jobs report progress through 7 stages:

1. **Stage 1/7: Decomposing question** (10%)
2. **Stage 2/7: Classifying queries** (20%)
3. **Stage 3/7: Executing queries** (35%)
4. **Stage 4/7: Enriching with follow-ups** (55%)
5. **Stage 5/7: Synthesizing findings** (70%)
6. **Stage 6/7: Generating follow-ups** (80%)
7. **Stage 7/7: Generating verbose analysis** (90%) - Only if verbose=1

## Monitoring

### View Running Jobs

```bash
# Celery flower (web UI)
celery -A app.core.celery_app flower

# Access at http://localhost:5555
```

### Check Job Queue

```python
from app.core.celery_app import celery_app

# Get active tasks
active = celery_app.control.inspect().active()

# Get scheduled tasks
scheduled = celery_app.control.inspect().scheduled()
```

## Configuration

In `.env`:

```bash
REDIS_URL=redis://localhost:6379/0
```

In `app/core/celery_app.py`:

```python
celery_app.conf.update(
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)
```

## Troubleshooting

### Jobs Stuck in PENDING

- Check if Celery worker is running
- Check Redis connection
- View worker logs: `celery -A app.core.celery_app worker --loglevel=debug`

### Jobs Not Updating Progress

- Ensure database connection is working in worker
- Check worker logs for errors
- Verify `research_jobs` table exists

### Notifications Not Showing

- Check browser notification permissions
- Ensure ToastProvider wraps the app
- Check browser console for errors

## Performance

- Workers can run multiple jobs in parallel
- Recommended: 1 worker per CPU core
- Long-running jobs use soft time limits to allow graceful shutdown
- Job results are stored in database for retrieval

## Future Enhancements

- [ ] WebSocket support for real-time updates (no polling)
- [ ] Job priority queue
- [ ] Job retry mechanism
- [ ] Scheduled/recurring research jobs
- [ ] Email notifications
- [ ] Job result export to file
