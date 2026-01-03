# Setup Checklist

Quick checklist to get all new features running.

## ☑️ Prerequisites

- [ ] Python 3.9+ installed
- [ ] Node.js 16+ installed
- [ ] PostgreSQL running
- [ ] Git repository cloned

## ☑️ Backend Setup

### 1. Dependencies

```bash
cd backend
pip install celery redis python-pptx
```

- [ ] Celery installed
- [ ] Redis library installed
- [ ] python-pptx installed

### 2. Redis

**Option A: Docker (Recommended)**
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

**Option B: Local Install**
```bash
# macOS
brew install redis && redis-server

# Ubuntu
sudo apt install redis-server && sudo systemctl start redis
```

**Verify:**
```bash
redis-cli ping  # Should return: PONG
```

- [ ] Redis running
- [ ] Redis responding to ping

### 3. Environment Variables

Check `.env` file has:
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_analytics
REDIS_URL=redis://localhost:6379/0
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=google/gemini-2.5-flash
DB_SCHEMA=  # Optional: leave blank for public schema
```

- [ ] DATABASE_URL configured
- [ ] REDIS_URL configured
- [ ] OPENROUTER_API_KEY set
- [ ] DB_SCHEMA set (optional)

### 4. Database Setup

```bash
python setup_database.py
```

**Verify tables created:**
```sql
psql $DATABASE_URL -c "\dt"
```

Should see:
- [ ] datasets
- [ ] queries
- [ ] research_jobs ← **NEW**
- [ ] dataset_groups ← **NEW**
- [ ] dataset_group_memberships ← **NEW**

### 5. Test Services

**Terminal 1 - API Server:**
```bash
python run_server.py
```
- [ ] API starts on port 8000
- [ ] No errors in console
- [ ] http://localhost:8000/docs loads

**Terminal 2 - Celery Worker:**
```bash
celery -A app.core.celery_app worker --loglevel=info
```
- [ ] Worker connects to Redis
- [ ] Shows registered tasks: `run_deep_research`
- [ ] No connection errors

**Or use single command:**
```bash
./start_all.sh
```

## ☑️ Frontend Setup

### 1. Dependencies

```bash
cd frontend
npm install
```

- [ ] No errors during install

### 2. Environment

Check `.env` file:
```bash
VITE_API_URL=http://localhost:8000/api/v1
```

- [ ] API URL configured correctly

### 3. Start Dev Server

```bash
npm run dev
```

- [ ] Frontend starts (usually port 5173)
- [ ] No compilation errors
- [ ] Can access in browser

## ☑️ Feature Testing

### Test 1: Async Research Jobs

1. Navigate to a dataset
2. Enter a research question
3. Click "Run Research"
4. **Expected:**
   - [ ] Toast notification appears "Research job started"
   - [ ] Can navigate away
   - [ ] Progress updates every 2 seconds
   - [ ] Notification when complete
   - [ ] Results auto-load

### Test 2: PowerPoint Generation

1. Complete a research analysis
2. View the report
3. Click "PowerPoint" button
4. Select a theme (e.g., "Professional")
5. **Expected:**
   - [ ] Loading spinner shows
   - [ ] Toast notification appears
   - [ ] PPTX file downloads
   - [ ] File opens in PowerPoint/Google Slides

### Test 3: Research History

1. Complete 2-3 research jobs
2. Click History icon in dataset header
3. **Expected:**
   - [ ] Modal shows list of past research
   - [ ] Search works
   - [ ] Can click to view old report
   - [ ] Can delete old research

### Test 4: Horizontal Scrolling

1. Upload dataset with 15+ columns
2. View in spreadsheet
3. **Expected:**
   - [ ] Horizontal scrollbar appears
   - [ ] Can scroll left/right
   - [ ] Headers stay aligned
   - [ ] Sticky headers work

### Test 5: Notifications

1. Submit a research job
2. **Expected:**
   - [ ] Browser notification permission requested
   - [ ] In-app toast shows progress
   - [ ] Browser notification when complete
   - [ ] Can click notification to view

## ☑️ API Endpoints

Test with curl:

### Async Jobs
```bash
# Submit
curl -X POST http://localhost:8000/api/v1/deep-research/jobs/submit \
  -H "Content-Type: application/json" \
  -d '{"dataset_id":"test","question":"Test?","verbose":0}'

