# Troubleshooting Guide

Common issues and solutions for Felix.

## Installation Issues

### Python Virtual Environment

**Problem**: `python -m venv venv` fails

**Solution**:
```bash
# Install python3-venv
sudo apt-get install python3-venv  # Ubuntu/Debian
brew install python  # macOS

# Or use virtualenv
pip install virtualenv
virtualenv venv
```

### PostgreSQL Connection

**Problem**: `FATAL: password authentication failed`

**Solutions**:
```bash
# 1. Check PostgreSQL is running
pg_isready

# 2. Verify credentials in .env
DATABASE_URL=postgresql://USERNAME:PASSWORD@localhost:5432/ai_analytics

# 3. Reset PostgreSQL password
sudo -u postgres psql
ALTER USER postgres PASSWORD 'newpassword';

# 4. Check pg_hba.conf authentication method
# Should have: local all postgres md5
```

### pgvector Extension

**Problem**: `ERROR: extension "vector" does not exist`

**Solution**:
```bash
# Install pgvector
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Enable in database
psql -U postgres -d ai_analytics
CREATE EXTENSION vector;
```

### Node Modules

**Problem**: `npm install` fails or takes too long

**Solution**:
```bash
# Clear npm cache
npm cache clean --force

# Delete lock file and node_modules
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Try with legacy peer deps if still failing
npm install --legacy-peer-deps
```

## Runtime Issues

### Backend Won't Start

**Problem**: `Address already in use`

**Solution**:
```bash
# Find process on port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
uvicorn app.main:app --port 8001
```

**Problem**: `ModuleNotFoundError`

**Solution**:
```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
which python  # Should point to venv
```

### Frontend Won't Start

**Problem**: `ECONNREFUSED localhost:8000`

**Solution**:
1. Ensure backend is running: `http://localhost:8000/docs`
2. Check frontend `.env.local` has correct API URL
3. Verify CORS settings in backend allow `localhost:5173`

**Problem**: Build fails with memory error

**Solution**:
```bash
# Increase Node memory limit
NODE_OPTIONS=--max_old_space_size=4096 npm run build
```

## Query Issues

### SQL Generation Errors

**Problem**: "Parser Error: syntax error at or near..."

**Causes & Solutions**:

1. **Backticks instead of quotes**:
   - Felix generates DuckDB SQL (uses `"column"`)
   - Check logs for generated SQL
   - May need to regenerate with better prompt

2. **Column name doesn't exist**:
   - Check Schema tab for exact column names
   - Case-sensitive matching
   - Include column name in query: "Show sales from revenue column"

3. **Date format issues**:
   - Felix expects: MM/DD/YYYY HH:MM:SS AM/PM
   - Verify in Spreadsheet tab
   - May need to pre-process dates in Excel

**Problem**: Query returns no results

**Solution**:
```
1. Check filter conditions are valid
2. Verify data exists: "Count all rows"
3. Review generated SQL in logs
4. Try broader query first
```

### Python Execution Errors

**Problem**: "Failed to generate Python code"

**Causes**:

1. **OpenRouter out of credits**:
   - Check OpenRouter dashboard
   - Add credits or change payment method
   - Verify API key in `.env`

2. **Model unavailable**:
   - Check OpenRouter status page
   - Try different model: `OPENROUTER_MODEL=google/gemini-2.5-flash`
   - See logs for actual error

**Problem**: Code execution times out

**Solution**:
```python
# Increase timeout in config.py
PYTHON_EXECUTION_TIMEOUT_SECONDS = 180  # 3 minutes

# Or reduce dataset size in query:
"Analyze first 10000 rows"
"Sample 5000 random records"
```

**Problem**: "Module 'prophet' has no attribute..."

**Solution**:
```bash
# Reinstall prophet
pip uninstall prophet
pip install prophet

# Or use pmdarima instead
pip install pmdarima
```

### Deep Research Issues

**Problem**: Deep Research takes too long

**Solutions**:
1. Be more specific in question
2. Use smaller dataset (< 10k rows)
3. Monitor progress in console logs
4. Maximum time is 5 minutes

**Problem**: "Insufficient data for analysis"

**Solution**:
- Need at least 1000 rows
- Need multiple columns (> 3)
- Need time-based data for trends
- Try simpler question first

## Data Upload Issues

### File Format Errors

**Problem**: "Unable to parse CSV"

**Solutions**:
```
1. Check file encoding (should be UTF-8)
2. Verify CSV has headers
3. Ensure no special characters in column names
4. Try Excel format instead
5. Check for embedded quotes/commas
```

**Problem**: "File too large"

**Solutions**:
```
1. Current limit: 100MB
2. Compress to Parquet first
3. Filter data in Excel before upload
4. Split into multiple datasets
5. Remove unnecessary columns
```

**Problem**: Date columns not recognized

**Solution**:
```
1. Format dates in Excel: MM/DD/YYYY HH:MM:SS AM/PM
2. Ensure consistent format across all rows
3. Or use YYYY-MM-DD format
4. Check Schema tab after upload
```

## Performance Issues

### Slow Query Execution

**Problem**: SQL queries take > 10 seconds

