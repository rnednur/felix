# AG-UI + Draggable Canvas Integration - Proof of Concept

## Overview

This proof of concept integrates AG-UI protocol and your draggable-canvas library into Felix (AI Analytics Platform) to create an interactive, spatial analytics workspace. Instead of traditional chat + tabs, users can now arrange analysis components freely on a canvas while AI streams results in real-time.

## What We Built

### Backend (Python/FastAPI)

#### 1. Database Models (`backend/app/models/workspace.py`)
- **Workspace**: Container for canvas items
  - Links to datasets or dataset groups
  - Owned by users
  - Soft delete support
- **CanvasItem**: Individual items on canvas
  - Flexible JSONB content field
  - Position (x, y, width, height, z-index)
  - Types: query-result, chart, code-block, insight-note, ml-model

#### 2. API Endpoints (`backend/app/api/endpoints/workspaces.py`)
- `GET /api/v1/workspaces` - List user workspaces
- `POST /api/v1/workspaces` - Create workspace
- `GET /api/v1/workspaces/{id}` - Get workspace with items
- `PUT /api/v1/workspaces/{id}` - Update workspace
- `DELETE /api/v1/workspaces/{id}` - Soft delete workspace
- `POST /api/v1/workspaces/{id}/items` - Add canvas item
- `PUT /api/v1/workspaces/{id}/items/{id}` - Update canvas item
- `DELETE /api/v1/workspaces/{id}/items/{id}` - Delete canvas item

#### 3. AG-UI Streaming (`backend/app/api/endpoints/canvas_stream.py`)
- `POST /api/v1/canvas/stream` - SSE endpoint for AI interactions
- Streams AG-UI protocol events:
  - `agent.thinking` - AI is analyzing
  - `agent.tool.use` - AI is using a tool (SQL generator, executor, chart generator)
  - `agent.tool.result` - Tool execution result
  - `canvas.item.create` - Create new canvas item
  - `agent.complete` - Stream finished
  - `error` - Error occurred

**Event Flow Example:**
```
1. agent.thinking → "Analyzing your question..."
2. agent.tool.use → { tool: "sql_generator" }
3. canvas.item.create → Code block with SQL
4. agent.tool.result → SQL generation complete
5. agent.tool.use → { tool: "sql_executor" }
6. canvas.item.create → Query results table
7. canvas.item.create → Visualization chart
8. agent.complete → Done!
```

### Frontend (React/TypeScript)

#### 1. Type Definitions (`frontend/src/types/canvas.ts`)
- Canvas item content types (QueryResult, Chart, CodeBlock, InsightNote, MLModel)
- Workspace and CanvasItem interfaces
- AG-UI event types

#### 2. Canvas Item Renderers
- **QueryResultItem** - Tables with pagination
- **ChartItem** - Vega visualizations
- **CodeBlockItem** - Syntax-highlighted code
- **InsightNoteItem** - Markdown notes with AI badge

#### 3. Canvas Workspace (`frontend/src/components/canvas/CanvasWorkspace.tsx`)
- Drag-and-drop canvas with grid background
- Toolbar with save/export actions
- Simplified draggable items (proof of concept)
- *Note: In production, replace with full `@rnednur/draggable-canvas` implementation*

#### 4. AG-UI Client Hook (`frontend/src/hooks/useAGUIStream.ts`)
- Connects to SSE endpoint
- Handles AG-UI events
- Creates canvas items from stream events
- Manages streaming state

#### 5. Workspace Page (`frontend/src/pages/WorkspaceDetail.tsx`)
- Full workspace UI with chat sidebar
- Integrates AG-UI streaming
- Saves canvas state to backend
- Uses existing DataWorkspaceLayout

## How It Works

### User Flow

1. **Create Workspace**
   ```
   POST /api/v1/workspaces
   { name: "Sales Analysis", dataset_id: "xyz" }
   ```

2. **Ask Question in Chat**
   - User types: "Show top 10 customers by revenue"
   - Frontend calls: `POST /api/v1/canvas/stream`
   - SSE connection opens

3. **AI Streams Response**
   ```
   Event: agent.thinking
   Data: { status: "Analyzing..." }

   Event: canvas.item.create
   Data: { itemType: "code-block", position: {x:100, y:100}, content: {...} }

   Event: canvas.item.create
   Data: { itemType: "query-result", position: {x:750, y:100}, content: {...} }

   Event: canvas.item.create
   Data: { itemType: "chart", position: {x:100, y:550}, content: {...} }

   Event: agent.complete
   ```

4. **Items Appear on Canvas**
   - Code block appears at (100, 100)
   - Results table at (750, 100)
   - Bar chart at (100, 550)

5. **User Arranges Items**
   - Drag items to desired positions
   - Resize as needed
   - Delete unwanted items

6. **Save Workspace**
   - Click "Save" button
   - Items persisted to database with positions

## Dependencies Installed

### Frontend
```json
{
  "eventsource": "^4.1.0",
  "react-markdown": "^10.1.0",
  "rehype-raw": "^7.0.0",
  "remark-gfm": "^4.0.1",
  "@rnednur/draggable-canvas": "file:../../draggable-canvas"
}
```

### Backend
```
sse-starlette==3.0.3
```

## Next Steps to Complete Implementation

### 1. Database Migration
```bash
cd backend
# Create Alembic migration for Workspace and CanvasItem tables
alembic revision --autogenerate -m "Add workspace and canvas_item tables"
alembic upgrade head
```

