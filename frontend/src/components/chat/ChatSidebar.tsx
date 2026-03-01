import { useState, useEffect, useRef, lazy, Suspense } from 'react'
import { Button } from '@/components/ui/button'
import { Send, Database, Code2, Brain, Bot, Sparkles, ChevronRight, Check, AlertCircle, Loader2, Play } from 'lucide-react'
import { QuickActions } from './QuickActions'
import { cn } from '@/lib/utils'

const SqlEditor = lazy(() => import('@/components/editor/SqlEditor').then(m => ({ default: m.SqlEditor })))

interface Message {
  role: 'user' | 'assistant'
  content: string
  status?: 'success' | 'error' | 'loading'
  metadata?: {
    rowCount?: number
    executionTime?: number
    insights?: string[]
  }
}

export type AnalysisMode = 'sql' | 'python' | 'auto' | 'deep-research' | 'agent'

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
  verboseMode?: boolean
  onVerboseModeToggle?: (value: boolean) => void
  generateInfographic?: boolean
  onInfographicToggle?: (value: boolean) => void
  infographicFormat?: 'pdf' | 'png'
  onInfographicFormatChange?: (format: 'pdf' | 'png') => void
  infographicColorScheme?: 'professional' | 'modern' | 'corporate'
  onInfographicColorSchemeChange?: (scheme: 'professional' | 'modern' | 'corporate') => void
  infographicGenerationMethod?: 'template' | 'ai'
  onInfographicGenerationMethodChange?: (method: 'template' | 'ai') => void
}

