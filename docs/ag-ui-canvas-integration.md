# AG-UI + Draggable Canvas Integration Plan

## Overview
Integrate AG-UI protocol and draggable-canvas library to transform Felix from a traditional chat + tabs interface into an interactive, spatial analytics workspace.

## Architecture

### Frontend Stack
- **draggable-canvas**: Spatial layout for analysis components
- **AG-UI Client**: Event-based streaming protocol for AI interactions
- **React + TypeScript**: Existing Felix frontend
- **TailwindCSS**: Styling (compatible with shadcn/ui)

### Backend Stack
- **FastAPI**: SSE (Server-Sent Events) endpoint for AG-UI streaming
- **PostgreSQL**: Canvas workspace persistence
- **Existing Services**: Query engine, LLM adapter, visualization generator

## Component Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Felix Application                     │
├─────────────────────────────────────────────────────────┤
│  Chat Sidebar          │  Canvas Workspace              │
│  - NL Query Input      │  ┌──────────┐  ┌──────────┐  │
│  - Quick Actions       │  │ Query    │  │ Chart    │  │
│  - History             │  │ Result   │  │          │  │
│                        │  └──────────┘  └──────────┘  │
│                        │  ┌──────────┐  ┌──────────┐  │
│                        │  │ Insight  │  │ Code     │  │
│                        │  │ Note     │  │ Block    │  │
│                        │  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────┘
         │                         │
         │ AG-UI Events            │ Canvas State
         ▼                         ▼
┌─────────────────────────────────────────────────────────┐
│                    Backend Services                      │
├─────────────────────────────────────────────────────────┤
│  /api/v1/canvas/stream (SSE)                            │
│  /api/v1/workspaces (CRUD)                              │
│  Query Engine │ LLM Service │ Visualization │ ML        │
└─────────────────────────────────────────────────────────┘
```

## Canvas Item Types

### 1. QueryResultItem
```typescript
{
  type: 'query-result',
  queryId: string,
  columns: string[],
  rows: any[],
  sql: string,
  executionTime: number
}
```

### 2. ChartItem
```typescript
{
  type: 'chart',
  chartType: 'bar' | 'line' | 'scatter' | 'pie',
  vegaSpec: any,
  title: string,
  sourceQueryId?: string
}
```

### 3. InsightNoteItem
```typescript
{
  type: 'insight-note',
  content: string, // Markdown
  aiGenerated: boolean,
  tags: string[]
}
```

### 4. CodeBlockItem
```typescript
{
  type: 'code-block',
  language: 'sql' | 'python',
  code: string,
  editable: boolean,
  executionResult?: any
}
```

### 5. MLModelItem
```typescript
{
  type: 'ml-model',
  modelId: string,
  modelType: string,
  metrics: Record<string, number>,
  features: string[],
  predictions?: any[]
}
```

## AG-UI Event Flow

### Query Execution with AG-UI Streaming

```typescript
// User asks: "Show top 10 customers by revenue"

// 1. Frontend sends to backend
POST /api/v1/canvas/stream
{
  workspaceId: 'workspace-123',
  message: 'Show top 10 customers by revenue'
}

// 2. Backend streams AG-UI events
event: agent.thinking
data: { status: "Analyzing query..." }

event: agent.tool.use
data: { tool: "sql_generator", input: {...} }

event: canvas.item.create
data: {
  itemType: "code-block",
  position: { x: 100, y: 100 },
  content: { language: "sql", code: "SELECT..." }
}

event: agent.tool.result
data: { tool: "sql_executor", result: {...} }

event: canvas.item.create
data: {
  itemType: "query-result",
  position: { x: 350, y: 100 },
  content: { columns: [...], rows: [...] }
}

event: canvas.item.create
data: {
  itemType: "chart",
  position: { x: 100, y: 400 },
  content: { chartType: "bar", vegaSpec: {...} }
}

event: agent.complete
data: { summary: "Created visualization of top customers" }
```

## Database Schema

### Workspace Table
```sql
CREATE TABLE workspaces (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES users(id),
    dataset_id UUID REFERENCES datasets(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);
```

### Canvas Items Table
```sql
CREATE TABLE canvas_items (
    id UUID PRIMARY KEY,
    workspace_id UUID REFERENCES workspaces(id),
    type VARCHAR(50) NOT NULL,
    x INTEGER NOT NULL,
    y INTEGER NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    z_index INTEGER DEFAULT 0,
    content JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Implementation Phases

### Phase 1: Foundation (Current)
- [x] Research AG-UI and draggable-canvas
- [ ] Install dependencies
- [ ] Create database models
- [ ] Create basic API endpoints

### Phase 2: Canvas UI
- [ ] Build CanvasWorkspace component
- [ ] Create custom item renderers
- [ ] Add drag/resize/delete functionality
- [ ] Implement toolbar and controls

### Phase 3: AG-UI Integration
- [ ] SSE endpoint for event streaming
- [ ] Connect chat to AG-UI backend
- [ ] Map query execution to canvas item creation
- [ ] Handle real-time item updates

### Phase 4: Advanced Features
- [ ] Auto-layout algorithms
- [ ] Canvas templates
- [ ] Collaborative editing
- [ ] Export to PDF/image
- [ ] Workspace sharing

## API Endpoints

### Canvas Workspaces
- `GET /api/v1/workspaces` - List user workspaces
- `POST /api/v1/workspaces` - Create workspace
- `GET /api/v1/workspaces/{id}` - Get workspace with items
- `PUT /api/v1/workspaces/{id}` - Update workspace
- `DELETE /api/v1/workspaces/{id}` - Delete workspace

### Canvas Items
- `POST /api/v1/workspaces/{id}/items` - Add item to canvas
- `PUT /api/v1/workspaces/{id}/items/{itemId}` - Update item
- `DELETE /api/v1/workspaces/{id}/items/{itemId}` - Delete item

### AG-UI Streaming
- `POST /api/v1/canvas/stream` - SSE endpoint for AI interactions

## Dependencies to Install

### Frontend
```json
{
  "@your-org/draggable-canvas": "^1.0.0",  // Or path to local package
  "eventsource": "^2.0.0",  // SSE client
  "react-markdown": "^9.0.0"  // For insight notes
}
```

### Backend
```python
# requirements.txt
sse-starlette==1.8.2  # SSE support for FastAPI
```

## Benefits

1. **Spatial Organization**: Users can arrange analysis components naturally
2. **Progressive Disclosure**: AI streams results incrementally
3. **Reusability**: Save workspace layouts as templates
4. **Collaboration**: Share workspaces with team
5. **Flexibility**: Mix SQL, Python, ML, and notes on one canvas
6. **Discoverability**: Visual representation of analysis flow

## Next Steps

1. Install dependencies
2. Create database models and migrations
3. Build basic canvas API
4. Create CanvasWorkspace React component
5. Implement AG-UI streaming
6. Build proof-of-concept with sample query
