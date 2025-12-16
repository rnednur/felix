import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useDataset, useDatasetPreview, useDatasetSchema } from '@/hooks/useDatasets'
import { useNLQuery } from '@/hooks/useQuery'
import { useVisualizationSuggestions } from '@/hooks/useVisualization'
import { ChatSidebar, type AnalysisMode } from '@/components/chat/ChatSidebar'
import { DataWorkspaceLayout } from '@/components/layout/DataWorkspaceLayout'
import { SpreadsheetView } from '@/components/canvas/SpreadsheetView'
import { DashboardView } from '@/components/canvas/DashboardView'
import { SchemaView } from '@/components/canvas/SchemaView'
import { ReportView } from '@/components/canvas/ReportView'
import { CanvasWorkspace } from '@/components/canvas/CanvasWorkspace'
import { useAGUIStream } from '@/hooks/useAGUIStream'
import { CanvasItem } from '@/types/canvas'
import { DatasetHub } from '@/components/dataset-hub/DatasetHub'
import { CodePreviewModal } from '@/components/python/CodePreviewModal'
import { DatasetOverviewModal } from '@/components/datasets/DatasetOverviewModal'
import { DatasetSettingsPanel } from '@/components/metadata/DatasetSettingsPanel'
import { ShareModal } from '@/components/sharing/ShareModal'
import { PlanEditor } from '@/components/research/PlanEditor'
import { ResearchHistoryModal } from '@/components/research/ResearchHistoryModal'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { IconButton } from '@/components/ui/icon-button'
import { FileSpreadsheet, BarChart3, Settings, Info, Table2, Code2, Upload, FileText, ArrowLeft, History, Share2, Layout, X, FolderOpen, Sparkles } from 'lucide-react'
import { describeDataset, generatePythonCode, executePythonCode, executeDeepResearch, type PythonAnalysisResult, type ExecutionResult, type DeepResearchResult } from '@/services/api'
import axios from '@/services/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  code?: string
  executionResult?: ExecutionResult
}

