# Agent Frontend Integration Guide

## Overview

This guide explains how to integrate the multi-agent system into your existing frontend. We'll leverage your current `ChatSidebar` component and extend it to support agent-based interactions.

## Integration Strategy

### Approach: **Gradual Enhancement**

Instead of rebuilding the chat UI, we'll:
1. **Extend existing ChatSidebar** to support agent mode
2. **Add agent API hooks** alongside existing query hooks
3. **Create agent selection UI** as a new mode (like SQL/Python/Deep Research)
4. **Preserve backward compatibility** with existing workflows

---

## Phase 1: Add Agent API Functions

### Step 1.1: Extend `api.ts` with Agent Types & Functions

**File**: `frontend/src/services/api.ts`

```typescript
// Add after existing interfaces

export interface Agent {
  name: string
  display_name: string
  description: string
  capabilities: string[]
  tier: string
  enabled: boolean
}

export interface AgentMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  agent_name?: string
  code?: string
  result_data?: any
  timestamp: string
}

export interface AgentSession {
  id: string
  dataset_id: string
  name?: string
  created_at: string
  updated_at: string
}

export interface AgentChatRequest {
  query: string
  dataset_id: string
  agent_name?: string  // Optional - orchestrator auto-selects
  session_id?: string
  stream?: boolean
}

export interface AgentChatResponse {
  session_id: string
  agent: string
  response: {
    summary: string
    sql?: string
    data?: any
    visualizations?: any[]
    type?: string
  }
  metadata: Record<string, any>
}

// Agent API functions
export const agentApi = {
  // List all available agents
  listAgents: async (): Promise<Agent[]> => {
    const { data } = await api.get('/agents')
    return data.agents
  },

  // Chat with agents (non-streaming)
  chat: async (request: AgentChatRequest): Promise<AgentChatResponse> => {
    const { data } = await api.post('/agents/chat', request)
    return data
  },

  // Chat with streaming (SSE)
  chatStream: (request: AgentChatRequest, onChunk: (chunk: any) => void) => {
    const eventSource = new EventSource(
      `${import.meta.env.VITE_API_URL || '/api/v1'}/agents/chat/stream`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      }
    )

    eventSource.onmessage = (event) => {
      const chunk = JSON.parse(event.data)
      onChunk(chunk)
    }

    eventSource.onerror = (error) => {
      console.error('SSE error:', error)
      eventSource.close()
    }

    return eventSource  // Return for cleanup
  },

  // Get session details
  getSession: async (sessionId: string) => {
    const { data } = await api.get(`/agents/sessions/${sessionId}`)
    return data
  },

  // List sessions
  listSessions: async (datasetId?: string) => {
    const { data } = await api.get('/agents/sessions', {
      params: datasetId ? { dataset_id: datasetId } : {}
    })
    return data.sessions
  },

  // Generate session name
  generateSessionName: async (sessionId: string) => {
    const { data } = await api.post(`/agents/sessions/${sessionId}/name`)
    return data.name
  },

  // Delete session
  deleteSession: async (sessionId: string) => {
    await api.delete(`/agents/sessions/${sessionId}`)
  }
}

export default api
```

---

## Phase 2: Create Agent Chat Hook

### Step 2.1: Create `useAgentChat.ts` Hook

**File**: `frontend/src/hooks/useAgentChat.ts`