export function ChatSidebar({
  datasetId,
  datasetInfo: _datasetInfo,
  onQuerySubmit,
  messages,
  isLoading,
  analysisMode = 'auto',
  onModeChange,
  verboseMode = true,
  onVerboseModeToggle,
  generateInfographic = false,
  onInfographicToggle,
  infographicFormat = 'pdf',
  onInfographicFormatChange,
  infographicColorScheme = 'professional',
  onInfographicColorSchemeChange,
  infographicGenerationMethod = 'template',
  onInfographicGenerationMethodChange
}: ChatSidebarProps) {
  const [input, setInput] = useState('')
  const [showDirectSql, setShowDirectSql] = useState(false)
  const [sqlEditorValue, setSqlEditorValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const getQuickSuggestions = (): string[] => {
    if (messages.length === 0) {
      return ['Give me an overview', 'Show top 10 rows', 'Key statistics']
    }
    const lastMessage = messages[messages.length - 1]
    if (lastMessage.role === 'assistant' && lastMessage.content.includes('Dataset Overview')) {
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

  const handleDirectSqlRun = () => {
    if (sqlEditorValue.trim() && !isLoading) {
      onQuerySubmit(sqlEditorValue.trim(), 'sql')
    }
  }

  const modeConfig = {
    auto: { icon: Sparkles, label: 'Auto', color: 'text-amber-600' },
    agent: { icon: Bot, label: 'Agent', color: 'text-violet-600' },
    sql: { icon: Database, label: 'SQL', color: 'text-emerald-600' },
    python: { icon: Code2, label: 'Python', color: 'text-blue-600' },
    'deep-research': { icon: Brain, label: 'Deep', color: 'text-rose-600' }
  }

  return (
    <div className="flex flex-col h-screen bg-background overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-border bg-card px-4 py-4">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-11 h-11 bg-gradient-primary rounded-xl flex items-center justify-center shadow-lg shadow-primary/25">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-success rounded-full border-2 border-card" />
          </div>
          <div>
            <h1 className="font-display text-xl font-semibold text-foreground tracking-tight">
              Felix
            </h1>
            <p className="text-xs text-muted-foreground">AI Analytics Assistant</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 bg-background-subtle">
        {messages.length === 0 && (
          <div className="mt-8 animate-fade-in">
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-primary-muted mb-3">
                <Sparkles className="h-6 w-6 text-primary" />
              </div>
              <h3 className="font-display font-semibold text-foreground mb-1">
                Ask about your data
              </h3>
              <p className="text-sm text-muted-foreground">
                I can help you explore, analyze, and visualize
              </p>
            </div>

            <div className="bg-card rounded-xl border border-border p-4 shadow-sm">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">
                Try asking
              </p>
              <div className="space-y-2">
                {[
                  'Give me an overview of this dataset',
                  'What are the top 10 items by value?',
                  'Show me trends over time',
                  'Summarize by category'
                ].map((suggestion, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setInput(suggestion)
                      onQuerySubmit(suggestion, analysisMode)
                    }}
                    className={cn(
                      'w-full text-left px-3 py-2.5 rounded-lg text-sm',
                      'bg-background-subtle hover:bg-muted',
                      'text-foreground',
                      'transition-colors duration-150',
                      'flex items-center gap-2 group'
                    )}
                  >
                    <ChevronRight className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary transition-colors" />
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((message, i) => (
          <div
            key={i}
            className={cn(
              'flex animate-fade-in',
              message.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0 mr-2 mt-1">
                <div className="w-7 h-7 rounded-lg bg-gradient-primary flex items-center justify-center shadow-sm">
                  <Sparkles className="h-3.5 w-3.5 text-white" />
                </div>
              </div>
            )}

            <div
              className={cn(
                'rounded-2xl px-4 py-3 max-w-[85%]',
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground rounded-br-md'
                  : 'bg-card border border-border shadow-sm rounded-bl-md'
              )}
            >
              {/* Message Status Indicator */}
              {message.role === 'assistant' && message.metadata?.rowCount !== undefined && (
                <div className="flex items-center gap-2 mb-2 pb-2 border-b border-border">
                  <div className="flex items-center gap-1.5 text-xs text-success">
                    <Check className="h-3.5 w-3.5" />
                    <span className="font-medium">Found {message.metadata.rowCount.toLocaleString()} results</span>
                  </div>
                  {message.metadata.executionTime && (
                    <span className="text-xs text-muted-foreground">
                      {message.metadata.executionTime}ms
                    </span>
                  )}
                </div>
              )}

              <div
                className={cn(
                  'text-sm leading-relaxed',
                  message.role === 'assistant' && 'text-foreground'
                )}
                dangerouslySetInnerHTML={{
                  __html: message.content
                    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
                    .replace(/\n/g, '<br/>')
                }}
              />

              {/* AI Insights */}
              {message.role === 'assistant' && message.metadata?.insights && message.metadata.insights.length > 0 && (
                <div className="mt-3 pt-3 border-t border-border">
                  <p className="text-xs font-medium text-muted-foreground mb-2">Key Insights</p>
                  <ul className="space-y-1.5">
                    {message.metadata.insights.map((insight, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-xs text-foreground">
                        <span className="text-primary mt-0.5">•</span>
                        {insight}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start animate-fade-in">
            <div className="flex-shrink-0 mr-2 mt-1">
              <div className="w-7 h-7 rounded-lg bg-gradient-primary flex items-center justify-center shadow-sm">
                <Sparkles className="h-3.5 w-3.5 text-white" />
              </div>
            </div>
            <div className="bg-card border border-border rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 text-primary animate-spin" />
                <span className="text-sm text-muted-foreground">Analyzing...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      {!isLoading && messages.length > 0 && (
        <QuickActions
          suggestions={getQuickSuggestions()}
          onSelect={(q) => {
            setInput(q)
            onQuerySubmit(q)
          }}
        />
      )}

      {/* Input Area */}
      <div className="flex-shrink-0 border-t border-border bg-card p-4 space-y-3">
        {/* Mode Selector */}
        {onModeChange && (
          <div className="flex gap-1 p-1 bg-muted rounded-lg">
            {(['auto', 'agent', 'sql', 'python', 'deep-research'] as AnalysisMode[]).map((mode) => {
              const config = modeConfig[mode]
              const Icon = config.icon
              const isActive = analysisMode === mode

              return (
                <button
                  key={mode}
                  type="button"
                  onClick={() => onModeChange(mode)}
                  className={cn(
                    'flex-1 px-2 py-1.5 text-xs font-medium rounded-md',
                    'flex items-center justify-center gap-1.5',
                    'transition-all duration-150',
                    isActive
                      ? 'bg-card text-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  )}
                >
                  <Icon className={cn('h-3.5 w-3.5', isActive && config.color)} />
                  <span className="hidden sm:inline">{config.label}</span>
                </button>
              )
            })}
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your data..."
              disabled={isLoading || !datasetId}
              className={cn(
                'w-full px-4 py-2.5 pr-4',
                'bg-background border border-border rounded-xl',
                'text-sm text-foreground placeholder:text-muted-foreground',
                'focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'transition-all duration-150'
              )}
            />
          </div>
          <Button
            type="submit"
            size="icon"
            disabled={isLoading || !input.trim() || !datasetId}
            className="h-10 w-10 rounded-xl shadow-sm"
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>

        {/* Mode Hints */}
        {analysisMode === 'agent' && (
          <p className="text-xs text-muted-foreground flex items-center gap-1.5">
            <Bot className="h-3.5 w-3.5 text-violet-500" />
            Agent mode auto-routes to specialized AI agents
          </p>
        )}
        {analysisMode === 'python' && (
          <p className="text-xs text-muted-foreground flex items-center gap-1.5">
            <Code2 className="h-3.5 w-3.5 text-blue-500" />
            Python mode for ML models and advanced analysis
          </p>
        )}
        {analysisMode === 'sql' && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                <Database className="h-3.5 w-3.5 text-emerald-500" />
                {showDirectSql ? 'Write SQL directly — Cmd+Enter to run' : 'Describe what you want in plain English'}
              </p>
              <button
                type="button"
                onClick={() => setShowDirectSql(v => !v)}
                className="text-xs text-emerald-600 hover:text-emerald-500 font-medium underline underline-offset-2"
              >
                {showDirectSql ? 'Switch to NL' : 'Write SQL'}
              </button>
            </div>
            {showDirectSql && (
              <div className="space-y-1.5">
                <Suspense fallback={
                  <div className="h-32 bg-gray-900 rounded-lg border border-gray-700 flex items-center justify-center">
                    <span className="text-xs text-gray-400">Loading editor...</span>
                  </div>
                }>
                  <SqlEditor
                    value={sqlEditorValue}
                    onChange={setSqlEditorValue}
                    onRun={handleDirectSqlRun}
                    height="160px"
                    showControls
                  />
                </Suspense>
                <button
                  type="button"
                  onClick={handleDirectSqlRun}
                  disabled={!sqlEditorValue.trim() || isLoading}
                  className="w-full flex items-center justify-center gap-2 py-2 px-4 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
                >
                  <Play className="h-3.5 w-3.5" />
                  Run SQL
                </button>
              </div>
            )}
          </div>
        )}
        {analysisMode === 'deep-research' && (
          <div className="space-y-3">
            <p className="text-xs text-muted-foreground flex items-center gap-1.5">
              <Brain className="h-3.5 w-3.5 text-rose-500" />
              Deep research for comprehensive multi-stage analysis
            </p>

            {/* Verbose Mode Toggle */}
            <div className="bg-muted rounded-lg p-3 space-y-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={verboseMode}
                  onChange={(e) => onVerboseModeToggle?.(e.target.checked)}
                  className="rounded border-border text-primary focus:ring-primary/20"
                />
                <span className="text-sm font-medium text-foreground">
                  Verbose Mode
                </span>
              </label>
              <p className="text-xs text-muted-foreground pl-6">
                {verboseMode
                  ? 'Full analysis with methodology, findings, and recommendations'
                  : 'Quick insights and key findings only'}
              </p>
            </div>

            {/* Infographic Options */}
            <div className="bg-muted rounded-lg p-3 space-y-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={generateInfographic}
                  onChange={(e) => onInfographicToggle?.(e.target.checked)}
                  className="rounded border-border text-primary focus:ring-primary/20"
                />
                <span className="text-sm font-medium text-foreground">
                  Generate Infographic
                </span>
              </label>

              {generateInfographic && (
                <div className="pl-6 space-y-2 pt-2">
                  <select
                    value={infographicGenerationMethod}
                    onChange={(e) => onInfographicGenerationMethodChange?.(e.target.value as 'template' | 'ai')}
                    className="w-full text-xs bg-card border border-border rounded-md px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary/20"
                  >
                    <option value="template">Template (Free)</option>
                    <option value="ai">AI-Powered (Premium)</option>
                  </select>

                  <select
                    value={infographicFormat}
                    onChange={(e) => onInfographicFormatChange?.(e.target.value as 'pdf' | 'png')}
                    className="w-full text-xs bg-card border border-border rounded-md px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary/20"
                  >
                    <option value="pdf">PDF</option>
                    <option value="png">PNG</option>
                  </select>

                  {infographicGenerationMethod === 'template' && (
                    <select
                      value={infographicColorScheme}
                      onChange={(e) => onInfographicColorSchemeChange?.(e.target.value as 'professional' | 'modern' | 'corporate')}
                      className="w-full text-xs bg-card border border-border rounded-md px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary/20"
                    >
                      <option value="professional">Professional</option>
                      <option value="modern">Modern</option>
                      <option value="corporate">Corporate</option>
                    </select>
                  )}

                  {infographicGenerationMethod === 'ai' && (
                    <p className="text-xs text-warning flex items-center gap-1.5">
                      <AlertCircle className="h-3.5 w-3.5" />
                      AI generation incurs API costs
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Slash Commands Help */}
        {input.startsWith('/') && (
          <div className="bg-primary-muted border border-primary/20 rounded-lg p-3">
            <p className="text-xs font-medium text-foreground mb-2">Slash Commands</p>
            <div className="space-y-1 text-xs text-muted-foreground">
              <p><code className="text-primary">/metadata</code> - Update column metadata</p>
              <p><code className="text-primary">/rule</code> - Create query rules</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
