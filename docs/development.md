# Development Guide

Guide for developers contributing to or extending Felix.

## Development Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Git
- Code editor (VS Code recommended)

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd aispreadsheets

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
python setup_database.py

# Frontend setup
cd ../frontend
npm install
```

### Running in Development

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python run_server.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

## Project Structure

```
aispreadsheets/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/      # REST API routes
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # Business logic
│   │   └── core/               # Configuration
│   ├── tests/                  # Pytest tests
│   ├── requirements.txt
│   └── run_server.py
├── frontend/
│   ├── src/
│   │   ├── pages/              # Route components
│   │   ├── components/         # React components
│   │   ├── lib/                # Utilities
│   │   └── hooks/              # Custom hooks
│   ├── package.json
│   └── vite.config.ts
├── docs/                       # Documentation
└── data/                       # Data storage
```

## Code Style

### Python (Backend)

**Formatter**: Black

```bash
black app/ tests/
```

**Linter**: Flake8

```bash
flake8 app/ tests/
```

**Type Checking**: mypy

```bash
mypy app/
```

**Import Sorting**: isort

```bash
isort app/ tests/
```

### TypeScript (Frontend)

**Linter**: ESLint

```bash
npm run lint
```

**Formatter**: Prettier (via ESLint)

```bash
npm run lint:fix
```

## Adding Features

### 1. Adding a New API Endpoint

```python
# backend/app/api/endpoints/my_feature.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter(prefix="/my-feature", tags=["my-feature"])

@router.post("/action")
async def do_action(
    request: MyRequest,
    db: Session = Depends(get_db)
):
    # Implementation
    return {"status": "success"}
```

Register in `backend/app/main.py`:

```python
from app.api.endpoints import my_feature

app.include_router(my_feature.router, prefix="/api/v1")
```

### 2. Adding a Database Model

```python
# backend/app/models/my_model.py
from sqlalchemy import Column, String, Integer, DateTime
from app.core.database import Base
from datetime import datetime
import uuid

class MyModel(Base):
    __tablename__ = "my_models"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

Create migration:

```bash
alembic revision --autogenerate -m "Add my_model table"
alembic upgrade head
```

### 3. Adding a Frontend Component

```tsx
// frontend/src/components/my-feature/MyComponent.tsx
import { FC } from 'react'

interface MyComponentProps {
  data: any
}

export const MyComponent: FC<MyComponentProps> = ({ data }) => {
  return (
    <div className="p-4">
      {/* Component code */}
    </div>
  )
}
```

Use in page:

```tsx
import { MyComponent } from '@/components/my-feature/MyComponent'

<MyComponent data={myData} />
```

### 4. Adding an LLM Service

```python
# backend/app/services/my_llm_service.py
import httpx
from app.core.config import settings

class MyLLMService:
    async def call_llm(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )

            if response.status_code != 200:
                raise Exception(f"API error: {response.text}")

            result = response.json()
            return result['choices'][0]['message']['content']
```

## Testing

### Backend Tests

Using pytest:

```python
# backend/tests/test_nl_query.py
import pytest
from app.services.nl_to_sql_service import NLToSQLService

@pytest.mark.asyncio
async def test_nl_to_sql():
    service = NLToSQLService()
    result = await service.generate_sql(
        "Show top 10 customers",
        dataset_id="test-dataset"
    )
    assert "SELECT" in result['sql']
    assert "LIMIT" in result['sql']
```

Run tests:

```bash
pytest
pytest tests/test_nl_query.py  # Specific file
pytest -v  # Verbose
pytest --cov=app  # With coverage
```

### Frontend Tests

Using Vitest (future):

```typescript
import { render, screen } from '@testing-library/react'
import { MyComponent } from './MyComponent'

test('renders component', () => {
  render(<MyComponent data={{}} />)
  expect(screen.getByText('Expected Text')).toBeInTheDocument()
})
```

## Debugging

### Backend Debugging

**VS Code launch.json**:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true
    }
  ]
}
```

**Print Debugging**:

```python
print(f"🔍 Debug: {variable}")
print(f"🤖 LLM Response: {response}")
```

### Frontend Debugging

Browser DevTools:
- Chrome/Edge DevTools
- React Developer Tools extension
- Network tab for API calls

Console debugging:

```typescript
console.log('Debug:', data)
console.table(arrayData)
debugger;  // Breakpoint
```

## Database Migrations

### Create Migration

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "Description"

# Manual migration
alembic revision -m "Description"
```