```typescript
import { useState, useCallback, useEffect } from 'react'
import { agentApi, Agent, AgentMessage, AgentChatResponse } from '@/services/api'

interface UseAgentChatOptions {
  datasetId: string
  sessionId?: string
  onSessionCreated?: (sessionId: string) => void
}

export function useAgentChat({ datasetId, sessionId: initialSessionId, onSessionCreated }: UseAgentChatOptions) {
  const [sessionId, setSessionId] = useState<string | undefined>(initialSessionId)
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string | undefined>()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastResponse, setLastResponse] = useState<AgentChatResponse | null>(null)

  // Load available agents on mount
  useEffect(() => {
    loadAgents()
  }, [])

  // Load session messages if sessionId provided
  useEffect(() => {
    if (sessionId) {
      loadSession(sessionId)
    }
  }, [sessionId])

  const loadAgents = async () => {
    try {
      const agentList = await agentApi.listAgents()
      setAgents(agentList)
    } catch (err) {
      console.error('Failed to load agents:', err)
    }
  }

  const loadSession = async (id: string) => {
    try {
      const session = await agentApi.getSession(id)
      setMessages(session.messages || [])
    } catch (err) {
      console.error('Failed to load session:', err)
    }
  }

  const sendMessage = useCallback(async (query: string, agentName?: string) => {
    setIsLoading(true)
    setError(null)

    // Add user message optimistically
    const userMessage: AgentMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])

    try {
      const response = await agentApi.chat({
        query,
        dataset_id: datasetId,
        agent_name: agentName || selectedAgent,
        session_id: sessionId,
        stream: false
      })

      // If new session created, update sessionId
      if (!sessionId && response.session_id) {
        setSessionId(response.session_id)
        onSessionCreated?.(response.session_id)
      }

      // Add assistant message
      const assistantMessage: AgentMessage = {
        id: `msg-${Date.now()}`,
        role: 'assistant',
        content: response.response.summary || JSON.stringify(response.response, null, 2),
        agent_name: response.agent,
        result_data: response.response,
        timestamp: new Date().toISOString()
      }

      setMessages(prev => [...prev, assistantMessage])
      setLastResponse(response)

    } catch (err: any) {
      setError(err.message || 'Failed to send message')
      console.error('Chat error:', err)

      // Add error message
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `❌ Error: ${err.message || 'Failed to process request'}`,
        timestamp: new Date().toISOString()
      }])
    } finally {
      setIsLoading(false)
    }
  }, [datasetId, sessionId, selectedAgent, onSessionCreated])

  const clearChat = useCallback(() => {
    setMessages([])
    setSessionId(undefined)
    setError(null)
    setLastResponse(null)
  }, [])

  return {
    sessionId,
    messages,
    agents,
    selectedAgent,
    isLoading,
    error,
    lastResponse,
    sendMessage,
    setSelectedAgent,
    clearChat,
    loadSession
  }
}
```

---

## Phase 3: Extend ChatSidebar Component

### Step 3.1: Add Agent Mode to ChatSidebar

**File**: `frontend/src/components/chat/ChatSidebar.tsx`

**Changes:**

1. **Update `AnalysisMode` type:**
```typescript
export type AnalysisMode = 'sql' | 'python' | 'auto' | 'deep-research' | 'agent'
```

2. **Add agent selection props:**
```typescript
interface ChatSidebarProps {
  // ... existing props
  agents?: Agent[]
  selectedAgent?: string
  onAgentChange?: (agentName: string | undefined) => void
  agentMode?: boolean  // Whether in agent mode
}
```

3. **Add agent mode UI in mode selector:**
```typescript
{(['auto', 'sql', 'python', 'deep-research', 'agent'] as AnalysisMode[]).map((mode) => (
  <button
    key={mode}
    type="button"
    onClick={() => onModeChange(mode)}
    className={`px-2.5 py-1 text-xs rounded-md flex items-center gap-1 transition-colors ${
      analysisMode === mode
        ? 'bg-blue-600 text-white'
        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
    }`}
  >
    {getModeIcon(mode)}
    <span>
      {mode === 'auto' ? 'Auto' :
       mode === 'sql' ? 'SQL' :
       mode === 'python' ? 'Python' :
       mode === 'deep-research' ? 'Deep' :
       mode === 'agent' ? '🤖 Agents' : mode}
    </span>
  </button>
))}
```

