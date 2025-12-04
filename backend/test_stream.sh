#!/bin/bash
# Test the AG-UI streaming endpoint

TOKEN="$1"
WORKSPACE_ID="$2"
DATASET_ID="$3"
MESSAGE="${4:-Show top 10 rows}"

if [ -z "$TOKEN" ] || [ -z "$WORKSPACE_ID" ] || [ -z "$DATASET_ID" ]; then
    echo "Usage: ./test_stream.sh <token> <workspace_id> <dataset_id> [message]"
    exit 1
fi

echo "🔄 Starting stream test..."
echo "Message: $MESSAGE"
echo ""

curl -N -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/canvas/stream?workspace_id=$WORKSPACE_ID&message=$MESSAGE&dataset_id=$DATASET_ID"
