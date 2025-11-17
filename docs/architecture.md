# Felix Architecture

Technical architecture and system design of the Felix AI Analytics platform.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Felix Platform                        │
├──────────────────┬──────────────────┬──────────────────────┤
│    Frontend      │     Backend      │    Data Storage       │
│  (React + Vite)  │    (FastAPI)     │  (PostgreSQL + FS)   │
└──────────────────┴──────────────────┴──────────────────────┘
         │                  │                    │
         │                  │                    │
         ▼                  ▼                    ▼
    Web Browser      OpenRouter API        File System
                     (Claude, GPT-4,       (Parquet files)
                      Gemini, etc.)
```

## Technology Stack

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Language**: TypeScript
- **UI Components**: Radix UI
- **Styling**: TailwindCSS
- **State Management**: TanStack Query (React Query)
- **Routing**: React Router
- **HTTP Client**: Axios

### Backend
- **Framework**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL 14+ with pgvector
- **Query Engine**: DuckDB (embedded)
- **Task Queue**: Celery + Redis (optional)
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic
- **AI/LLM**: OpenRouter API

### Data Processing
- **pandas**: Data manipulation
- **DuckDB**: Fast SQL queries on Parquet
- **numpy**: Numerical operations
- **scikit-learn**: Machine learning
- **sentence-transformers**: Embeddings (all-MiniLM-L6-v2)

### Infrastructure
- **File Storage**: Local filesystem (Parquet format)
- **Embeddings**: Binary format with pickle
- **Cache**: In-memory (future: Redis)

## Architecture Layers

### 1. Presentation Layer (Frontend)

```
src/
├── pages/           # Route components
│   ├── Home.tsx              # Dataset upload
│   └── DatasetDetail.tsx     # Analysis interface
├── components/      # Reusable UI components
│   ├── chat/        # Chat sidebar
│   ├── canvas/      # Report views
│   ├── datasets/    # Dataset components
│   └── ui/          # Base UI primitives
├── lib/            # Utilities
│   └── api.ts      # API client
└── hooks/          # Custom React hooks
```

#### Key Components

**ChatSidebar**:
- Natural language input
- Conversation history
- Mode selection (Auto, SQL, Python, Deep Research)
- Quick action buttons

**DatasetDetail**:
- Tab interface (Spreadsheet, Schema, Dashboard, Report, Code)
- Query result display
- Visualization rendering
- Code execution interface

**ReportView**:
- Deep Research report rendering
- Expandable sections
- PDF export functionality
- Embedded visualizations

### 2. API Layer (Backend)

```
app/
├── api/endpoints/   # REST API endpoints
│   ├── datasets.py          # Dataset CRUD
│   ├── nl_query.py          # NL to SQL
│   ├── python_analysis.py   # Python code gen/exec
│   └── deep_research.py     # Deep research
├── models/         # Database models
│   ├── dataset.py
│   ├── code_execution.py
│   └── ml_model.py
├── schemas/        # Pydantic schemas
│   └── dataset.py
├── services/       # Business logic
│   ├── nl_to_sql_service.py
│   ├── nl_to_python_service.py
│   ├── code_executor_service.py
│   ├── deep_research_service.py
│   ├── embedding_service.py
│   └── storage_service.py
└── core/           # Core configuration
    ├── config.py
    ├── database.py
    └── security.py
```

### 3. Service Layer

#### NL to SQL Service
```python
class NLToSQLService:
    """Convert natural language to DuckDB SQL"""

    1. Load dataset schema
    2. Generate embeddings for query
    3. Find relevant columns (semantic search)
    4. Build LLM prompt with context
    5. Call OpenRouter API
    6. Parse and validate SQL
    7. Apply safety guardrails
    8. Return executable SQL
```

#### NL to Python Service
```python
class NLToPythonService:
    """Generate Python code for analysis"""

    1. Detect analysis mode (ML, stats, workflow)
    2. Load schema and embeddings
    3. Generate optimized DuckDB pre-filter
    4. Build mode-specific prompt
    5. Call OpenRouter API
    6. Parse and clean code
    7. Validate safety
    8. Return executable Python
```

#### Code Executor Service
```python
class CodeExecutorService:
    """Safely execute Python code"""

    1. Setup sandboxed environment
    2. Install required libraries
    3. Load dataset into DuckDB
    4. Execute code with timeout
    5. Extract results and visualizations
    6. Handle errors and cleanup
    7. Return structured output
