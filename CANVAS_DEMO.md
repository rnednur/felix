# 🎨 Canvas Mode Demo Guide

## Quick Start (No Database Setup Required!)

Canvas mode is now integrated into the existing Felix UI. You can enable it with a single click!

### Step 1: Start the Servers

**Backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### Step 2: Login and Open a Dataset

1. Go to http://localhost:5173
2. Login with your credentials
3. Upload a dataset or select an existing one
4. Click on the dataset to open it

### Step 3: Enable Canvas Mode

Look at the top-right of the dataset page. You'll see a button that says **"Tabs Mode"**.

Click it to switch to **"Canvas Mode"** 🎨

### Step 4: Ask Questions

The chat sidebar still works the same! Type any question:

**Examples:**
- `Show top 10 customers by revenue`
- `What's the average order value by region?`
- `Show sales trends over time`

Press Enter or click Send.

### Step 5: Watch the Magic ✨

Instead of results appearing in tabs, you'll see:

1. **SQL Code Block** appears at (100, 100) - Shows the generated SQL
2. **Results Table** appears at (750, 100) - Shows query results
3. **Chart** appears at (100, 550) - Auto-generated visualization

All items appear on a **draggable canvas** with a grid background!

### Step 6: Interact with Canvas

**Drag Items:**
- Click and hold the gray header bar at the top of any item
- Drag it to a new position
- Release to drop

**Delete Items:**
- Click the × button in the top-right corner of any item

**Save Canvas:**
- Click the "Save" button in the toolbar
- (Note: Full persistence requires database setup - see below)

### Step 7: Switch Back to Tabs

Click the **"Canvas Mode"** button again to return to traditional tabs view.

---

## Full Setup (With Database Persistence)

If you want to save canvas workspaces to the database:

### 1. Create Database Tables

```bash
cd backend
psql $DATABASE_URL -f create_workspace_tables.sql
```

Or using Alembic:
```bash
alembic revision --autogenerate -m "Add workspace tables"
alembic upgrade head
```

### 2. Restart Backend

The backend will now support workspace persistence!

---

## Features Demo

### Traditional Mode (Tabs)
- Spreadsheet: View raw data
- Schema: Column metadata
- Dashboard: Query results + charts
- Report: Deep research reports
- Code: Python execution results

### Canvas Mode
- **Spatial Organization**: Arrange items freely
- **Real-time Streaming**: Watch analysis develop
- **Multiple Items**: Show code, results, and charts together
- **Drag & Drop**: Organize your analysis visually

---

## Keyboard Shortcuts (Coming Soon)

- `Cmd/Ctrl + K` - Toggle canvas mode
- `Cmd/Ctrl + S` - Save canvas
- `Delete` - Delete selected item
- `Cmd/Ctrl + Z` - Undo

---

## Comparison

### Before (Tabs Mode)
```
Ask question → Results in Dashboard tab → Chart in Dashboard tab
```
One thing at a time, must switch tabs to see different views.

### After (Canvas Mode)
```
Ask question → Code + Results + Chart all appear on canvas
```
Everything visible at once, arrange as you like!

---

## Architecture Flow

```
User Query
    ↓
[Canvas Mode Check]
    ↓
AG-UI Stream Starts
    ↓
Backend generates SQL
    ↓
Event: canvas.item.create (code-block)
    ↓
Frontend adds item to canvas
    ↓
Backend executes SQL
    ↓
Event: canvas.item.create (query-result)
    ↓
Frontend adds item to canvas
    ↓
Backend generates chart
    ↓
Event: canvas.item.create (chart)
    ↓
Frontend adds item to canvas
    ↓
Done! 🎉
```

---

## Troubleshooting

**Canvas mode button not showing?**
- Make sure you've restarted the frontend after pulling the latest code
- Clear browser cache

**Items not appearing?**
- Open browser DevTools > Console
- Look for AG-UI event logs
- Check Network tab for SSE connection

**Backend errors?**
- Make sure sse-starlette is installed: `pip install sse-starlette`
- Check backend logs for import errors

**CORS errors?**
- Backend should allow localhost:5173
- Check CORS middleware in app/main.py

---

## What's Next?

This is a proof of concept! Future enhancements:

- **Auto-layout**: Intelligent positioning
- **Templates**: Save and reuse layouts
- **Collaboration**: Real-time multi-user editing
- **Export**: PDF/PNG of entire canvas
- **Full draggable-canvas**: Replace simple POC with full library
- **Undo/Redo**: History management
- **Keyboard shortcuts**: Power user features

---

## Demo Script for Stakeholders

1. **Show traditional mode**
   - "This is how Felix works today - tabs for different views"

2. **Enable canvas mode**
   - "Click this button to switch to canvas mode"

3. **Ask a complex question**
   - "Show me sales by region with a trend analysis"

4. **Point out the workflow**
   - "See how the SQL appears first"
   - "Then the results table"
   - "And finally the visualization"
   - "All on one canvas, arranged spatially"

5. **Drag things around**
   - "I can reorganize these however I want"
   - "Put related items near each other"
   - "Create custom dashboards"

6. **Ask another question**
   - "Now watch as I add more analysis"
   - Items keep appearing, canvas grows organically

7. **Show the vision**
   - "Imagine saving these layouts"
   - "Sharing them with your team"
   - "Building a library of analytical templates"
   - "Real-time collaboration"

---

Enjoy your new spatial analytics workspace! 🚀