**Solutions**:
```
1. Add LIMIT: "Show first 1000 records"
2. Filter early: "Sales in 2023"
3. Use specific columns: "Show id and revenue"
4. Check dataset size (should be < 1M rows)
```

**Problem**: Python analysis is very slow

**Solutions**:
```python
# Use DuckDB filtering in generated code
df = duckdb_conn.execute("""
    SELECT * FROM dataset
    WHERE condition
    LIMIT 10000
""").df()

# Instead of:
df = pd.read_parquet(path)  # Loads everything
```

### Memory Issues

**Problem**: "MemoryError" or browser crashes

**Solutions**:
```
1. Close other tabs
2. Reduce dataset size
3. Use filters in queries
4. Increase backend memory limit
5. Clear browser cache
```

## Visualization Issues

### Charts Not Displaying

**Problem**: Visualizations show as empty

**Checks**:
1. Open browser DevTools > Console
2. Look for image loading errors
3. Check Network tab for failed requests
4. Verify base64 data is present

**Solution**:
```python
# Ensure code uses correct format:
result = {
    'visualizations': [
        {
            'data': base64_string,  # NOT 'base64'
            'caption': 'Chart title'
        }
    ]
}
```

**Problem**: PDF export is blank

**Solution**:
1. Wait for visualizations to load
2. Try Chrome instead of Firefox
3. Use Print > Save as PDF instead of Download button
4. Check browser's print preview first

## Error Messages

### "OpenRouter API error (status 401)"

**Cause**: Invalid API key

**Solution**:
```bash
# Check .env file
OPENROUTER_API_KEY=sk-or-v1-...

# Verify key at openrouter.ai
# Create new key if needed
# Restart backend after changing
```

### "OpenRouter API error (status 402)"

**Cause**: Insufficient credits

**Solution**:
1. Go to openrouter.ai
2. Add credits to account
3. Or switch to free model:
   ```bash
   OPENROUTER_MODEL=google/gemini-2.5-flash
   ```

### "OpenRouter API error (status 429)"

**Cause**: Rate limit exceeded

**Solution**:
- Wait 60 seconds
- Use cheaper/faster model
- Reduce concurrent requests

### "Execution exceeded 120 seconds"

**Cause**: Code timeout

**Solutions**:
```
1. Reduce dataset size
2. Simplify analysis
3. Increase timeout in config
4. Check for infinite loops in code
```

## Browser Issues

### Layout Problems

**Problem**: UI looks broken

**Solutions**:
```
1. Hard refresh: Ctrl+Shift+R (Windows) / Cmd+Shift+R (Mac)
2. Clear browser cache
3. Try different browser (Chrome recommended)
4. Check browser zoom (should be 100%)
5. Update browser to latest version
```

### Chat Not Working

**Problem**: Messages don't send

**Checks**:
1. Open DevTools > Network tab
2. Look for failed POST requests
3. Check Console for JavaScript errors

**Solutions**:
```
1. Ensure backend is running
2. Check CORS errors in console
3. Verify API URL in frontend/.env.local
4. Clear browser cache and cookies
```

## Database Issues

### Migration Errors

**Problem**: `alembic upgrade` fails

**Solution**:
```bash
# Check current version
alembic current

# Force to specific version
alembic stamp head

# Reset and recreate
python setup_database.py --reset
alembic upgrade head
```

**Problem**: Duplicate key error

**Solution**:
```sql
-- Find duplicates
SELECT id, COUNT(*) FROM datasets GROUP BY id HAVING COUNT(*) > 1;

-- Delete duplicates
DELETE FROM datasets WHERE ctid NOT IN (
    SELECT MIN(ctid) FROM datasets GROUP BY id
);
```

## Development Issues

### Tests Failing

**Problem**: pytest fails

**Solutions**:
```bash
# Ensure test database exists
createdb ai_analytics_test

# Set test environment
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_analytics_test

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_specific.py::test_function -v
```

### Import Errors in IDE

**Problem**: VS Code shows import errors

**Solution**:
```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "python.analysis.extraPaths": ["./backend"]
}
```

## Getting Help

If issues persist:

1. **Check logs**:
   - Backend: Terminal running `python run_server.py`
   - Frontend: Browser DevTools > Console
   - Database: PostgreSQL logs

2. **Enable debug mode**:
   ```bash
   # Backend
   export DEBUG=True
   python run_server.py

   # Check detailed logs
   ```

3. **Minimal reproduction**:
   - Note exact steps to reproduce
   - Include error message
   - Share relevant logs

4. **Create issue**:
   - GitHub Issues with template
   - Include environment details
   - Provide sample data if possible

## Common Error Reference

| Error | Likely Cause | Solution |
|-------|--------------|----------|
| 401 Unauthorized | Invalid API key | Check OPENROUTER_API_KEY |
| 402 Payment Required | No credits | Add credits to OpenRouter |
| 404 Not Found | Dataset deleted | Re-upload dataset |
| 422 Validation Error | Invalid request | Check request format |
| 500 Internal Server Error | Backend crash | Check backend logs |
| Connection refused | Backend not running | Start backend server |
| CORS error | Frontend/backend mismatch | Check CORS settings |

## Next Steps

- Review [Configuration](./configuration.md) for settings
- Check [Development Guide](./development.md) for debugging
- Read [Architecture](./architecture.md) for system understanding