export default function DatasetDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: dataset } = useDataset(id!)
  const { data: preview } = useDatasetPreview(id!)
  const { data: schema } = useDatasetSchema(id!)

  // Save the current dataset ID to localStorage for "back" navigation
  useEffect(() => {
    if (id) {
      localStorage.setItem('lastViewedDatasetId', id)
    }
  }, [id])
  const [messages, setMessages] = useState<Message[]>([])
  const [currentView, setCurrentView] = useState<'hub' | 'spreadsheet' | 'dashboard' | 'schema' | 'code' | 'report' | 'canvas'>('hub')
  const [queryResult, setQueryResult] = useState<any>(null)

  // Canvas mode state
  const [canvasItems, setCanvasItems] = useState<CanvasItem[]>([])
  const [canvasMode, setCanvasMode] = useState(false)
  const [showLoadDialog, setShowLoadDialog] = useState(false)
  const [savedWorkspaces, setSavedWorkspaces] = useState<any[]>([])
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('auto')
  const [codePreview, setCodePreview] = useState<PythonAnalysisResult | null>(null)
  const [showCodeModal, setShowCodeModal] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)
  const [isGeneratingCode, setIsGeneratingCode] = useState(false)
  const [deepResearchReport, setDeepResearchReport] = useState<any>(null)
  const [showOverviewModal, setShowOverviewModal] = useState(false)
  const [overviewData, setOverviewData] = useState<any>(null)
  const [showSettingsPanel, setShowSettingsPanel] = useState(false)
  const [lastExecution, setLastExecution] = useState<{
    code: string
    result: ExecutionResult | null
    mode: string
  } | null>(null)

  // Deep research options
  const [verboseMode, setVerboseMode] = useState(true)

  // Infographic options
  const [generateInfographic, setGenerateInfographic] = useState(false)
  const [infographicFormat, setInfographicFormat] = useState<'pdf' | 'png'>('pdf')
  const [infographicColorScheme, setInfographicColorScheme] = useState<'professional' | 'modern' | 'corporate'>('professional')
  const [infographicGenerationMethod, setInfographicGenerationMethod] = useState<'template' | 'ai'>('template')
  const [currentInfographic, setCurrentInfographic] = useState<any>(null)

  // Planning flow
  const [showPlanEditor, setShowPlanEditor] = useState(false)
  const [currentPlan, setCurrentPlan] = useState<any>(null)

  // Research history
  const [showHistoryModal, setShowHistoryModal] = useState(false)

  // Sharing
  const [showShareModal, setShowShareModal] = useState(false)

  const nlQueryMutation = useNLQuery()
  const { data: vizSuggestions } = useVisualizationSuggestions(queryResult?.query_id)

  // AG-UI Stream for canvas mode
  const { isStreaming, startStream } = useAGUIStream({
    workspaceId: id || 'temp',
    datasetId: id,
    onItemCreate: (item) => {
      setCanvasItems(prev => {
        // First item - use backend position
        if (prev.length === 0) {
          return [item as CanvasItem]
        }

        // Check if this is a header (start of new question group)
        const isHeader = item.type === 'insight-note' &&
                        (item.content as any)?.tags?.includes('query-header')

        if (isHeader) {
          // Find the bottom of the last group
          const maxY = Math.max(...prev.map(i => i.y + i.height))
          // Start new group with 150px spacing
          return [...prev, { ...item, y: maxY + 150 } as CanvasItem]
        }

        // For non-header items, find the last header to determine group base Y
        const headers = prev.filter(p =>
          p.type === 'insight-note' && (p.content as any)?.tags?.includes('query-header')
        )
        const lastHeader = headers[headers.length - 1]
        const baseY = lastHeader ? lastHeader.y : 50

        // Adjust Y position relative to the current group's base
        // Keep the backend's relative positioning within the group
        const adjustedItem = {
          ...item,
          y: baseY + (item.y - 100) // Backend uses base_y = 100, adjust to actual base
        } as CanvasItem

        return [...prev, adjustedItem]
      })
    },
    onComplete: () => {
      console.log('Stream completed')
    },
    onError: (err) => {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ Error: ${err}`
      }])
    }
  })

  // Check user's role and permissions
  const { data: userRole } = useQuery({
    queryKey: ['user-role', id],
    queryFn: async () => {
      const { data } = await axios.get(`/sharing/datasets/${id}/my-role`)
      return data
    },
    enabled: !!id
  })

  // Removed auto-describe - users can click "Describe Dataset" button to open modal

  const generateInsights = (result: any, originalQuery: string): string => {
    const { rows, total_rows } = result
    if (rows.length === 0) return 'No results found for your query.'

    let insights: string[] = []
    const firstRow = rows[0]
    const columns = Object.keys(firstRow)

    // Analyze column types
    const numericCols = columns.filter((key) => {
      const val = firstRow[key]
      return typeof val === 'number' || (!isNaN(parseFloat(val)) && isFinite(val))
    })

    // Check if it's an aggregation query
    const hasAggregations = columns.some((key) =>
      key.toLowerCase().match(/(sum|avg|count|total|min|max|distinct)/i)
    )

    // Check if it's a simple count query
    const isCountQuery = rows.length === 1 && columns.length === 1 &&
                        columns[0].toLowerCase().includes('count')

    if (isCountQuery) {
      const count = Object.values(firstRow)[0]
      insights.push(`📊 This dataset contains **${count.toLocaleString()} records**.`)
      insights.push('\n\n💡 Try asking:')
      insights.push('• "Show me the first 10 rows"')
      insights.push('• "What are the top categories by sales?"')
      insights.push('• "Summarize revenue by region"')
    } else if (hasAggregations && rows.length === 1) {
      // Single summary row with multiple metrics
      insights.push(`📈 **Summary Statistics:**\n`)

      Object.entries(firstRow).forEach(([key, value]) => {
        const formattedValue = typeof value === 'number'
          ? value.toLocaleString(undefined, { maximumFractionDigits: 2 })
          : value
        insights.push(`• ${key}: **${formattedValue}**`)
      })

      insights.push('\n\n💡 You can also ask:')
      insights.push('• "Break this down by category"')
      insights.push('• "Show me a trend over time"')
    } else if (hasAggregations && rows.length > 1 && rows.length < 20) {
      // Grouped aggregation results
      insights.push(`📊 Found **${total_rows} ${columns[0]}** with aggregated metrics.`)

      // Highlight top items if applicable
      if (numericCols.length > 0) {
        const topMetric = numericCols[0]
        const topValue = firstRow[topMetric]
        const topName = firstRow[columns[0]]

        insights.push(`\n🏆 Top performer: **${topName}** with ${topMetric.toLowerCase()} of **${typeof topValue === 'number' ? topValue.toLocaleString() : topValue}**`)
      }

      insights.push('\n\nCheck the **Dashboard** tab to see visualizations.')
    } else if (rows.length > 20) {
      // Large result set
      insights.push(`📋 Retrieved **${total_rows.toLocaleString()} rows** from your query.`)
      insights.push('\n\nShowing the top results in the **Dashboard** tab.')
      insights.push('\n\n💡 You might want to:')
      insights.push('• Add filters to narrow down results')
      insights.push('• Group by a category')
      insights.push('• Sort by a specific column')
    } else {
      // Small result set
      insights.push(`✅ Found **${total_rows} ${total_rows === 1 ? 'result' : 'results'}**.`)
      insights.push('\n\nView the details in the **Dashboard** tab.')
    }

    return insights.join('\n')
  }

  // Handle execute plan when user clicks "Start research" in plan editor
  const handleExecutePlan = async (editedPlan: { main_question: string; sub_questions: any[] }) => {
    setShowPlanEditor(false)

    setMessages((prev) => [...prev, {
      role: 'assistant',
      content: '🧠 Executing research plan...'
    }])

    try {
      const apiUrl = import.meta.env.VITE_API_URL || '/api/v1'

      const response = await fetch(`${apiUrl}/deep-research/execute-plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_id: id!,
          main_question: editedPlan.main_question,
          sub_questions: editedPlan.sub_questions,
          enable_python: true,
          enable_world_knowledge: true,
          verbose_mode: verboseMode,
          generate_infographic: generateInfographic,
          infographic_format: infographicFormat,
          infographic_color_scheme: infographicColorScheme,
          infographic_generation_method: infographicGenerationMethod
        })
      })

      const result = await response.json()

      if (!result.success) {
        throw new Error(result.error || 'Research execution failed')
      }

      // Save results
      setDeepResearchReport(result)
      if (result.infographic) {
        setCurrentInfographic(result.infographic)
      }

      // Switch to report view
      setCurrentView('report')

      // Update message
      setMessages((prev) => {
        const newMessages = [...prev]
        newMessages[newMessages.length - 1] = {
          role: 'assistant',
          content: `✅ Research complete! View the full report in the **Report** tab.`
        }
        return newMessages
      })

    } catch (error: any) {
      console.error('Plan execution failed:', error)
      setMessages((prev) => {
        const newMessages = [...prev]
        newMessages[newMessages.length - 1] = {
          role: 'assistant',
          content: `❌ Execution failed: ${error.message || 'Unknown error'}`
        }
        return newMessages
      })
    }
  }

  const handleLoadWorkspace = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        alert('Please log in to load workspaces')
        return
      }

      // Fetch workspaces for this dataset
      const response = await axios.get('/workspaces', {
        headers: { Authorization: `Bearer ${token}` }
      })

      // Filter by dataset_id if needed
      const workspacesForDataset = response.data.filter((ws: any) => ws.dataset_id === id)
      setSavedWorkspaces(workspacesForDataset)
      setShowLoadDialog(true)
    } catch (error: any) {
      console.error('Failed to load workspaces:', error)
      alert(`Failed to load workspaces: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleSelectWorkspace = async (workspaceId: string) => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) return

      // Fetch workspace with items
      const response = await axios.get(`/workspaces/${workspaceId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })

      const workspace = response.data

      // Convert backend format to frontend format
      const loadedItems: CanvasItem[] = workspace.items.map((item: any) => ({
        id: item.id,
        workspaceId: workspace.id,
        type: item.type,
        x: item.x,
        y: item.y,
        width: item.width,
        height: item.height,
        zIndex: item.z_index,
        content: item.content
      }))

      setCanvasItems(loadedItems)
      setShowLoadDialog(false)
      alert(`✅ Loaded workspace: ${workspace.name}`)
    } catch (error: any) {
      console.error('Failed to load workspace:', error)
      alert(`Failed to load workspace: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleQuerySubmit = async (query: string, mode: AnalysisMode = 'auto') => {
    // Switch away from hub view when query is submitted
    if (currentView === 'hub') {
      setCurrentView('dashboard')
    }

    // Handle canvas mode
    if (canvasMode) {
      setMessages((prev) => [...prev, { role: 'user', content: query }])
      startStream(query)
      setCurrentView('canvas')
      return
    }

    // Check for slash commands
    if (query.startsWith('/metadata ')) {
      const instruction = query.substring(10).trim()
      setMessages((prev) => [...prev, { role: 'user', content: query }])

      try {
        setMessages((prev) => [...prev, {
          role: 'assistant',
          content: '🤖 Using AI to update column metadata...'
        }])

        const response = await fetch(`http://localhost:8000/api/v1/metadata/datasets/${id}/ai-update`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ instruction })
        })

        const result = await response.json()

        if (!response.ok) throw new Error(result.detail || 'Failed to update metadata')

        const updatesText = Object.entries(result.updates || {})
          .map(([col, updates]: [string, any]) => {
            const fields = Object.entries(updates)
              .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
              .join(', ')
            return `• **${col}**: ${fields}`
          })
          .join('\n')

        setMessages((prev) => [...prev.slice(0, -1), {
          role: 'assistant',
          content: `✅ ${result.message}\n\n**Updates:**\n${updatesText}\n\n💡 The AI has analyzed your columns and applied the requested metadata updates. These will now help improve query accuracy.`
        }])
        return
      } catch (error: any) {
        setMessages((prev) => [...prev.slice(0, -1), {
          role: 'assistant',
          content: `❌ Failed to update metadata: ${error.message}`
        }])
        return
      }
    }

    if (query.startsWith('/rule ')) {
      const instruction = query.substring(6).trim()
      setMessages((prev) => [...prev, { role: 'user', content: query }])

      try {
        setMessages((prev) => [...prev, {
          role: 'assistant',
          content: '🤖 Using AI to create query rules...'
        }])

        const response = await fetch(`http://localhost:8000/api/v1/metadata/datasets/${id}/ai-rules`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ instruction })
        })

        const result = await response.json()

        if (!response.ok) throw new Error(result.detail || 'Failed to create rules')

        const rulesText = (result.rules || [])
          .map((rule: any) => `• **${rule.name}**: ${rule.description}\n  Type: ${rule.rule_type}, Condition: ${JSON.stringify(rule.condition)}`)
          .join('\n\n')

        setMessages((prev) => [...prev.slice(0, -1), {
          role: 'assistant',
          content: `✅ ${result.message}\n\n**Rules Created:**\n${rulesText}\n\n💡 These rules will be automatically applied to all future queries on this dataset.`
        }])
        return
      } catch (error: any) {
        setMessages((prev) => [...prev.slice(0, -1), {
          role: 'assistant',
          content: `❌ Failed to create rules: ${error.message}`
        }])
        return
      }
    }

    // Check for special commands
    if (query.toLowerCase().includes('describe') ||
        query.toLowerCase().includes('metadata') ||
        query.toLowerCase().includes('tell me about this data')) {

      setMessages((prev) => [...prev, { role: 'user', content: query }])

      try {
        const description = await describeDataset(id!)
        setMessages((prev) => [...prev, {
          role: 'assistant',
          content: description.description_text
        }])
        return
      } catch (error: any) {
        setMessages((prev) => [...prev, {
          role: 'assistant',
          content: '❌ Failed to retrieve metadata. Please try again.'
        }])
        return
      }
    }

    // Add user message
    setMessages((prev) => [...prev, { role: 'user', content: query }])

    // Deep Research mode
    if (mode === 'deep-research') {
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: '🧠 Generating research plan...'
      }])

      try {
        const apiUrl = import.meta.env.VITE_API_URL || '/api/v1'

        // Step 1: Generate plan first
        const planResponse = await fetch(`${apiUrl}/deep-research/plan`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            dataset_id: id!,
            question: query,
            max_sub_questions: 10
          })
        })

        const plan = await planResponse.json()

        if (!plan.success) {
          throw new Error(plan.error || 'Plan generation failed')
        }

        // Step 2: Show plan editor modal
        setCurrentPlan(plan)
        setShowPlanEditor(true)

        // Update message to show plan is ready
        setMessages((prev) => {
          const newMessages = [...prev]
          newMessages[newMessages.length - 1] = {
            role: 'assistant',
            content: '✅ Research plan ready! Review and edit your plan in the modal.'
          }
          return newMessages
        })

      } catch (error: any) {
        console.error('Plan generation failed:', error)
        setMessages((prev) => {
          const newMessages = [...prev]
          newMessages[newMessages.length - 1] = {
            role: 'assistant',
            content: `❌ Plan generation failed: ${error.message || 'Unknown error'}`
          }
          return newMessages
        })
      }
      return
    }

    // Python mode
    if (mode === 'python') {
      // Show generating message
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: '⚙️ Generating Python code...'
      }])
      setIsGeneratingCode(true)

      try {
        const result = await generatePythonCode(id!, query, 'auto', false)
        setCodePreview(result)
        setShowCodeModal(true)
        setIsGeneratingCode(false)

        // Replace generating message with success
        setMessages((prev) => {
          const newMessages = [...prev]
          newMessages[newMessages.length - 1] = {
            role: 'assistant',
            content: `🐍 Generated **${result.mode.toUpperCase()}** Python code. Click Execute to run it.\n\n**Estimated runtime**: ${result.estimated_runtime}`
          }
          return newMessages
        })
      } catch (error: any) {
        setIsGeneratingCode(false)
        // Replace generating message with error
        setMessages((prev) => {
          const newMessages = [...prev]
          newMessages[newMessages.length - 1] = {
            role: 'assistant',
            content: `❌ Failed to generate Python code: ${error.message}`
          }
          return newMessages
        })
      }
      return
    }

    // SQL mode (default)
    try {
      const result = await nlQueryMutation.mutateAsync({ datasetId: id!, query })
      setQueryResult(result)

      // Generate insights with context
      const insights = generateInsights(result, query)
      setMessages((prev) => [...prev, { role: 'assistant', content: insights }])

      // Switch to dashboard view to show results
      setCurrentView('dashboard')
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.message

      // Parse error message for better UX
      let friendlyError = '❌ Sorry, I encountered an error.\n\n'

      if (errorMsg.includes('Parser Error')) {
        friendlyError += '**SQL Syntax Issue**: The generated query has a syntax error. Try rephrasing your question.\n\n'
        friendlyError += '💡 Examples:\n'
        friendlyError += '• "Show me all records"\n'
        friendlyError += '• "Count total rows"\n'
        friendlyError += '• "What are the top 5 items by sales?"'
      } else if (errorMsg.includes('column')) {
        friendlyError += '**Column Not Found**: The query references a column that doesn\'t exist.\n\n'
        friendlyError += 'Check the **Spreadsheet** tab to see available columns.'
      } else {
        friendlyError += `**Error**: ${errorMsg.split('\n')[0]}`
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: friendlyError,
        },
      ])
    }
  }

  const handleExecutePython = async () => {
    if (!codePreview) return

    setIsExecuting(true)

    try {
      const result = await executePythonCode(codePreview.execution_id)

      setShowCodeModal(false)
      setIsExecuting(false)

      // Store execution details
      setLastExecution({
        code: codePreview.generated_code,
        result: result,
        mode: codePreview.mode
      })

      if (result.status === 'SUCCESS') {
        // Add success message with results
        let message = `✅ **Code executed successfully!**\n\n`

        if (result.output) {
          message += `**Results:**\n${JSON.stringify(result.output.summary || result.output, null, 2)}`
        }

        if (result.execution_time_ms) {
          message += `\n\n⏱️ Execution time: ${result.execution_time_ms}ms`
        }

        setMessages((prev) => [...prev, {
          role: 'assistant',
          content: message,
          executionResult: result
        }])

        // Show results in code tab
        setCurrentView('code')
      } else {
        setMessages((prev) => [...prev, {
          role: 'assistant',
          content: `❌ Execution failed: ${result.error || 'Unknown error'}`
        }])
      }
    } catch (error: any) {
      setIsExecuting(false)
      setShowCodeModal(false)
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: `❌ Execution failed: ${error.message}`
      }])
    }
  }

  if (!dataset) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p>Loading...</p>
      </div>
    )
  }

  // Prepare data for different views
  const spreadsheetData = preview || { columns: [], rows: [] }

  const dashboardQueryResult = queryResult
    ? {
        columns: Object.keys(queryResult.rows[0] || {}),
        rows: queryResult.rows,
        sql: queryResult.sql,
        execution_time_ms: queryResult.execution_time_ms,
        total_rows: queryResult.total_rows,
      }
    : undefined

  const charts = vizSuggestions?.suggestions || []

  return (
    <>
      {/* Code Preview Modal */}
      {codePreview && (
        <CodePreviewModal
          isOpen={showCodeModal}
          onClose={() => setShowCodeModal(false)}
          analysisResult={codePreview}
          onExecute={handleExecutePython}
          isExecuting={isExecuting}
        />
      )}

      {/* Dataset Overview Modal */}
      {dataset && (
        <DatasetOverviewModal
          isOpen={showOverviewModal}
          onClose={() => setShowOverviewModal(false)}
          dataset={dataset}
          description={overviewData}
        />
      )}

      {/* Dataset Settings Panel */}
      {showSettingsPanel && dataset && schema && (
        <DatasetSettingsPanel
          datasetId={id!}
          columns={schema.columns.map(col => ({ name: col.name, dtype: col.dtype }))}
          onClose={() => setShowSettingsPanel(false)}
        />
      )}

      {/* Plan Editor Modal */}
      {showPlanEditor && currentPlan && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <PlanEditor
            plan={currentPlan}
            onExecute={handleExecutePlan}
            onCancel={() => setShowPlanEditor(false)}
          />
        </div>
      )}

      {/* Share Modal */}
      {showShareModal && dataset && (
        <ShareModal
          datasetId={id!}
          datasetName={dataset.name}
          onClose={() => setShowShareModal(false)}
        />
      )}

      {/* Research History Modal */}
      <ResearchHistoryModal
        isOpen={showHistoryModal}
        onClose={() => setShowHistoryModal(false)}
        datasetId={id!}
        onLoadResearch={(report) => {
          setDeepResearchReport(report)
          setCurrentView('report')
        }}
      />

      {/* Load Workspace Dialog */}
      {showLoadDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Load Workspace</h3>
              <button
                onClick={() => setShowLoadDialog(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto">
              {savedWorkspaces.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <FolderOpen className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                  <p className="font-medium">No saved workspaces found</p>
                  <p className="text-sm mt-1">Create your first workspace by saving the current canvas</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {savedWorkspaces.map((workspace) => (
                    <button
                      key={workspace.id}
                      onClick={() => handleSelectWorkspace(workspace.id)}
                      className="w-full text-left p-4 border border-gray-200 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900">{workspace.name}</h4>
                          {workspace.description && (
                            <p className="text-sm text-gray-600 mt-1">{workspace.description}</p>
                          )}
                          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                            <span>Created: {new Date(workspace.created_at).toLocaleDateString()}</span>
                            <span>•</span>
                            <span>Updated: {new Date(workspace.updated_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                        <div className="text-blue-600 ml-4">
                          <FolderOpen className="h-5 w-5" />
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200">
              <button
                onClick={() => setShowLoadDialog(false)}
                className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      <DataWorkspaceLayout
        sidebar={
          <ChatSidebar
            datasetId={id}
            onQuerySubmit={handleQuerySubmit}
            messages={messages}
            isLoading={nlQueryMutation.isPending || isGeneratingCode || isExecuting || isStreaming}
            analysisMode={analysisMode}
            onModeChange={setAnalysisMode}
            verboseMode={verboseMode}
            onVerboseModeToggle={setVerboseMode}
            generateInfographic={generateInfographic}
            onInfographicToggle={setGenerateInfographic}
            infographicFormat={infographicFormat}
            onInfographicFormatChange={setInfographicFormat}
            infographicColorScheme={infographicColorScheme}
            onInfographicColorSchemeChange={setInfographicColorScheme}
            infographicGenerationMethod={infographicGenerationMethod}
            onInfographicGenerationMethodChange={setInfographicGenerationMethod}
          />
        }
        header={
          <div className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <IconButton
                  variant="ghost"
                  size="md"
                  tooltip="Back to Dataset Hub"
                  onClick={() => navigate('/')}
                >
                  <ArrowLeft className="h-5 w-5" />
                </IconButton>
                <div>
                  <h2 className="text-xl font-semibold">{dataset.name}</h2>
                  <p className="text-sm text-gray-500">
                    {dataset.row_count.toLocaleString()} rows • {dataset.source_type}
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  variant={canvasMode ? "default" : "outline"}
                  size="sm"
                  onClick={() => {
                    setCanvasMode(!canvasMode)
                    if (!canvasMode) {
                      setCurrentView('canvas')
                    } else {
                      setCurrentView('spreadsheet')
                    }
                  }}
                  className="flex items-center gap-2"
                >
                  <Layout className="h-4 w-4" />
                  {canvasMode ? 'Canvas Mode' : 'Tabs Mode'}
                </Button>
                <IconButton
                  variant="default"
                  size="md"
                  tooltip="Describe Dataset"
                  onClick={async () => {
                    const description = await describeDataset(id!)
                    setOverviewData(description)
                    setShowOverviewModal(true)
                  }}
                >
                  <Info className="h-5 w-5" />
                </IconButton>
                <IconButton
                  variant="default"
                  size="md"
                  tooltip="Research History"
                  onClick={() => setShowHistoryModal(true)}
                >
                  <History className="h-5 w-5" />
                </IconButton>
                {userRole?.can_share && (
                  <IconButton
                    variant="default"
                    size="md"
                    tooltip="Share Dataset"
                    onClick={() => setShowShareModal(true)}
                  >
                    <Share2 className="h-5 w-5" />
                  </IconButton>
                )}
                <IconButton
                  variant="primary"
                  size="md"
                  tooltip="Upload Dataset"
                  onClick={() => navigate('/')}
                >
                  <Upload className="h-5 w-5" />
                </IconButton>
                <IconButton
                  variant="default"
                  size="md"
                  tooltip="Settings"
                  onClick={() => setShowSettingsPanel(true)}
                >
                  <Settings className="h-5 w-5" />
                </IconButton>
              </div>
            </div>
          </div>
        }
      >
        {/* Canvas Mode or Tabs */}
        {canvasMode ? (
          <CanvasWorkspace
            workspaceId={id || 'temp'}
            items={canvasItems}
            onItemsChange={setCanvasItems}
            onLoad={handleLoadWorkspace}
            onSave={async (name: string, description?: string) => {
              try {
                console.log('Saving workspace...', { name, description, dataset_id: id })
                const token = localStorage.getItem('access_token')
                console.log('Token:', token ? `Present (${token.substring(0, 20)}...)` : 'Missing')

                if (!token) {
                  throw new Error('No authentication token found. Please log in again.')
                }

                // Create workspace via API with explicit auth header
                const response = await axios.post(
                  '/workspaces',
                  {
                    name,
                    description,
                    dataset_id: id
                  },
                  {
                    headers: {
                      Authorization: `Bearer ${token}`
                    }
                  }
                )
                console.log('Request headers:', response.config.headers)

                console.log('Workspace created:', response.data)
                const workspaceId = response.data.id

                // Save each canvas item
                console.log(`Saving ${canvasItems.length} canvas items...`)
                for (const item of canvasItems) {
                  await axios.post(
                    `/workspaces/${workspaceId}/items`,
                    {
                      type: item.type,
                      x: item.x,
                      y: item.y,
                      width: item.width,
                      height: item.height,
                      z_index: item.zIndex,
                      content: item.content
                    },
                    {
                      headers: {
                        Authorization: `Bearer ${token}`
                      }
                    }
                  )
                }

                console.log('All items saved successfully')
                alert(`✅ Workspace "${name}" saved successfully!`)
              } catch (error: any) {
                console.error('Failed to save workspace:', error)
                console.error('Error response:', error.response?.data)
                console.error('Error status:', error.response?.status)
                alert(`❌ Failed to save workspace: ${error.response?.data?.detail || error.message}`)
              }
            }}
          />
        ) : (
          <Tabs value={currentView} onValueChange={(v) => setCurrentView(v as any)} className="flex-1 flex flex-col overflow-hidden h-full">
            <div className="border-b border-gray-200 bg-gray-50 px-4">
              <TabsList className="bg-transparent">
                <TabsTrigger value="hub" className="gap-2">
                  <Sparkles className="h-4 w-4" />
                  Home
                </TabsTrigger>
                <TabsTrigger value="spreadsheet" className="gap-2">
                  <FileSpreadsheet className="h-4 w-4" />
                  Spreadsheet
                </TabsTrigger>
                <TabsTrigger value="schema" className="gap-2">
                  <Table2 className="h-4 w-4" />
                  Schema
                </TabsTrigger>
                <TabsTrigger value="dashboard" className="gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Dashboard
                  {queryResult && (
                    <span className="ml-1 px-1.5 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
                      {queryResult.total_rows}
                    </span>
                  )}
                </TabsTrigger>
                <TabsTrigger value="report" className="gap-2">
                  <FileText className="h-4 w-4" />
                  Report
                  {deepResearchReport && (
                    <span className="ml-1 px-1.5 py-0.5 text-xs bg-purple-100 text-purple-700 rounded">
                      New
                    </span>
                  )}
                </TabsTrigger>
                <TabsTrigger value="code" className="gap-2">
                  <Code2 className="h-4 w-4" />
                  Code
                  {lastExecution && (
                    <span className={`ml-1 px-1.5 py-0.5 text-xs rounded ${
                      lastExecution.result?.status === 'SUCCESS'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-red-100 text-red-700'
                    }`}>
                      {lastExecution.result?.status || 'N/A'}
                    </span>
                  )}
                </TabsTrigger>
              </TabsList>
            </div>

          {/* Hub View - AI Suggestions and Quick Start */}
          <TabsContent value="hub" className="flex-1 m-0 overflow-hidden">
            <DatasetHub
              datasetId={id!}
              datasetName={dataset.name}
              onQuerySelect={handleQuerySubmit}
            />
          </TabsContent>

          {/* Spreadsheet View - Always shows original dataset */}
          <TabsContent value="spreadsheet" className="flex-1 m-0 p-6 overflow-auto">
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-700">Original Dataset Preview</h3>
              <p className="text-xs text-gray-500">Showing first 100 rows of the uploaded data</p>
            </div>
            <SpreadsheetView data={spreadsheetData} />
          </TabsContent>

          {/* Schema View - Shows column metadata */}
          <TabsContent value="schema" className="flex-1 m-0 overflow-auto">
            <SchemaView datasetId={id!} />
          </TabsContent>

          {/* Dashboard View - Shows query results + charts */}
          <TabsContent value="dashboard" className="flex-1 m-0 overflow-auto">
            <DashboardView queryResult={dashboardQueryResult} charts={charts} />
          </TabsContent>

          {/* Report View - Shows Deep Research report */}
          <TabsContent value="report" className="flex-1 m-0 overflow-hidden flex flex-col">
            {deepResearchReport && (
              <div className="border-b border-gray-200 bg-gray-50 px-6 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900 text-lg">Deep Research Report</h3>
                    <p className="text-sm text-gray-600 mt-1">{deepResearchReport.main_question}</p>
                  </div>

                  {/* Infographic Download Button */}
                  {currentInfographic && (
                    <button
                      onClick={() => {
                        // Download infographic
                        const { data, format, filename } = currentInfographic

                        try {
                          // Convert base64 to blob
                          const byteCharacters = atob(data)
                          const byteNumbers = new Array(byteCharacters.length)
                          for (let i = 0; i < byteCharacters.length; i++) {
                            byteNumbers[i] = byteCharacters.charCodeAt(i)
                          }
                          const byteArray = new Uint8Array(byteNumbers)
                          const mimeType = format === 'pdf' ? 'application/pdf' : 'image/png'
                          const blob = new Blob([byteArray], { type: mimeType })

                          // Trigger download
                          const url = URL.createObjectURL(blob)
                          const link = document.createElement('a')
                          link.href = url
                          link.download = filename
                          link.click()
                          URL.revokeObjectURL(url)
                        } catch (error) {
                          console.error('Download failed:', error)
                          alert('Failed to download infographic')
                        }
                      }}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg flex items-center gap-2 text-sm font-medium transition-colors shadow-sm"
                    >
                      <span>📊</span>
                      <span>Download {currentInfographic.format.toUpperCase()} Infographic</span>
                      <span className="text-xs opacity-90 ml-1">
                        ({(currentInfographic.size_bytes / 1024).toFixed(1)} KB)
                      </span>
                    </button>
                  )}
                </div>
              </div>
            )}
            <div className="flex-1 overflow-hidden">
              <ReportView report={deepResearchReport} />
            </div>
          </TabsContent>

          {/* Code View - Shows Python code and execution details */}
          <TabsContent value="code" className="flex-1 m-0 p-6 overflow-auto">
            {lastExecution ? (
              <div className="space-y-6">
                {/* Execution Summary */}
                <div className="border-b border-gray-200 pb-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold">Execution Details</h3>
                    <div className="flex items-center gap-2">
                      <span className="text-xs bg-blue-100 text-blue-700 px-2.5 py-1 rounded-md font-medium">
                        {lastExecution.mode.toUpperCase()} Mode
                      </span>
                      <span className={`text-xs px-2.5 py-1 rounded-md font-semibold ${
                        lastExecution.result?.status === 'SUCCESS'
                          ? 'bg-green-500 text-white'
                          : 'bg-red-500 text-white'
                      }`}>
                        {lastExecution.result?.status || 'PENDING'}
                      </span>
                    </div>
                  </div>

                  {lastExecution.result?.execution_time_ms && (
                    <p className="text-sm text-gray-600 mt-3">
                      <Info className="h-3.5 w-3.5 inline mr-1" />
                      Execution time: <strong>{lastExecution.result.execution_time_ms}ms</strong>
                    </p>
                  )}
                </div>

                {/* Generated Code */}
                <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                  <div className="bg-gray-800 px-4 py-2 flex items-center justify-between">
                    <span className="text-xs text-gray-300">Python Code</span>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(lastExecution.code)
                      }}
                      className="text-xs text-blue-400 hover:text-blue-300"
                    >
                      Copy Code
                    </button>
                  </div>
                  <pre className="p-4 text-sm bg-gray-900 text-gray-100 overflow-x-auto">
                    <code>{lastExecution.code}</code>
                  </pre>
                </div>

                {/* Execution Results */}
                {lastExecution.result?.output && (
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <h4 className="font-semibold mb-3">Output</h4>
                    <div className="space-y-3">
                      {lastExecution.result.output.summary && (
                        <div className="bg-green-50 border border-green-200 rounded p-3">
                          <p className="text-sm text-green-800">{lastExecution.result.output.summary}</p>
                        </div>
                      )}

                      {lastExecution.result.output.metrics && (
                        <div>
                          <h5 className="text-sm font-medium text-gray-700 mb-2">Metrics</h5>
                          <div className="bg-gray-50 rounded p-3">
                            <pre className="text-xs text-gray-800">
                              {JSON.stringify(lastExecution.result.output.metrics, null, 2)}
                            </pre>
                          </div>
                        </div>
                      )}

                      {lastExecution.result.output.data && (
                        <div>
                          <h5 className="text-sm font-medium text-gray-700 mb-2">Data</h5>
                          <div className="bg-gray-50 rounded p-3 max-h-96 overflow-auto">
                            <pre className="text-xs text-gray-800">
                              {JSON.stringify(lastExecution.result.output.data, null, 2)}
                            </pre>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Visualizations */}
                {lastExecution.result?.visualizations && lastExecution.result.visualizations.length > 0 && (
                  <div className="bg-white border border-gray-200 rounded-lg p-4">
                    <h4 className="font-semibold mb-3">Visualizations</h4>
                    <div className="space-y-4">
                      {lastExecution.result.visualizations.map((viz, idx) => (
                        <div key={idx} className="border border-gray-200 rounded p-2">
                          <img
                            src={`data:image/png;base64,${viz.data}`}
                            alt={`Visualization ${idx + 1}`}
                            className="max-w-full h-auto"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Error Details */}
                {lastExecution.result?.error && (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <h4 className="font-semibold text-red-800 mb-2">Error</h4>
                    <p className="text-sm text-red-700">{lastExecution.result.error}</p>
                    {lastExecution.result.error_trace && (
                      <pre className="mt-3 text-xs text-red-600 bg-red-100 p-3 rounded overflow-x-auto">
                        {lastExecution.result.error_trace}
                      </pre>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-gray-500">
                <Code2 className="h-16 w-16 mb-4 text-gray-300" />
                <p className="text-lg font-medium">No Python code executed yet</p>
                <p className="text-sm mt-2">Switch to Python mode and run some code to see execution details here</p>
              </div>
            )}
          </TabsContent>
          </Tabs>
        )}
      </DataWorkspaceLayout>
    </>
  )
}