# Status
curl http://localhost:8000/api/v1/deep-research/jobs/{job_id}

# List
curl http://localhost:8000/api/v1/deep-research/jobs
```

- [ ] Submit returns job_id
- [ ] Status shows progress
- [ ] List returns array

### PowerPoint
```bash
curl -X POST http://localhost:8000/api/v1/deep-research/generate-presentation \
  -H "Content-Type: application/json" \
  -d '{"research_id":"test-id","theme":"modern"}'
```

- [ ] Returns success with base64 data
- [ ] File size reasonable (40-100 KB)

## ☑️ Database Schema

If using custom schema:

```bash
# Set in .env
DB_SCHEMA=myapp

# Re-run setup
python setup_database.py
```

**Verify:**
```sql
SELECT schemaname, tablename
FROM pg_tables
WHERE schemaname = 'myapp';
```

- [ ] All tables in custom schema
- [ ] API works with custom schema

## ☑️ Monitoring

### Celery Flower (Optional)

```bash
pip install flower
celery -A app.core.celery_app flower
```

Open http://localhost:5555

- [ ] Shows active workers
- [ ] Shows task history
- [ ] Shows task details

### Logs

```bash
# API logs
tail -f logs/api.log

# Celery logs
tail -f logs/celery.log
```

- [ ] Logs being written
- [ ] No errors

## ☑️ Production Readiness

### Security
- [ ] Change default passwords
- [ ] Enable HTTPS
- [ ] Set proper CORS origins
- [ ] Rotate API keys

### Performance
- [ ] Multiple Celery workers (1 per CPU core)
- [ ] Redis persistence enabled
- [ ] Database connection pooling
- [ ] API rate limiting

### Monitoring
- [ ] Health checks enabled
- [ ] Error tracking (Sentry, etc.)
- [ ] Log aggregation
- [ ] Metrics collection

### Backups
- [ ] Database backups scheduled
- [ ] Research files backed up (`data/research_jobs/`)
- [ ] Presentation files backed up (`data/presentations/`)

## ☑️ Documentation

Review these docs:

- [ ] `ASYNC_RESEARCH.md` - Async jobs guide
- [ ] `QUICKSTART_ASYNC.md` - Quick setup
- [ ] `POWERPOINT_GENERATION.md` - PowerPoint feature
- [ ] `DATABASE_SCHEMA.md` - Schema config
- [ ] `IMPLEMENTATION_SUMMARY.md` - All features

## ☑️ Troubleshooting

If issues occur, check:

1. **Jobs stuck in "pending"**
   - [ ] Celery worker running?
   - [ ] Redis accessible?
   - [ ] Database connection OK?

2. **No notifications**
   - [ ] ToastProvider wraps App?
   - [ ] Browser permissions granted?
   - [ ] Console errors?

3. **PowerPoint fails**
   - [ ] python-pptx installed?
   - [ ] Write permissions for `data/presentations/`?
   - [ ] File size reasonable?

4. **Horizontal scroll not working**
   - [ ] Clear browser cache
   - [ ] Hard refresh (Cmd+Shift+R)
   - [ ] Check element inspect

## 🎉 Success!

If all checkboxes are ✅, you're ready to go!

**Quick commands:**

```bash
# Start everything
cd backend && ./start_all.sh

# In another terminal
cd frontend && npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Flower (optional): http://localhost:5555

## 📞 Get Help

- Check logs first
- Review documentation
- Test with curl
- Check browser console
- Verify services running

Happy coding! 🚀
