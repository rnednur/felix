import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Upload, Settings, Send, Code2, Database, Table2, Brain } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { QuickActions } from './QuickActions'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export type AnalysisMode = 'sql' | 'python' | 'auto' | 'deep-research'

interface DatasetInfo {
  name: string
  rowCount: number
  columnCount: number
  numericColumns?: number
  categoricalColumns?: number
  datetimeColumns?: number
  completeness?: number
  duplicates?: number
}

interface ChatSidebarProps {
  datasetId?: string
  datasetInfo?: DatasetInfo
  onQuerySubmit: (query: string, mode?: AnalysisMode) => void
  messages: Message[]
  isLoading?: boolean
  analysisMode?: AnalysisMode
  onModeChange?: (mode: AnalysisMode) => void
}

export function ChatSidebar({
  datasetId,
  datasetInfo,
  onQuerySubmit,
  messages,
  isLoading,
  analysisMode = 'auto',
  onModeChange
}: ChatSidebarProps) {
  const [input, setInput] = useState('')
  const navigate = useNavigate()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  // Generate smart suggestions based on conversation context
  const getQuickSuggestions = (): string[] => {
    if (messages.length === 0) {
      return ['Describe dataset', 'How many records?', 'Show first 10']
    }

    const lastMessage = messages[messages.length - 1]
    if (lastMessage.role === 'assistant' && lastMessage.content.includes('Dataset Overview')) {
      // After showing metadata, suggest queries
      return ['Show first 10', 'Summarize data', 'Group by category']
    } else if (lastMessage.role === 'assistant' && lastMessage.content.includes('records')) {
      return ['Show top 10', 'Group by category', 'Show trends']
    }

    return ['Show summary', 'Group data']
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      onQuerySubmit(input, analysisMode)
      setInput('')
    }
  }

  const getModeLabel = (mode: AnalysisMode) => {
    switch (mode) {
      case 'sql': return 'SQL Mode'
      case 'python': return 'Python Mode'
      case 'auto': return 'Auto Mode'
      case 'deep-research': return 'Deep Research'
    }
  }

  const getModeIcon = (mode: AnalysisMode) => {
    switch (mode) {
      case 'sql': return <Database className="h-4 w-4" />
      case 'python': return <Code2 className="h-4 w-4" />
      case 'auto': return <span className="text-xs font-bold">✨</span>
      case 'deep-research': return <Brain className="h-4 w-4" />
    }
  }

  return (
    <div className="w-96 border-r border-gray-200 flex flex-col bg-white h-screen overflow-hidden">
      {/* Header */}
      <div className="border-b border-gray-200 p-3">
        <div className="flex items-center gap-1">
          <div className="w-14 h-14 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center shadow-md">
            <svg className="h-8 w-8 text-white" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2c-1.1 0-2 .9-2 2v2c0 1.1.9 2 2 2s2-.9 2-2V4c0-1.1-.9-2-2-2zm-9 9c0-1.1.9-2 2-2h2c1.1 0 2 .9 2 2s-.9 2-2 2H5c-1.1 0-2-.9-2-2zm14 0c0-1.1.9-2 2-2h2c1.1 0 2 .9 2 2s-.9 2-2 2h-2c-1.1 0-2-.9-2-2zM12 16c-2.2 0-4 1.8-4 4v2h8v-2c0-2.2-1.8-4-4-4zm-6.8-3.2l-1.4-1.4c-.8-.8-.8-2 0-2.8.8-.8 2-.8 2.8 0l1.4 1.4c.8.8.8 2 0 2.8-.8.8-2 .8-2.8 0zm13.6 0c-.8.8-2 .8-2.8 0-.8-.8-.8-2 0-2.8l1.4-1.4c.8-.8 2-.8 2.8 0 .8.8.8 2 0 2.8l-1.4 1.4zM12 13c.6 0 1 .4 1 1s-.4 1-1 1-1-.4-1-1 .4-1 1-1z"/>
            </svg>
          </div>
          <div>
            <h1 className="font-bold text-2xl bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Felix</h1>
            <p className="text-sm text-gray-500">AI Analytics</p>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 text-sm mt-8 px-2">
            <div className="mb-4">
              <p className="text-base font-medium text-gray-700">💬 Ask about your data</p>
            </div>
            <div className="text-left bg-gray-50 rounded-lg p-3 space-y-2">
              <p className="text-xs font-semibold text-gray-600">Try these:</p>
              <div className="space-y-1 text-xs">
                <p>• "How many records are there?"</p>
                <p>• "Show top 10 by revenue"</p>
                <p>• "Summarize sales by category"</p>
                <p>• "What's the average discount?"</p>
                <p>• "Show me trends over time"</p>
              </div>
              <div className="pt-2 border-t border-gray-200 mt-2">
                <p className="text-xs text-gray-500">
                  💡 Check the <strong>Schema</strong> tab to see all columns and stats
                </p>
              </div>
            </div>
          </div>
        )}

        {messages.map((message, i) => (
          <div
            key={i}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`rounded-lg px-4 py-3 max-w-[85%] ${
                message.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-900'
              }`}
            >
              <div
                className="text-sm whitespace-pre-wrap"
                style={{
                  lineHeight: '1.5',
                }}
                dangerouslySetInnerHTML={{
                  __html: message.content
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/\n/g, '<br/>')
                }}
              />
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 rounded-lg px-4 py-2">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}

        {/* Invisible element to scroll to */}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      {!isLoading && messages.length > 0 && (
        <QuickActions suggestions={getQuickSuggestions()} onSelect={(q) => {
          setInput(q)
          onQuerySubmit(q)
        }} />
      )}

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4 bg-white space-y-3">
        {/* Mode Selector */}
        {onModeChange && (
          <div className="space-y-2">
            <div className="flex gap-1 flex-wrap">
              {(['auto', 'sql', 'python', 'deep-research'] as AnalysisMode[]).map((mode) => (
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
                     'Deep'}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              analysisMode === 'deep-research'
                ? 'Try: "Why are sales declining in Q3?"'
                : analysisMode === 'python'
                ? 'Try: "Train a model to predict Sales"'
                : analysisMode === 'sql'
                ? 'Ask about your data...'
                : 'Ask anything...'
            }
            disabled={isLoading || !datasetId}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
          <Button type="submit" size="icon" disabled={isLoading || !input.trim() || !datasetId}>
            <Send className="h-4 w-4" />
          </Button>
        </form>

        {analysisMode === 'python' && (
          <div className="text-xs text-gray-500">
            💡 Python mode: ML models, stats, workflows
          </div>
        )}
        {analysisMode === 'deep-research' && (
          <div className="text-xs text-gray-500">
            🧠 Deep research: Multi-stage analysis with insights
          </div>
        )}
        {input.startsWith('/') && (
          <div className="text-xs bg-blue-50 text-blue-700 p-2 rounded border border-blue-200">
            <div className="font-medium mb-1">Slash Commands:</div>
            <div className="space-y-0.5">
              <div><code>/metadata [instruction]</code> - Update column metadata with AI</div>
              <div><code>/rule [instruction]</code> - Create query rules with AI</div>
            </div>
            <div className="mt-1 text-blue-600">
              Examples: <code>/metadata mark email as PII</code> or <code>/rule only show active users</code>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