4. **Add agent selector dropdown (when agent mode is active):**
```typescript
{analysisMode === 'agent' && agents && agents.length > 0 && (
  <div className="space-y-2">
    <label className="text-xs font-medium text-gray-700">
      Select Agent (or leave Auto):
    </label>
    <select
      value={selectedAgent || ''}
      onChange={(e) => onAgentChange?.(e.target.value || undefined)}
      className="w-full text-sm border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      <option value="">🎯 Auto-Select (Recommended)</option>
      {agents.map((agent) => (
        <option key={agent.name} value={agent.name}>
          {agent.display_name} - {agent.description}
        </option>
      ))}
    </select>
    {selectedAgent && (
      <div className="text-xs text-gray-600 bg-blue-50 p-2 rounded border border-blue-200">
        <strong>Agent:</strong> {agents.find(a => a.name === selectedAgent)?.description}
      </div>
    )}
  </div>
)}
```

5. **Update placeholder text for agent mode:**
```typescript
placeholder={
  analysisMode === 'agent'
    ? selectedAgent
      ? `Ask ${agents?.find(a => a.name === selectedAgent)?.display_name}...`
      : 'Ask anything - agent will be selected automatically'
    : analysisMode === 'deep-research'
    ? 'Try: "Why are sales declining in Q3?"'
    : // ... existing placeholders
}
```

---

## Phase 4: Integrate with DatasetDetail Page

### Step 4.1: Update `DatasetDetail.tsx`

**File**: `frontend/src/pages/DatasetDetail.tsx`

```typescript
import { useAgentChat } from '@/hooks/useAgentChat'

// Inside DatasetDetail component:

const {
  sessionId: agentSessionId,
  messages: agentMessages,
  agents,
  selectedAgent,
  isLoading: agentLoading,
  sendMessage: sendAgentMessage,
  setSelectedAgent,
  clearChat: clearAgentChat
} = useAgentChat({
  datasetId: id!,
  onSessionCreated: (newSessionId) => {
    console.log('New agent session:', newSessionId)
    // Optionally store in URL or state
  }
})

// Update ChatSidebar to support both modes:

<ChatSidebar
  datasetId={id}
  datasetInfo={{
    name: dataset?.name || '',
    rowCount: dataset?.row_count || 0,
    columnCount: schema?.columns?.length || 0
  }}
  onQuerySubmit={async (query, mode) => {
    if (mode === 'agent') {
      // Use agent system
      await sendAgentMessage(query, selectedAgent)
    } else {
      // Use existing query system
      await handleQuery(query)
    }
  }}
  messages={
    analysisMode === 'agent'
      ? agentMessages.map(msg => ({
          role: msg.role as 'user' | 'assistant',
          content: msg.content
        }))
      : messages  // Existing messages
  }
  isLoading={analysisMode === 'agent' ? agentLoading : isLoading}
  analysisMode={analysisMode}
  onModeChange={setAnalysisMode}

  // Agent-specific props
  agents={agents}
  selectedAgent={selectedAgent}
  onAgentChange={setSelectedAgent}
  agentMode={analysisMode === 'agent'}
/>
```

---

## Phase 5: Enhanced Message Rendering

### Step 5.1: Create AgentMessageRenderer Component

**File**: `frontend/src/components/chat/AgentMessageRenderer.tsx`

