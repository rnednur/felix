# Getting Started with Felix

This guide will help you set up and start using Felix for data analytics.

## Prerequisites

### Required Software
- **Python 3.9+**
- **Node.js 18+** and npm
- **PostgreSQL 14+** with pgvector extension
- **Git**

### API Keys
- **OpenRouter API Key**: Get one from [openrouter.ai](https://openrouter.ai/)
  - Felix uses OpenRouter to access various LLMs (Claude, GPT-4, Gemini, etc.)
  - You'll need credits in your OpenRouter account

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd aispreadsheets
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
```

Edit `.env` file:
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_analytics
REDIS_URL=redis://localhost:6379/0
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet
ENVIRONMENT=development
```

**Available Models**:
- `anthropic/claude-3.5-sonnet` (recommended for quality)
- `openai/gpt-4-turbo` (good balance)
- `google/gemini-2.5-flash` (fast and cheap)
- See [OpenRouter models](https://openrouter.ai/models) for full list

### 3. Database Setup

```bash
# Make sure PostgreSQL is running
# Install pgvector extension if not already installed
# psql -U postgres -c "CREATE EXTENSION vector;"

# Initialize database
python setup_database.py
```

### 4. Start Backend

```bash
# Interactive startup (recommended for first time)
./start.sh

# Or manually start API server
python run_server.py
```

The API will be available at `http://localhost:8000`

### 5. Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:5173`

## First Steps

### 1. Upload a Dataset

1. Open Felix in your browser (`http://localhost:5173`)
2. Click **Upload Dataset** or drag and drop a CSV/Excel file
3. Supported formats: CSV, Excel (.xlsx, .xls), Parquet
4. Maximum file size: 100MB

### 2. Explore Your Data

Once uploaded, you'll see:
- **Spreadsheet Tab**: View your raw data
- **Schema Tab**: Column types, statistics, and data quality info
- **Chat Sidebar**: Ask questions about your data

### 3. Ask Your First Question

Try these example queries:

**Simple Queries (SQL Mode)**:
```
Show me the first 10 rows
How many records are there?
What's the average sales by region?
Count customers by country
```

**Python Analysis**:
```
Perform exploratory data analysis
Build a prediction model for sales
Clean and transform this data
Calculate correlation between columns
```

**Deep Research**:
```
Why are sales declining in Q3?
What factors drive customer churn?
Analyze seasonal patterns in the data
```

## Query Modes

Felix automatically selects the best mode, but you can choose manually:

- **Auto Mode** (✨): Automatically picks SQL or Python based on your question
- **SQL Mode** (🗄️): Fast queries for filtering and aggregations
- **Python Mode** (🐍): Advanced analysis, ML models, statistics
- **Deep Research Mode** (🧠): Multi-stage comprehensive analysis

## Tips for Best Results

1. **Be specific**: Instead of "analyze sales", try "what are the top 5 products by revenue?"

2. **Check the Schema tab**: Know your column names and types

3. **Use Dataset Overview**: Click "Describe Dataset" to get AI insights about your data

4. **Review generated code**: Click the Code tab to see and understand the SQL/Python

5. **Start simple**: Begin with basic queries, then move to complex analyses

## Next Steps

- Read the [User Guide](./user-guide.md) for detailed features
- Learn about [Query Modes](./query-modes.md)
- Explore [Python Analysis](./python-analysis.md) for ML and statistics
- Try [Deep Research](./deep-research.md) for comprehensive insights

## Troubleshooting

### Backend won't start
- Check PostgreSQL is running: `pg_isready`
- Verify `.env` file has correct database URL
- Check logs for specific errors

### Frontend can't connect
- Ensure backend is running on port 8000
- Check browser console for errors
- Verify CORS settings in backend

### OpenRouter errors
- Verify API key is correct in `.env`
- Check you have credits in your OpenRouter account
- Try a different model if one is unavailable

See [Troubleshooting Guide](./troubleshooting.md) for more help.
