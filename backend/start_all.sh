#!/bin/bash
# Start all services for AI Analytics Platform
# This script starts:
# 1. FastAPI server
# 2. Celery worker for async tasks

set -e

echo "=========================================="
echo "Starting AI Analytics Platform"
echo "=========================================="

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Warning: Redis is not running!"
    echo "Start Redis first:"
    echo "  docker run -d -p 6379:6379 redis:alpine"
    echo "  OR"
    echo "  redis-server"
    exit 1
fi

echo "✓ Redis is running"

# Start FastAPI server in background
echo ""
echo "Starting FastAPI server..."
python run_server.py &
SERVER_PID=$!
echo "✓ FastAPI server started (PID: $SERVER_PID)"

# Wait a moment for server to start
sleep 2

# Start Celery worker in background
echo ""
echo "Starting Celery worker..."
celery -A app.core.celery_app worker --loglevel=info &
WORKER_PID=$!
echo "✓ Celery worker started (PID: $WORKER_PID)"

echo ""
echo "=========================================="
echo "✅ All services started successfully!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - FastAPI API:     http://localhost:8000"
echo "  - API Docs:        http://localhost:8000/docs"
echo "  - Celery Worker:   Running (PID: $WORKER_PID)"
echo "  - Redis:           redis://localhost:6379"
echo ""
echo "To stop all services:"
echo "  kill $SERVER_PID $WORKER_PID"
echo ""
echo "Or use:"
echo "  pkill -f 'run_server.py'"
echo "  pkill -f 'celery.*worker'"
echo ""

# Wait for interrupt
trap "echo ''; echo 'Stopping services...'; kill $SERVER_PID $WORKER_PID 2>/dev/null; exit 0" INT TERM

# Keep script running
wait