```typescript
import { AgentMessage } from '@/services/api'
import { CheckCircle2, XCircle, Code2, Database, Table } from 'lucide-react'

interface AgentMessageRendererProps {
  message: AgentMessage
}

export function AgentMessageRenderer({ message }: AgentMessageRendererProps) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="bg-blue-500 text-white rounded-lg px-4 py-3 max-w-[85%]">
          <div className="text-sm whitespace-pre-wrap">{message.content}</div>
        </div>
      </div>
    )
  }

  // Assistant message with agent response
  const resultData = message.result_data

  return (
    <div className="flex justify-start">
      <div className="bg-gray-100 rounded-lg px-4 py-3 max-w-[85%] space-y-3">
        {/* Agent badge */}
        {message.agent_name && (
          <div className="flex items-center gap-2 text-xs">
            <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full font-medium">
              🤖 {message.agent_name.replace('_', ' ')}
            </span>
          </div>
        )}

        {/* Summary */}
        <div className="text-sm text-gray-900">
          {message.content}
        </div>

        {/* SQL Query */}
        {resultData?.sql && (
          <div className="bg-gray-800 text-gray-100 rounded p-3 text-xs font-mono overflow-x-auto">
            <div className="flex items-center gap-2 mb-2 text-gray-400">
              <Database className="h-3 w-3" />
              <span className="text-[10px] uppercase">SQL Query</span>
            </div>
            <pre>{resultData.sql}</pre>
          </div>
        )}

        {/* Code */}
        {message.code && !resultData?.sql && (
          <div className="bg-gray-800 text-gray-100 rounded p-3 text-xs font-mono overflow-x-auto">
            <div className="flex items-center gap-2 mb-2 text-gray-400">
              <Code2 className="h-3 w-3" />
              <span className="text-[10px] uppercase">Code</span>
            </div>
            <pre>{message.code}</pre>
          </div>
        )}

        {/* Result Preview */}
        {resultData?.result_preview && Array.isArray(resultData.result_preview) && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs text-gray-600">
              <Table className="h-3 w-3" />
              <span>Results ({resultData.row_count || resultData.result_preview.length} rows)</span>
            </div>
            <div className="bg-white rounded border border-gray-200 overflow-x-auto">
              <table className="min-w-full text-xs">
                <thead className="bg-gray-50">
                  <tr>
                    {Object.keys(resultData.result_preview[0] || {}).map((key) => (
                      <th key={key} className="px-3 py-2 text-left font-medium text-gray-700 border-b">
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {resultData.result_preview.slice(0, 5).map((row: any, i: number) => (
                    <tr key={i} className="border-b">
                      {Object.values(row).map((val: any, j: number) => (
                        <td key={j} className="px-3 py-2 text-gray-900">
                          {String(val)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Data Profiling Results */}
        {resultData?.observations && (
          <div className="space-y-2">
            <div className="text-xs font-medium text-gray-700">
              📊 Observations:
            </div>
            <ul className="text-xs space-y-1 text-gray-700">
              {resultData.observations.slice(0, 5).map((obs: string, i: number) => (
                <li key={i} className="flex items-start gap-2">
                  <CheckCircle2 className="h-3 w-3 text-green-600 mt-0.5 flex-shrink-0" />
                  <span dangerouslySetInnerHTML={{ __html: obs.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Timestamp */}
        <div className="text-[10px] text-gray-400">
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}
```

### Step 5.2: Use AgentMessageRenderer in ChatSidebar

Update the message rendering in ChatSidebar:

```typescript
{analysisMode === 'agent' ? (
  // Render agent messages with special component
  agentMessages.map((message, i) => (
    <AgentMessageRenderer key={message.id || i} message={message} />
  ))
) : (
  // Existing message rendering
  messages.map((message, i) => (
    <div
      key={i}
      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
    >
      {/* ... existing rendering ... */}
    </div>
  ))
)}
```

---

## Phase 6: Session Management UI

### Step 6.1: Create AgentSessionList Component

**File**: `frontend/src/components/agents/AgentSessionList.tsx`