### 2. Replace Simplified Canvas with Full draggable-canvas
In `CanvasWorkspace.tsx`, replace `SimpleDraggableItem` with:
```typescript
import { DraggableItem } from '@rnednur/draggable-canvas'
```

### 3. Add Authentication Headers
Update `useAGUIStream.ts` to include auth token:
```typescript
const eventSource = new EventSource(url, {
  headers: {
    Authorization: `Bearer ${token}`
  }
})
```

### 4. Fix SSE POST Request
EventSource only supports GET. Options:
- Use fetch() with ReadableStream for POST
- Or convert stream endpoint to accept query params (current approach)
- Or use WebSockets instead of SSE

### 5. Add Workspace Management UI
Create page to:
- List all workspaces
- Create new workspace
- Select dataset/group for workspace
- Navigate to WorkspaceDetail

### 6. Enhanced Features
- **Auto-layout**: Automatically position items intelligently
- **Templates**: Save canvas arrangements as reusable templates
- **Collaboration**: Real-time collaborative editing
- **Export**: PDF/PNG export of entire canvas
- **Sharing**: Share workspaces with team members

## File Structure

```
backend/
├── app/
│   ├── api/endpoints/
│   │   ├── workspaces.py          # Workspace CRUD endpoints
│   │   └── canvas_stream.py       # AG-UI SSE streaming
│   ├── models/
│   │   └── workspace.py           # Workspace & CanvasItem models
│   └── schemas/
│       └── workspace.py           # Pydantic schemas

frontend/
├── src/
│   ├── components/canvas/
│   │   ├── CanvasWorkspace.tsx    # Main canvas component
│   │   ├── QueryResultItem.tsx    # Query result renderer
│   │   ├── ChartItem.tsx          # Chart renderer
│   │   ├── CodeBlockItem.tsx      # Code block renderer
│   │   └── InsightNoteItem.tsx    # Insight note renderer
│   ├── hooks/
│   │   └── useAGUIStream.ts       # AG-UI client hook
│   ├── pages/
│   │   └── WorkspaceDetail.tsx    # Workspace page
│   └── types/
│       └── canvas.ts              # TypeScript definitions

docs/
├── ag-ui-canvas-integration.md    # Integration plan
└── CANVAS_INTEGRATION.md          # This file
```

## Testing the Integration

### 1. Start Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 2. Create Database Tables
```bash
# Run migration or create tables manually in PostgreSQL
```

### 3. Start Frontend
```bash
cd frontend
npm run dev
```

### 4. Test Flow
1. Login to Felix
2. Navigate to `/workspaces/test-workspace-id`
3. Type query in chat
4. Watch items appear on canvas
5. Drag items around
6. Click "Save"

## Architecture Diagram

```
┌────────────────────────────────────────────────────────┐
│                   Felix Frontend                       │
│  ┌──────────────┐              ┌──────────────────┐  │
│  │  Chat        │              │  Canvas          │  │
│  │  Sidebar     │              │  Workspace       │  │
│  │              │              │                  │  │
│  │  [Query]     │─────────────▶│  ┌──┐  ┌──┐    │  │
│  │              │  AG-UI       │  │  │  │  │    │  │
│  │  [Send]      │  Events      │  └──┘  └──┘    │  │
│  └──────────────┘              └──────────────────┘  │
└────────────────────────────────────────────────────────┘
                       │
                       │ SSE Stream
                       ▼
┌────────────────────────────────────────────────────────┐
│                   Felix Backend                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │  /api/v1/canvas/stream                           │ │
│  │  - Generate SQL                                  │ │
│  │  - Execute query                                 │ │
│  │  - Create visualizations                        │ │
│  │  - Stream AG-UI events                          │ │
│  └──────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────┐ │
│  │  /api/v1/workspaces                              │ │
│  │  - CRUD operations                               │ │
│  │  - Item management                               │ │
│  └──────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │   PostgreSQL   │
              │  - workspaces  │
              │  - canvas_items│
              └────────────────┘
```

## Benefits of This Approach

1. **Spatial Organization**: Users naturally arrange related analysis
2. **Real-time Streaming**: See analysis develop progressively
3. **Reusability**: Save and share workspace layouts
4. **Flexibility**: Mix SQL, Python, charts, notes on one canvas
5. **Discoverability**: Visual representation of analysis flow
6. **Collaboration**: Foundation for multi-user workspaces

## Known Limitations (POC)

- SimpleDraggableItem is basic - needs full draggable-canvas integration
- No auto-layout algorithm yet
- SSE uses GET instead of POST (needs WebSocket or fetch stream)
- No workspace list/creation UI
- No real-time collaboration
- Limited error handling
- No undo/redo
- No export functionality

## Production Checklist

- [ ] Create Alembic migration
- [ ] Integrate full `@rnednur/draggable-canvas`
- [ ] Add workspace management UI
- [ ] Implement auto-layout
- [ ] Add export (PDF/PNG)
- [ ] Real-time collaboration with WebSockets
- [ ] Comprehensive error handling
- [ ] Loading states and optimistic updates
- [ ] Keyboard shortcuts
- [ ] Mobile responsive design
- [ ] Performance optimization for large canvases
- [ ] Analytics and usage tracking

## Conclusion

This proof of concept demonstrates a powerful new paradigm for data analytics UX. By combining AG-UI's streaming protocol with spatial canvas organization, Felix transforms from a traditional chat interface into an interactive workspace where analysis components can be freely arranged and composed.

The integration leverages your existing draggable-canvas library and follows AG-UI standards, making it extensible and compatible with future agent protocols.
