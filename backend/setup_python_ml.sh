#!/bin/bash

# Setup script for Python/ML analytics features

echo " Setting up Python/ML Analytics Features..."

# Install Python dependencies
echo "📦 Installing Python ML libraries..."
pip install scikit-learn scipy statsmodels matplotlib seaborn

# Create required directories
echo "📁 Creating data directories..."
mkdir -p data/models
mkdir -p data/executions

# Run database migration
echo "🗄️  Running database migrations..."
if [ -f "migrations/002_add_code_execution_ml_models.sql" ]; then
    echo "Migration file found. Run manually with:"
    echo "psql -U postgres -d your_database -f migrations/002_add_code_execution_ml_models.sql"
else
    echo "⚠️  Migration file not found!"
fi

# Update .env if needed
if [ -f "../.env" ]; then
    echo "✅ .env file exists"

    # Check if Python settings are present
    if ! grep -q "PYTHON_EXECUTION_TIMEOUT_SECONDS" ../.env; then
        echo ""
        echo "Add these settings to your .env file:"
        echo "PYTHON_EXECUTION_TIMEOUT_SECONDS=120"
        echo "PYTHON_MAX_MEMORY_MB=1024"
        echo "ENABLE_PYTHON_EXECUTION=true"
    else
        echo "✅ Python execution settings already configured"
    fi
else
    echo "⚠️  .env file not found. Copy .env.example to .env first."
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with Python execution settings (if not already done)"
echo "2. Run database migration manually"
echo "3. Restart the server: python run_server.py"
echo ""
echo "📖 See PYTHON_ML_FEATURES.md for full documentation"
