#!/bin/bash

# Script to start Redis for the agent system

echo "🚀 Starting Redis for AI Agent System..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo ""
    echo "Please start Docker Desktop and try again."
    echo ""
    echo "Alternative: Install Redis with Homebrew:"
    echo "  brew install redis"
    echo "  brew services start redis"
    exit 1
fi

# Check if redis-agent container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^redis-agent$"; then
    echo "📦 Redis container already exists"

    # Check if it's running
    if docker ps --format '{{.Names}}' | grep -q "^redis-agent$"; then
        echo "✅ Redis is already running on port 6379"
    else
        echo "🔄 Starting existing Redis container..."
        docker start redis-agent
        echo "✅ Redis started on port 6379"
    fi
else
    echo "📥 Creating and starting Redis container..."
    docker run -d \
        --name redis-agent \
        -p 6379:6379 \
        --restart unless-stopped \
        redis:alpine

    if [ $? -eq 0 ]; then
        echo "✅ Redis started successfully on port 6379"
    else
        echo "❌ Failed to start Redis"
        exit 1
    fi
fi

# Test connection
echo "🔍 Testing Redis connection..."
sleep 2

if docker exec redis-agent redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is responding to PING"
    echo ""
    echo "🎉 Redis is ready for agent system!"
    echo ""
    echo "You can now start your backend:"
    echo "  cd backend"
    echo "  uvicorn app.main:app --reload"
else
    echo "⚠️  Redis container is running but not responding"
    echo "Try: docker logs redis-agent"
fi

echo ""
echo "Useful commands:"
echo "  Stop Redis:    docker stop redis-agent"
echo "  Remove Redis:  docker rm redis-agent"
echo "  View logs:     docker logs redis-agent"
echo "  Redis CLI:     docker exec -it redis-agent redis-cli"
