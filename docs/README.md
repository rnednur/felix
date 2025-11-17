# Felix - AI Analytics Platform

**Felix** is an intelligent data analytics platform that transforms natural language questions into powerful data insights. Upload your datasets and ask questions in plain English - Felix handles the SQL, Python, and machine learning behind the scenes.

## 🌟 Key Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **Smart Query Modes**:
  - **Auto Mode**: Automatically chooses the best approach (SQL or Python)
  - **SQL Mode**: Fast queries for filtering, aggregating, and exploring data
  - **Python Mode**: Advanced transformations, statistical analysis, and data cleaning
  - **Deep Research Mode**: Multi-stage analysis with comprehensive reports
- **Machine Learning**: Build prediction models with simple commands like "predict sales by region"
- **Interactive Visualizations**: Automatic chart generation and data exploration
- **Dataset Overview**: AI-powered insights about your data structure and quality
- **Code Generation**: See and customize the generated SQL/Python code
- **Report Export**: Download comprehensive PDF reports of deep research analyses

## 📋 Table of Contents

1. [Getting Started](./getting-started.md)
2. [User Guide](./user-guide.md)
3. [Query Modes](./query-modes.md)
4. [Python Analysis](./python-analysis.md)
5. [Deep Research](./deep-research.md)
6. [API Reference](./api-reference.md)
7. [Architecture](./architecture.md)
8. [Configuration](./configuration.md)
9. [Development](./development.md)
10. [Troubleshooting](./troubleshooting.md)

## 🚀 Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd aispreadsheets

# Setup backend
cd backend
cp .env.example .env
# Edit .env with your API keys
python setup_database.py
./start.sh

# Setup frontend (in new terminal)
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to start using Felix!

## 💡 Example Queries

- "Show me the top 10 customers by total revenue"
- "What's the average order value by region?"
- "Build a prediction model to forecast next month's sales"
- "Perform exploratory data analysis on this dataset"
- "Why are sales declining in Q3?" (Deep Research mode)

## 🏗️ Architecture

Felix consists of:
- **Frontend**: React + TypeScript + Vite
- **Backend**: FastAPI + PostgreSQL + DuckDB
- **AI**: OpenRouter (supports Claude, GPT-4, Gemini, and more)
- **Data Processing**: Pandas, DuckDB for fast analytics
- **ML**: scikit-learn, XGBoost, Prophet for predictions

## 📝 License

[Add your license here]

## 🤝 Contributing

Contributions are welcome! Please read our [Development Guide](./development.md) for details.

## 📧 Support

For issues and questions, please [open an issue](https://github.com/yourrepo/issues) on GitHub.