### Apply Migration

```bash
alembic upgrade head     # Latest
alembic upgrade +1       # One step
alembic downgrade -1     # Rollback one
alembic history          # Show history
```

### Example Migration

```python
# migrations/versions/xxx_add_column.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('datasets',
        sa.Column('description', sa.String(500), nullable=True)
    )

def downgrade():
    op.drop_column('datasets', 'description')
```

## API Documentation

Felix uses FastAPI's automatic documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Document endpoints:

```python
@router.post("/analyze", summary="Analyze dataset")
async def analyze_dataset(
    dataset_id: str = Query(..., description="Dataset UUID"),
    query: str = Body(..., description="Natural language query")
):
    """
    Perform analysis on dataset using natural language.

    Returns:
        - **sql**: Generated SQL query
        - **data**: Query results
        - **execution_time_ms**: Execution time
    """
    pass
```

## Common Development Tasks

### Adding a New Query Mode

1. Add mode to enum:

```python
# backend/app/services/nl_to_python_service.py
class AnalysisMode:
    SQL = "sql"
    PYTHON = "python"
    MY_MODE = "my_mode"  # New mode
```

2. Add detection logic:

```python
def detect_mode(self, nl_query: str) -> str:
    if 'my_keyword' in nl_query.lower():
        return AnalysisMode.MY_MODE
```

3. Add prompt template:

```python
def get_mode_instructions(self, mode: str) -> str:
    if mode == AnalysisMode.MY_MODE:
        return """MODE: My Custom Mode
        Instructions here..."""
```

### Adding Visualization Support

1. Backend - return visualization data:

```python
visualizations = [{
    'data': base64_image,
    'type': 'my_chart',
    'caption': 'Chart description'
}]
```

2. Frontend - render visualization:

```tsx
{result.visualizations?.map((viz, idx) => (
  <img
    key={idx}
    src={`data:image/png;base64,${viz.data}`}
    alt={viz.caption}
  />
))}
```

### Adding ML Model Support

1. Add to allowed packages:

```python
# backend/app/services/code_executor_service.py
allowed_packages = [
    # ...existing
    'my_ml_library'
]
```

2. Add to imports:

```python
try:
    import my_ml_library
    libs['my_ml'] = my_ml_library
except ImportError:
    self._install_package('my-ml-library')
```

3. Update prompt to include usage:

```python
# Include in Python prompt
Use my_ml_library for [specific task]
```

## Performance Optimization

### Backend

**Use DuckDB for filtering**:

```python
# Instead of:
df = pd.read_parquet(path)
df = df[df['date'] > '2023-01-01']

# Do:
df = duckdb.execute("""
    SELECT * FROM read_parquet('{path}')
    WHERE date > '2023-01-01'
""").df()
```

**Cache embeddings**:

```python
# Load once, cache in memory
if not hasattr(self, '_cached_embeddings'):
    self._cached_embeddings = pickle.load(open(path, 'rb'))
```

### Frontend

**Use React Query caching**:

```typescript
const { data } = useQuery({
  queryKey: ['dataset', datasetId],
  queryFn: () => fetchDataset(datasetId),
  staleTime: 5 * 60 * 1000  // Cache 5 minutes
})
```

**Lazy load components**:

```typescript
const HeavyComponent = lazy(() => import('./HeavyComponent'))

<Suspense fallback={<Loading />}>
  <HeavyComponent />
</Suspense>
```

## Git Workflow

### Branch Naming

- `feature/add-visualization-types`
- `fix/sql-generation-bug`
- `docs/update-api-reference`
- `refactor/improve-error-handling`

### Commit Messages

```
feat: Add support for time series forecasting
fix: Resolve SQL injection vulnerability
docs: Update configuration guide
refactor: Simplify code executor service
test: Add tests for deep research
```

### Pull Request Process

1. Create feature branch
2. Make changes
3. Write tests
4. Update documentation
5. Run linters/formatters
6. Create PR with description
7. Address review comments
8. Merge when approved

## Troubleshooting Development Issues

### ImportError for packages

```bash
pip install --upgrade package-name
```

### Database connection errors

```bash
# Check PostgreSQL is running
pg_isready

# Reset database
python setup_database.py --reset
```

### Frontend build errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Docs](https://react.dev/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [TailwindCSS Docs](https://tailwindcss.com/docs)

## Next Steps

- Review [Architecture](./architecture.md)
- Check [API Reference](./api-reference.md)
- Read [Configuration](./configuration.md)