```

#### Deep Research Service
```python
class DeepResearchService:
    """Multi-stage comprehensive analysis"""

    1. Decompose question into sub-questions
    2. Generate SQL/Python for each
    3. Execute analyses in parallel
    4. Collect results
    5. Synthesize findings with LLM
    6. Generate final report
    7. Create follow-up recommendations
```

#### Embedding Service
```python
class EmbeddingService:
    """Semantic search for columns"""

    1. Load sentence-transformer model
    2. Generate embeddings for columns
    3. Store embeddings (binary file)
    4. Semantic search for query
    5. Return relevant columns with scores
```

### 4. Data Layer

#### Database Schema (PostgreSQL)

```sql
-- Datasets table
CREATE TABLE datasets (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    file_type VARCHAR(10),
    row_count INTEGER,
    column_count INTEGER,
    file_size_mb NUMERIC,
    upload_status VARCHAR(50),
    created_at TIMESTAMP,
    deleted_at TIMESTAMP  -- Soft delete
);

-- Code executions table
CREATE TABLE code_executions (
    id UUID PRIMARY KEY,
    dataset_id UUID REFERENCES datasets(id),
    nl_input TEXT,
    mode VARCHAR(50),  -- sql, python, ml, stats, workflow
    generated_code TEXT,
    execution_status VARCHAR(50),
    result_summary JSONB,
    visualizations JSONB,
    error_message TEXT,
    error_trace TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- ML models table
CREATE TABLE ml_models (
    id UUID PRIMARY KEY,
    dataset_id UUID REFERENCES datasets(id),
    code_execution_id UUID REFERENCES code_executions(id),
    name VARCHAR(255),
    model_type VARCHAR(50),  -- regression, classification, clustering
    framework VARCHAR(50),   -- sklearn, xgboost, prophet
    features TEXT[],
    target_column VARCHAR(255),
    metrics JSONB,
    model_artifact_path VARCHAR(500),
    status VARCHAR(50),
    created_at TIMESTAMP
);
```

#### File Storage Structure

```
data/
├── datasets/
│   └── {dataset_id}/
│       ├── data.parquet           # Main data file
│       ├── schema.json            # Column metadata
│       └── original.csv           # Original upload
├── embeddings/
│   └── {dataset_id}_embeddings.bin  # Column embeddings
├── models/
│   └── {model_id}.pkl             # Saved ML models
└── executions/
    └── {execution_id}/
        └── outputs.json           # Execution results
```

## Data Flow

### Query Execution Flow

```
User Query
    │
    ├─ Mode Detection
    │   ├─ Auto → Analyze keywords
    │   ├─ SQL → Direct to SQL
    │   ├─ Python → Direct to Python
    │   └─ Deep Research → Multi-stage
    │
    ▼
[SQL Path]                      [Python Path]
    │                               │
    ├─ Load Schema                  ├─ Detect Mode
    ├─ Semantic Search              ├─ Load Schema
    ├─ Build Prompt                 ├─ Generate DuckDB Filter
    ├─ Call LLM                     ├─ Build Prompt
    ├─ Parse SQL                    ├─ Call LLM
    ├─ Validate                     ├─ Parse Code
    ├─ Execute (DuckDB)             ├─ Safety Check
    └─ Return Results               ├─ Execute (Sandbox)
                                    ├─ Extract Results
                                    └─ Return Results
```

### Deep Research Flow

```
Complex Question
    │
    ├─ Question Decomposition (LLM)
    │   └─ Generate 5-15 sub-questions
    │
    ├─ Analysis Planning
    │   ├─ Classify each (SQL vs Python)
    │   └─ Prioritize execution order
    │
    ├─ Parallel Execution
    │   ├─ Execute SQL queries
    │   ├─ Execute Python analyses
    │   └─ Collect results
    │
    ├─ Result Synthesis (LLM)
    │   ├─ Analyze all findings
    │   ├─ Identify patterns
    │   └─ Draw conclusions
    │
    └─ Report Generation
        ├─ Executive summary
        ├─ Key findings
        ├─ Visualizations
        └─ Follow-up questions
```

## Security Architecture

### Sandboxing

Python code execution is sandboxed:

```python
# Restricted builtins (no file I/O, no system calls)
safe_builtins = {
    'abs', 'all', 'any', 'bool', 'dict', 'enumerate',
    'filter', 'float', 'int', 'len', 'list', 'map',
    'max', 'min', 'print', 'range', 'set', 'sorted',
    'str', 'sum', 'tuple', 'zip'
    # Explicitly excludes: open, eval, exec, __import__
}

# Allowed imports only
allowed_packages = [
    'pandas', 'numpy', 'scikit-learn', 'scipy',
    'statsmodels', 'matplotlib', 'seaborn',
    'xgboost', 'lightgbm', 'prophet', 'duckdb'
]

# Execution timeout: 120 seconds max
# Memory limit: 1GB max
```

### SQL Injection Prevention

```python
# All SQL generated by LLM, not user input
# DuckDB with parameterized queries
# Read-only access to data
# No DROP, DELETE, UPDATE allowed
# Automatic LIMIT 1000 added
```

### Data Privacy

- Datasets stored locally (not sent to external services)
- Only schema/column names sent to LLM
- No actual data rows sent to LLM
- Soft delete for datasets (can be recovered)

## Performance Optimizations

### 1. DuckDB for Fast Queries

```python
# Instead of loading full dataset into pandas:
df = pd.read_parquet('data.parquet')  # Slow

# Use DuckDB for filtered loading:
df = duckdb.execute("""
    SELECT col1, col2, col3
    FROM read_parquet('data.parquet')
    WHERE date >= '2023-01-01'
    LIMIT 10000
""").df()  # Much faster!
```

### 2. Columnar Storage (Parquet)

- Compressed file format
- Only read needed columns
- 10-100x smaller than CSV
- Fast filtering and aggregation

### 3. Semantic Search Caching

```python
# Embeddings generated once at upload
# Cached in binary file for reuse
# Similarity search in milliseconds
```

### 4. Parallel Execution

Deep Research runs queries in parallel:
```python
import asyncio

# Run up to 5 queries concurrently
results = await asyncio.gather(*[
    execute_query(q) for q in queries
])
```

## Scalability Considerations

### Current Architecture

- Single server deployment
- In-process query execution
- File-based storage
- Suitable for: < 100 concurrent users, < 1000 datasets

### Scaling Strategies

**Horizontal Scaling**:
```
Load Balancer
    │
    ├─ API Server 1
    ├─ API Server 2
    └─ API Server 3
         │
         └─ Shared PostgreSQL + Redis
```

**Async Processing**:
```
Web Server → Redis Queue → Celery Workers
    │                           │
    └───────────────────────────┘
           (via PostgreSQL)
```

**Cloud Storage**:
```
Local Storage → S3/GCS/Azure Blob
```

## Deployment Architecture

### Development

```
┌────────────────┐    ┌────────────────┐
│   Frontend     │    │    Backend     │
│  localhost:    │───▶│  localhost:    │
│     5173       │    │     8000       │
└────────────────┘    └────────────────┘
                            │
                            ▼
                      PostgreSQL
                     (localhost:5432)
```

### Production (Future)

```
               ┌──────────────┐
               │   Nginx/     │
               │  CloudFlare  │
               └──────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
    ┌────────┐              ┌──────────┐
    │ Static │              │  API     │
    │ Files  │              │ Servers  │
    │ (CDN)  │              │ (Docker) │
    └────────┘              └──────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 │                │                │
           ┌──────────┐    ┌──────────┐    ┌──────────┐
           │PostgreSQL│    │  Redis   │    │  S3/     │
           │(RDS/Cloud│    │ (Cache)  │    │  Blob    │
           │ SQL)     │    │          │    │ Storage  │
           └──────────┘    └──────────┘    └──────────┘
```

## Error Handling

### Multi-Layer Error Recovery

```
1. Client-side validation
   └─ Error: Display to user

2. API validation (Pydantic)
   └─ Error: 422 Unprocessable Entity

3. Business logic validation
   └─ Error: 400 Bad Request

4. Code execution error
   ├─ Pattern-based fix
   ├─ LLM-based fix (if pattern fails)
   └─ Report error to user

5. Infrastructure error
   └─ 500 Internal Server Error (logged)
```

## Monitoring and Observability

### Logging

```python
# Structured logging
import logging

logger.info("Query executed", extra={
    "dataset_id": dataset_id,
    "execution_time_ms": exec_time,
    "mode": "sql"
})
```

### Metrics (Future)

- Query execution times
- LLM API latency
- Error rates
- Dataset sizes
- User activity

### Tracing (Future)

OpenTelemetry integration for distributed tracing.

## Next Steps

- Review [Configuration](./configuration.md) for setup options
- Check [Development](./development.md) for contributing
- Read [API Reference](./api-reference.md) for integration
