# Felix API Reference

Complete reference for Felix's REST API endpoints.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently Felix does not require authentication. Future versions will support JWT tokens.

## Common Response Format

### Success Response
```json
{
  "status": "success",
  "data": { ... }
}
```

### Error Response
```json
{
  "detail": "Error message here"
}
```

## Endpoints

### Datasets

#### Upload Dataset

Upload a new dataset file.

```http
POST /datasets/upload
Content-Type: multipart/form-data

Parameters:
  file: File (CSV, Excel, or Parquet)

Response: 201 Created
{
  "id": "uuid",
  "name": "filename.csv",
  "file_type": "csv",
  "row_count": 1000,
  "column_count": 10,
  "upload_status": "completed"
}
```

#### List Datasets

Get all uploaded datasets.

```http
GET /datasets

Response: 200 OK
[
  {
    "id": "uuid",
    "name": "sales_data.csv",
    "row_count": 5000,
    "column_count": 15,
    "created_at": "2024-01-01T10:00:00Z"
  }
]
```

#### Get Dataset

Get dataset details.

```http
GET /datasets/{dataset_id}

Response: 200 OK
{
  "id": "uuid",
  "name": "sales_data.csv",
  "row_count": 5000,
  "column_count": 15,
  "file_size_mb": 2.5,
  "created_at": "2024-01-01T10:00:00Z"
}
```

#### Get Dataset Schema

Get column information and statistics.

```http
GET /datasets/{dataset_id}/schema

Response: 200 OK
{
  "columns": [
    {
      "name": "customer_id",
      "dtype": "int64",
      "stats": {
        "count": 5000,
        "min": 1,
        "max": 9999,
        "mean": 5234.2
      }
    },
    {
      "name": "product_category",
      "dtype": "object",
      "stats": {
        "count": 5000,
        "unique": 8,
        "top_values": [
          ["Electronics", 1234],
          ["Clothing", 987]
        ]
      }
    }
  ]
}
```

#### Get Dataset Preview

Get first N rows of data.

```http
GET /datasets/{dataset_id}/preview?limit=100

Response: 200 OK
{
  "columns": ["col1", "col2", "col3"],
  "data": [
    ["value1", "value2", "value3"],
    ...
  ],
  "total_rows": 5000,
  "preview_rows": 100
}
```

#### Delete Dataset

Delete a dataset.

```http
DELETE /datasets/{dataset_id}

Response: 204 No Content
```

### Natural Language Queries (SQL)

#### Execute NL Query

Convert natural language to SQL and execute.

```http
POST /nl-query

Body:
{
  "dataset_id": "uuid",
  "query": "Show top 10 customers by revenue"
}

Response: 200 OK
{
  "sql": "SELECT customer_id, SUM(revenue) as total FROM dataset GROUP BY customer_id ORDER BY total DESC LIMIT 10",
  "columns": ["customer_id", "total"],
  "data": [
    [101, 50000],
    [205, 45000],
    ...
  ],
  "total_rows": 10,
  "execution_time_ms": 45
}
```

### Python Analysis

#### Generate Python Code

Generate Python code from natural language.

```http
POST /python-analysis/generate

Body:
{
  "dataset_id": "uuid",
  "query": "Build a prediction model for sales",
  "mode": "auto",  // "auto", "python", "ml", "stats", "workflow"
  "execute_immediately": false
}

Response: 200 OK
{
  "execution_id": "uuid",
  "mode": "ml",
  "generated_code": "import pandas as pd\n...",
  "steps": [
    {
      "step": 1,
      "description": "Load and preprocess data"
    }
  ],
  "estimated_runtime": "30-120 seconds (ML model training)",
  "requires_review": false,
  "safety_warnings": null
}
```

#### Execute Python Code

Execute previously generated Python code.

```http
POST /python-analysis/execute

Body:
{
  "execution_id": "uuid"
}

Response: 200 OK
{
  "execution_id": "uuid",
  "status": "SUCCESS",  // "SUCCESS", "FAILED", "TIMEOUT"
  "output": {
    "summary": "Model trained successfully. R² = 0.85",
    "data": [...],
    "metrics": {
      "r2_score": 0.85,
      "rmse": 12.3
    }
  },
  "visualizations": [
    {
      "type": "scatter",
      "format": "png",
      "data": "base64_encoded_image"
    }
  ],
  "error": null,
  "execution_time_ms": 45000
}
```

#### Get Execution Result

Get status and results of a Python execution.

```http
GET /python-analysis/execution/{execution_id}

Response: 200 OK
{
  "execution_id": "uuid",
  "status": "SUCCESS",
  "output": { ... },
  "visualizations": [ ... ],
  "error": null,
  "execution_time_ms": 45000
}
```

#### List Dataset Executions

Get all Python executions for a dataset.

```http
GET /python-analysis/executions/dataset/{dataset_id}?limit=50

Response: 200 OK
[
  {
    "execution_id": "uuid",
    "nl_input": "Build prediction model",
    "mode": "ml",
    "status": "SUCCESS",
    "execution_time_ms": 45000,
    "created_at": "2024-01-01T10:00:00Z"
  }
]
```

### Deep Research

#### Start Deep Research

Start a deep research analysis.

```http
POST /deep-research/start

Body:
{
  "dataset_id": "uuid",
  "question": "Why are sales declining in Q3?"
}

Response: 202 Accepted
{
  "research_id": "uuid",
  "status": "running",
  "estimated_time_seconds": 120
}
```