```typescript
import { useState, useEffect } from 'react'
import { agentApi, AgentSession } from '@/services/api'
import { MessageSquare, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface AgentSessionListProps {
  datasetId: string
  onSessionSelect: (sessionId: string) => void
  currentSessionId?: string
}

export function AgentSessionList({ datasetId, onSessionSelect, currentSessionId }: AgentSessionListProps) {
  const [sessions, setSessions] = useState<AgentSession[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadSessions()
  }, [datasetId])

  const loadSessions = async () => {
    try {
      setIsLoading(true)
      const sessionList = await agentApi.listSessions(datasetId)
      setSessions(sessionList)
    } catch (err) {
      console.error('Failed to load sessions:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation()

    if (!confirm('Delete this conversation?')) return

    try {
      await agentApi.deleteSession(sessionId)
      setSessions(prev => prev.filter(s => s.id !== sessionId))
      if (currentSessionId === sessionId) {
        onSessionSelect('')  // Clear current session
      }
    } catch (err) {
      console.error('Failed to delete session:', err)
    }
  }

  if (isLoading) {
    return <div className="text-sm text-gray-500 p-4">Loading conversations...</div>
  }

  if (sessions.length === 0) {
    return (
      <div className="text-sm text-gray-500 p-4 text-center">
        No conversations yet. Start chatting!
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="text-xs font-medium text-gray-600 px-4 py-2">
        Previous Conversations
      </div>
      {sessions.map((session) => (
        <button
          key={session.id}
          onClick={() => onSessionSelect(session.id)}
          className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${
            currentSessionId === session.id ? 'bg-blue-50 border-l-4 border-blue-600' : ''
          }`}
        >
          <div className="flex items-start gap-3">
            <MessageSquare className="h-4 w-4 text-gray-400 mt-1 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-gray-900 truncate">
                {session.name || 'Untitled Conversation'}
              </div>
              <div className="text-xs text-gray-500">
                {new Date(session.updated_at).toLocaleDateString()}
              </div>
            </div>
            <button
              onClick={(e) => handleDelete(session.id, e)}
              className="p-1 hover:bg-red-100 rounded"
            >
              <Trash2 className="h-3 w-3 text-red-600" />
            </button>
          </div>
        </button>
      ))}
    </div>
  )
}
```

### Step 6.2: Add Session List to DatasetDetail Sidebar

```typescript
{analysisMode === 'agent' && (
  <div className="border-t border-gray-200 mt-4">
    <AgentSessionList
      datasetId={id!}
      onSessionSelect={(sessionId) => {
        // Load this session
        loadSession(sessionId)
      }}
      currentSessionId={agentSessionId}
    />
  </div>
)}
```

---

## Quick Start Implementation Checklist

### Minimal Viable Integration (1-2 hours):

- [ ] **Step 1**: Add agent API functions to `api.ts` (15 min)
- [ ] **Step 2**: Create `useAgentChat` hook (20 min)
- [ ] **Step 3**: Add `'agent'` to AnalysisMode in ChatSidebar (5 min)
- [ ] **Step 4**: Add agent mode button to mode selector (10 min)
- [ ] **Step 5**: Wire up agent chat in DatasetDetail (20 min)
- [ ] **Step 6**: Test basic agent chat functionality (30 min)

### Enhanced Experience (additional 2-3 hours):

- [ ] **Step 7**: Create AgentMessageRenderer component (45 min)
- [ ] **Step 8**: Add agent selection dropdown (30 min)
- [ ] **Step 9**: Create AgentSessionList component (45 min)
- [ ] **Step 10**: Add session management to sidebar (30 min)
- [ ] **Step 11**: Add streaming support (optional) (1 hour)

---

## Testing the Integration

### 1. Start Backend
```bash
cd backend
python run_server.py
```

### 2. Start Frontend
```bash
cd frontend
npm run dev
```

### 3. Test Agent Chat
1. Upload a dataset
2. Click "Agent" mode in chat sidebar
3. Type: "What's in this dataset?"
4. Should see agent profiling or querying the data
5. Try: "Show me the first 10 rows"
6. Should see QueryAgent returning SQL results

### 4. Verify Agent Selection
1. Select "Data Scouting Agent" from dropdown
2. Ask: "Profile this data"
3. Should see data quality observations

---

## Benefits of This Approach

✅ **Gradual Migration**: Existing workflows continue to work
✅ **Minimal Code Changes**: Reuses existing ChatSidebar component
✅ **Consistent UX**: Matches existing SQL/Python/Deep Research modes
✅ **Extensible**: Easy to add more agents later
✅ **Backward Compatible**: Old API calls still work

---

## Next Steps After Integration

1. **Add more agent types** (ML, Visualization, Statistical)
2. **Implement streaming UI** for long-running operations
3. **Add agent usage metrics** (tokens, cost tracking)
4. **Create agent marketplace** for custom agents
5. **Add agent configuration UI** for power users

Let me know which phase you'd like to implement first!
