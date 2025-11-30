# Configuration Guide

Complete configuration reference for Felix.

## Environment Variables

### Backend Configuration

Located in `backend/.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_analytics

# Redis (optional, for Celery)
REDIS_URL=redis://localhost:6379/0

# OpenRouter API
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# Environment
ENVIRONMENT=development  # or production

# HuggingFace (for embeddings)
HF_HUB_OFFLINE=1         # Use cached models
TRANSFORMERS_OFFLINE=1
```

### Available Models

Configure `OPENROUTER_MODEL` with any OpenRouter-supported model:

**Recommended Models**:
- `anthropic/claude-4.5-sonnet` - Best quality (default)
- `anthropic/claude-4.5-opus` - Highest quality, slower
- `openai/gpt-4-turbo` - Very good, faster
- `google/gemini-2.5-flash` - Fast and cheap
- `openai/gpt-3.5-turbo` - Cheapest, lower quality

**Specialized Models**:
- `openrouter/sherlock-dash-alpha` - Fast reasoning
- `moonshotai/kimi-k2-thinking` - Deep thinking
- `openai/gpt-5.1-codex` - Code generation

See [OpenRouter Models](https://openrouter.ai/models) for full list.

### File Storage Settings

```python
# In backend/app/core/config.py

DATA_DIR = "data"
DATASETS_DIR = "data/datasets"
EMBEDDINGS_DIR = "data/embeddings"
MODELS_DIR = "data/models"
CODE_EXECUTIONS_DIR = "data/executions"
```

### Upload Limits

```python
MAX_UPLOAD_SIZE_MB = 100
QUERY_TIMEOUT_SECONDS = 30
MAX_QUERY_ROWS = 100000
```

### Python Execution

```python
PYTHON_EXECUTION_TIMEOUT_SECONDS = 120
PYTHON_MAX_MEMORY_MB = 1024
ENABLE_PYTHON_EXECUTION = True
```

## Frontend Configuration

Located in `frontend/src/lib/api.ts`:

```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
```

### Environment Variables

Create `frontend/.env.local`:

```bash
VITE_API_URL=http://localhost:8000
```

## Database Configuration

### PostgreSQL Setup

```sql
-- Create database
CREATE DATABASE ai_analytics;

-- Enable pgvector extension (if using)
CREATE EXTENSION vector;
```

### Connection Pool

In `backend/app/core/database.py`:

```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,        # Max connections
    max_overflow=20,      # Extra connections if needed
    pool_pre_ping=True    # Verify connections
)
```

## LLM Configuration

### Temperature Settings

Adjust in service files:

```python
# backend/app/services/nl_to_sql_service.py
"temperature": 0.0  # Deterministic SQL

# backend/app/services/nl_to_python_service.py
"temperature": 0.3  # More creative Python

# backend/app/services/deep_research_service.py
"temperature": 0.7  # Creative insights
```

### Timeout Settings

```python
# backend/app/services/nl_to_sql_service.py
async with httpx.AsyncClient(timeout=30.0) as client:

# backend/app/services/nl_to_python_service.py
async with httpx.AsyncClient(timeout=60.0) as client:

# backend/app/services/deep_research_service.py
async with httpx.AsyncClient(timeout=60.0) as client:
```

## Security Configuration

### CORS Settings

In `backend/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For production:

```python
allow_origins=[
    "https://yourdomain.com",
    "https://www.yourdomain.com"
]
```

### Allowed Packages

Python code can only import these packages:

```python
# backend/app/services/code_executor_service.py
allowed_packages = [
    'scikit-learn', 'scipy', 'statsmodels',
    'matplotlib', 'seaborn', 'xgboost',
    'lightgbm', 'prophet', 'pmdarima', 'duckdb'
]
```

## Performance Tuning

### DuckDB Configuration

```python
# In code execution
duckdb_conn = duckdb.connect(
    database=':memory:',
    config={
        'threads': 4,           # CPU cores
        'memory_limit': '1GB'   # Memory cap
    }
)
```

### Query Limits

```python
# Auto-add LIMIT to SQL queries
if 'LIMIT' not in sql.upper():
    sql += ' LIMIT 1000'
```

### Embedding Model

Change model in `backend/app/services/embedding_service.py`:

```python
self.model = SentenceTransformer('all-MiniLM-L6-v2')

# Alternatives:
# 'all-mpnet-base-v2' - More accurate, slower
# 'all-MiniLM-L12-v2' - Balanced
```

## Logging Configuration

### Log Level

```python
# backend/app/main.py
import logging

logging.basicConfig(
    level=logging.INFO,  # or DEBUG, WARNING, ERROR
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### File Logging

```python
handler = logging.FileHandler('felix.log')
handler.setLevel(logging.INFO)
logger.addHandler(handler)
```

## Deployment Configuration

### Production Settings

```bash
# backend/.env
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@prod-host:5432/ai_analytics
OPENROUTER_API_KEY=sk-or-v1-production-key
```

### Docker Configuration

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ai_analytics
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/ai_analytics
      REDIS_URL: redis://redis:6379/0

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

## Advanced Configuration

### Custom Prompts

Modify prompts in service files:

```python
# backend/app/services/nl_to_sql_service.py
def build_prompt(self, nl_query, schema, relevant_cols):
    return f"""You are a SQL expert...
    [Customize prompt here]
    """
```

### Error Retry Logic

```python
# backend/app/api/endpoints/python_analysis.py
max_retries = 2  # Change retry count
```

### Visualization Settings

```python
# In generated Python code
plt.savefig(buffer, format='png', dpi=150)  # Change DPI
```

## Configuration Precedence

1. Environment variables (`.env`)
2. Default values in `config.py`
3. Runtime overrides (API parameters)

## Best Practices

1. **Never commit `.env` files** - Use `.env.example` as template
2. **Use different keys** for dev/prod
3. **Set conservative limits** initially
4. **Enable logging** in production
5. **Monitor API costs** with OpenRouter dashboard

## Next Steps

- Review [Development Guide](./development.md)
- Check [Troubleshooting](./troubleshooting.md)
- Read [Architecture](./architecture.md)
