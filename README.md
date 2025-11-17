# Felix - AI Analytics Platform

Felix is an intelligent data analytics platform that transforms natural language questions into powerful data insights using AI. Upload your datasets and ask questions in plain English - Felix handles the SQL, Python, and machine learning behind the scenes.

## Features

- **Natural Language Queries** - Ask questions in plain English
- **Smart Query Modes** - Auto, SQL, Python, and Deep Research modes
- **Machine Learning** - Build prediction models with simple commands
- **Interactive Visualizations** - Automatic chart generation
- **Fast Analytics** - DuckDB query engine with Parquet storage
- **Dataset Overview** - AI-powered insights about your data
- **Code Generation** - See and customize generated SQL/Python code
- **Report Export** - Download comprehensive PDF reports

## Architecture

- **Backend**: FastAPI + PostgreSQL + DuckDB
- **Frontend**: React + TypeScript + Vite + TailwindCSS
- **Storage**: Parquet files (columnar format)
- **AI**: OpenRouter (Claude, GPT-4, Gemini, and more)
- **Data Processing**: Pandas, scikit-learn, XGBoost, Prophet
- **Query Engine**: DuckDB (embedded)

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 15+
- Redis (for background jobs)

### 1. Start Infrastructure

```bash
# Start PostgreSQL and Redis
docker-compose up -d
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Run server
uvicorn app.main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend will be available at: http://localhost:5173

## Usage

1. **Upload Data**
   - Go to http://localhost:5173
   - Click "Upload Dataset" or drag and drop a CSV/Excel file
   - Wait for processing to complete

2. **Ask Questions**
   - Type natural language questions in the chat sidebar
   - Examples:
     - "Show top 10 customers by revenue"
     - "Build a prediction model for sales"
     - "Why are sales declining in Q3?" (Deep Research)
   - Felix automatically chooses SQL, Python, or Deep Research mode

3. **View Results**
   - Dashboard tab: Query results and charts
   - Code tab: Generated SQL/Python code and execution details
   - Report tab: Comprehensive Deep Research reports
   - Export reports as PDF

## Documentation

For complete documentation, see the [docs](./docs/) directory:

- [Getting Started](./docs/getting-started.md) - Installation and setup
- [User Guide](./docs/user-guide.md) - How to use Felix
- [Query Modes](./docs/query-modes.md) - Auto, SQL, Python, Deep Research
- [Python Analysis](./docs/python-analysis.md) - ML and statistics
- [API Reference](./docs/api-reference.md) - REST API documentation
- [Architecture](./docs/architecture.md) - System design
- [Troubleshooting](./docs/troubleshooting.md) - Common issues

## Project Structure

```
aispreadsheets/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/     # API routes
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   └── core/              # Config & database
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── hooks/             # Custom hooks
│   │   ├── services/          # API client
│   │   └── types/             # TypeScript types
│   └── package.json
├── data/                      # Parquet files & schemas
│   ├── datasets/
│   ├── queries/
│   └── embeddings/
└── docker-compose.yml
```

## API Endpoints

### Datasets
- `POST /api/v1/datasets/upload` - Upload CSV/XLSX
- `GET /api/v1/datasets/` - List all datasets
- `GET /api/v1/datasets/{id}` - Get dataset metadata
- `GET /api/v1/datasets/{id}/preview` - Preview data
- `GET /api/v1/datasets/{id}/schema` - Get schema with stats

### Queries
- `POST /api/v1/queries/nl` - Natural language query
- `POST /api/v1/queries/sql` - Direct SQL query
- `GET /api/v1/queries/{id}` - Get query results

### Visualizations
- `POST /api/v1/visualizations/suggest` - Get chart suggestions
- `POST /api/v1/visualizations/` - Create visualization

## Configuration

### Backend (.env)
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_analytics
REDIS_URL=redis://localhost:6379/0
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet  # or google/gemini-2.5-flash, openai/gpt-4-turbo
ENVIRONMENT=development
```

See [Configuration Guide](./docs/configuration.md) for all options.

## Development

### Run Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Code Quality
```bash
# Backend
black .
isort .
mypy app/

# Frontend
npm run lint
```

## Roadmap

- [ ] Multi-dataset joins
- [ ] Semantic metrics layer
- [ ] Auto-insights generation
- [ ] Query caching
- [ ] Warehouse promotion (Snowflake/BigQuery)
- [ ] Authentication & RBAC
- [ ] Collaborative features

## License

MIT