#### Get Research Status

Check status of running research.

```http
GET /deep-research/{research_id}/status

Response: 200 OK
{
  "research_id": "uuid",
  "status": "running",  // "running", "completed", "failed"
  "progress": 0.45,  // 0.0 to 1.0
  "current_step": "Analyzing regional trends",
  "completed_steps": 5,
  "total_steps": 10
}
```

#### Get Research Result

Get completed research report.

```http
GET /deep-research/{research_id}/result

Response: 200 OK
{
  "research_id": "uuid",
  "main_question": "Why are sales declining in Q3?",
  "direct_answer": "Sales are declining...",
  "key_findings": [
    "Finding 1",
    "Finding 2"
  ],
  "supporting_details": [
    {
      "question": "Sub-question 1",
      "method": "sql",
      "success": true,
      "data": { ... }
    }
  ],
  "visualizations": [ ... ],
  "follow_up_questions": [ ... ],
  "execution_time_seconds": 125,
  "sub_questions_count": 8
}
```

### Dataset Description

#### Generate Dataset Description

Get AI-generated dataset description.

```http
POST /describe-dataset

Body:
{
  "dataset_id": "uuid"
}

Response: 200 OK
{
  "dataset_id": "uuid",
  "description_text": "This dataset contains sales transactions...",
  "key_insights": [
    "5000 records spanning 2 years",
    "8 product categories",
    "Revenue ranges from $10 to $50000"
  ],
  "recommendations": [
    "Analyze sales by category",
    "Look for seasonal patterns"
  ]
}
```

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 202 | Accepted (async operation started) |
| 204 | No Content (successful deletion) |
| 400 | Bad Request (invalid parameters) |
| 404 | Not Found (dataset/execution not found) |
| 422 | Unprocessable Entity (validation error) |
| 500 | Internal Server Error |

## Rate Limiting

Currently no rate limits. Future versions may implement:
- 100 requests/minute per IP
- 1000 requests/hour per IP

## Pagination

For endpoints returning lists, use query parameters:

```http
GET /datasets?offset=0&limit=50
```

## Filtering and Sorting

Datasets can be filtered and sorted:

```http
GET /datasets?sort_by=created_at&order=desc&file_type=csv
```

## Webhooks

Not currently supported. Future feature for async notifications.

## SDK Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Upload dataset
with open('data.csv', 'rb') as f:
    response = requests.post(
        f"{BASE_URL}/datasets/upload",
        files={'file': f}
    )
    dataset = response.json()
    dataset_id = dataset['id']

# Execute NL query
response = requests.post(
    f"{BASE_URL}/nl-query",
    json={
        "dataset_id": dataset_id,
        "query": "Show top 10 customers by revenue"
    }
)
result = response.json()
print(result['data'])

# Generate and execute Python code
code_response = requests.post(
    f"{BASE_URL}/python-analysis/generate",
    json={
        "dataset_id": dataset_id,
        "query": "Build regression model for sales",
        "execute_immediately": False
    }
)
execution_id = code_response.json()['execution_id']

# Execute the code
exec_response = requests.post(
    f"{BASE_URL}/python-analysis/execute",
    json={"execution_id": execution_id}
)
result = exec_response.json()
print(f"Model R²: {result['output']['metrics']['r2_score']}")
```

### JavaScript

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

// Upload dataset
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch(`${BASE_URL}/datasets/upload`, {
  method: 'POST',
  body: formData
});
const dataset = await uploadResponse.json();

// Execute NL query
const queryResponse = await fetch(`${BASE_URL}/nl-query`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    dataset_id: dataset.id,
    query: 'Show top 10 customers by revenue'
  })
});
const result = await queryResponse.json();
console.log(result.data);
```

### cURL

```bash
# Upload dataset
curl -X POST http://localhost:8000/api/v1/datasets/upload \
  -F "file=@data.csv"

# Execute NL query
curl -X POST http://localhost:8000/api/v1/nl-query \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "uuid",
    "query": "Show top 10 customers by revenue"
  }'

# Start deep research
curl -X POST http://localhost:8000/api/v1/deep-research/start \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "uuid",
    "question": "Why are sales declining?"
  }'
```

## OpenAPI Documentation

Interactive API documentation available at:

```
http://localhost:8000/docs
```

Alternative ReDoc documentation:

```
http://localhost:8000/redoc
```

## Best Practices

### 1. Handle Async Operations

For long-running operations (Python execution, Deep Research):

```python
# Start operation
response = requests.post(url, json=data)
execution_id = response.json()['execution_id']

# Poll for completion
import time
while True:
    status = requests.get(f"{url}/{execution_id}").json()
    if status['status'] in ['SUCCESS', 'FAILED']:
        break
    time.sleep(2)
```

### 2. Error Handling

```python
try:
    response = requests.post(url, json=data)
    response.raise_for_status()
    result = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        print("Dataset not found")
    else:
        print(f"Error: {e.response.json()['detail']}")
```

### 3. Timeout Settings

```python
# Set appropriate timeouts
response = requests.post(
    url,
    json=data,
    timeout=30  # 30 second timeout
)
```

## Next Steps

- Review [Configuration](./configuration.md) for API settings
- Check [Development](./development.md) for extending the API
- Read [Architecture](./architecture.md) for system design
