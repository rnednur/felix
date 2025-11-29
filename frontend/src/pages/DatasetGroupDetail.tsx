import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, FileSpreadsheet, BarChart3, Table2, FileText, Database } from 'lucide-react'
import { DatasetGroupManager } from '@/components/datasets/DatasetGroupManager'
import { useDatasetGroup, useDatasetGroupSchemas, useDatasetGroupPreview } from '@/hooks/useDatasetGroups'
import { useNLQuery } from '@/hooks/useQuery'
import { useVisualizationSuggestions } from '@/hooks/useVisualization'
import { ChatSidebar, type AnalysisMode } from '@/components/chat/ChatSidebar'
import { SpreadsheetView } from '@/components/canvas/SpreadsheetView'
import { DashboardView } from '@/components/canvas/DashboardView'
import { ReportView } from '@/components/canvas/ReportView'
import { GroupSchemaView } from '@/components/canvas/GroupSchemaView'
import { GroupDataPreview } from '@/components/canvas/GroupDataPreview'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { IconButton } from '@/components/ui/icon-button'
import { generatePythonCode, executePythonCode, executeDeepResearch, type PythonAnalysisResult, type ExecutionResult } from '@/services/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  code?: string
  executionResult?: ExecutionResult
}

export default function DatasetGroupDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: group } = useDatasetGroup(id === 'new' ? undefined : id)
  const { data: schemas, isLoading: schemasLoading } = useDatasetGroupSchemas(id === 'new' ? undefined : id)
  const { data: previews, isLoading: previewsLoading } = useDatasetGroupPreview(id === 'new' ? undefined : id)

  // If it's a new group page, always show manager
  const isNewGroup = id === 'new'
  const [showManager, setShowManager] = useState(false)  // Start collapsed
  const [messages, setMessages] = useState<Message[]>([])
  const [currentView, setCurrentView] = useState<'preview' | 'spreadsheet' | 'schema' | 'dashboard' | 'report'>('preview')
  const [queryResult, setQueryResult] = useState<any>(null)
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('auto')
  const [isExecuting, setIsExecuting] = useState(false)
  const [isGeneratingCode, setIsGeneratingCode] = useState(false)
  const [deepResearchReport, setDeepResearchReport] = useState<any>(null)
  const [verboseMode, setVerboseMode] = useState(true)

  const nlQueryMutation = useNLQuery()
  const { data: vizSuggestions } = useVisualizationSuggestions(queryResult?.query_id)
  const charts = vizSuggestions?.suggestions || []

  const generateInsights = (result: any, originalQuery: string): string => {
    const { rows, total_rows } = result
    if (rows.length === 0) return 'No results found for your query.'

    let insights: string[] = []
    insights.push(`✅ Found **${total_rows} ${total_rows === 1 ? 'result' : 'results'}** across multiple datasets.`)

    if (result.datasets_used && result.datasets_used.length > 0) {
      insights.push(`\n📊 Used tables: **${result.datasets_used.join(', ')}**`)
    }

    if (result.sql) {
      insights.push(`\n💡 View the SQL and visualizations in the **Dashboard** tab.`)
    }

    return insights.join('\n')
  }

  const handleMessage = async (content: string) => {
    if (!id || isNewGroup) return

    setMessages((prev) => [...prev, { role: 'user', content }])

    if (analysisMode === 'sql') {
      try {
        const result = await nlQueryMutation.mutateAsync({
          query: content,
          groupId: id
        })

        setQueryResult(result)

        const responseText = generateInsights(result, content)
        setMessages((prev) => [...prev, { role: 'assistant', content: responseText }])

        setCurrentView('dashboard')
      } catch (err: any) {
        const errorMessage = err?.response?.data?.detail || err.message || 'Query failed'
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `❌ ${errorMessage}` }
        ])
      }
    } else if (analysisMode === 'python') {
      // Python mode - requires selecting a single dataset from the group
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '⚠️ Python analysis requires a single dataset. Please select a dataset from the group or use SQL mode for multi-table queries.' }
      ])
    } else if (analysisMode === 'research') {
      // Deep research mode
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: '🔍 Starting deep research across all datasets in this group...' }
      ])

      try {
        setIsExecuting(true)

        // Get first dataset from group for now - could be enhanced to research across all
        const firstDatasetId = group?.memberships[0]?.dataset_id

        if (!firstDatasetId) {
          throw new Error('No datasets in this group')
        }

        const result = await executeDeepResearch(firstDatasetId, content, verboseMode)

        setDeepResearchReport(result)
        setCurrentView('report')
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: '✅ Research complete! View the full report in the **Report** tab.' }
        ])
      } catch (err: any) {
        const errorMessage = err?.response?.data?.detail || err.message || 'Research failed'
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `❌ ${errorMessage}` }
        ])
      } finally {
        setIsExecuting(false)
      }
    } else {
      // Auto mode - default to SQL for groups
      try {
        const result = await nlQueryMutation.mutateAsync({
          query: content,
          groupId: id
        })

        setQueryResult(result)

        const responseText = generateInsights(result, content)
        setMessages((prev) => [...prev, { role: 'assistant', content: responseText }])

        setCurrentView('dashboard')
      } catch (err: any) {
        const errorMessage = err?.response?.data?.detail || err.message || 'Query failed'
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', content: `❌ ${errorMessage}` }
        ])
      }
    }
  }

  const prepareSpreadsheetData = () => {
    if (!queryResult || !queryResult.rows || queryResult.rows.length === 0) {
      return { columns: [], rows: [] }
    }

    const columns = Object.keys(queryResult.rows[0])
    return {
      columns,
      rows: queryResult.rows
    }
  }

  const prepareDashboardData = () => {
    if (!queryResult || !queryResult.rows || queryResult.rows.length === 0) {
      return null
    }

    const columns = Object.keys(queryResult.rows[0])
    return {
      columns,
      rows: queryResult.rows,
      sql: queryResult.sql,
      execution_time_ms: queryResult.execution_time_ms,
      total_rows: queryResult.total_rows
    }
  }

  return (
    <div className="flex h-screen bg-white overflow-hidden">
      {/* Chat Sidebar - LEFT SIDE */}
      {!isNewGroup && (
        <ChatSidebar
          datasetId={id}
          messages={messages}
          onQuerySubmit={handleMessage}
          analysisMode={analysisMode}
          onModeChange={setAnalysisMode}
          isLoading={nlQueryMutation.isPending || isExecuting || isGeneratingCode}
          verboseMode={verboseMode}
          onVerboseModeToggle={setVerboseMode}
        />
      )}

      {/* Main Content - RIGHT SIDE */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Header */}
        <div className="border-b border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/')}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </button>
              <div>
                <h2 className="text-xl font-semibold">{group?.name || 'Dataset Group'}</h2>
                {group?.description && (
                  <p className="text-sm text-gray-500">{group.description}</p>
                )}
                {group?.memberships && (
                  <p className="text-xs text-gray-500 mt-1">
                    {group.memberships.length} dataset{group.memberships.length !== 1 ? 's' : ''} • Multi-table analysis
                  </p>
                )}
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowManager(!showManager)}
                className="px-3 py-2 text-sm border rounded hover:bg-gray-50"
              >
                {showManager ? 'Hide Manager' : 'Manage Datasets'}
              </button>
            </div>
          </div>
        </div>

        {/* Manager Section (Collapsible) */}
        {showManager && (
          <div className="bg-gray-50 border-b border-gray-200 p-6">
            <DatasetGroupManager />
          </div>
        )}

        {/* Content Area */}
        {isNewGroup ? (
          <div className="flex-1 flex items-center justify-center bg-gray-50">
            <div className="text-center">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Create a Dataset Group</h2>
              <p className="text-gray-600 mb-4">Use the manager above to create and configure your dataset group</p>
            </div>
          </div>
        ) : (
          <Tabs value={currentView} onValueChange={(v) => setCurrentView(v as any)} className="flex-1 flex flex-col overflow-hidden">
            {/* Tab List */}
            <div className="border-b border-gray-200 bg-gray-50 px-4">
              <TabsList className="bg-transparent">
                <TabsTrigger value="preview" className="gap-2">
                  <Database className="h-4 w-4" />
                  Preview
                </TabsTrigger>
                <TabsTrigger value="schema" className="gap-2">
                  <Table2 className="h-4 w-4" />
                  Schema
                </TabsTrigger>
                <TabsTrigger value="spreadsheet" className="gap-2">
                  <FileSpreadsheet className="h-4 w-4" />
                  Query Results
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
              </TabsList>
            </div>

            {/* Tab Content */}
            <TabsContent value="preview" className="flex-1 m-0 overflow-auto">
              {previewsLoading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-gray-500">Loading preview...</div>
                </div>
              ) : previews && previews.length > 0 ? (
                <GroupDataPreview previews={previews} />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  No preview data available. Add datasets to this group.
                </div>
              )}
            </TabsContent>
            <TabsContent value="schema" className="flex-1 m-0 overflow-auto">
              {schemasLoading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-gray-500">Loading schemas...</div>
                </div>
              ) : schemas && schemas.length > 0 ? (
                <GroupSchemaView schemas={schemas} />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  No schemas available. Add datasets to this group.
                </div>
              )}
            </TabsContent>
            <TabsContent value="spreadsheet" className="flex-1 m-0 p-6 overflow-auto">
              <SpreadsheetView data={prepareSpreadsheetData()} />
            </TabsContent>
            <TabsContent value="dashboard" className="flex-1 m-0 overflow-auto">
              <DashboardView queryResult={prepareDashboardData()} charts={charts} />
            </TabsContent>
            <TabsContent value="report" className="flex-1 m-0 overflow-auto">
              <ReportView report={deepResearchReport} />
            </TabsContent>
          </Tabs>
        )}
      </div>
    </div>
  )
}
