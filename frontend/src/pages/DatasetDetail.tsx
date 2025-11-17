import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useDataset, useDatasetPreview } from '@/hooks/useDatasets'
import { useNLQuery } from '@/hooks/useQuery'
import { useVisualizationSuggestions } from '@/hooks/useVisualization'
import { ChatSidebar, type AnalysisMode } from '@/components/chat/ChatSidebar'
import { SpreadsheetView } from '@/components/canvas/SpreadsheetView'
import { DashboardView } from '@/components/canvas/DashboardView'
import { SchemaView } from '@/components/canvas/SchemaView'
import { ReportView } from '@/components/canvas/ReportView'
import { CodePreviewModal } from '@/components/python/CodePreviewModal'
import { DatasetOverviewModal } from '@/components/datasets/DatasetOverviewModal'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { FileSpreadsheet, BarChart3, Settings, Info, Table2, Code2, Upload, FileText } from 'lucide-react'
import { describeDataset, generatePythonCode, executePythonCode, executeDeepResearch, type PythonAnalysisResult, type ExecutionResult, type DeepResearchResult } from '@/services/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  code?: string
  executionResult?: ExecutionResult
}

export default function DatasetDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: dataset } = useDataset(id!)
  const { data: preview } = useDatasetPreview(id!)
  const [messages, setMessages] = useState<Message[]>([])
  const [currentView, setCurrentView] = useState<'spreadsheet' | 'dashboard' | 'schema' | 'code' | 'report'>('spreadsheet')
  const [queryResult, setQueryResult] = useState<any>(null)
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>('auto')
  const [codePreview, setCodePreview] = useState<PythonAnalysisResult | null>(null)
  const [showCodeModal, setShowCodeModal] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)
  const [isGeneratingCode, setIsGeneratingCode] = useState(false)
  const [deepResearchReport, setDeepResearchReport] = useState<any>(null)
  const [showOverviewModal, setShowOverviewModal] = useState(false)
  const [overviewData, setOverviewData] = useState<any>(null)
  const [lastExecution, setLastExecution] = useState<{
    code: string
    result: ExecutionResult | null
    mode: string
  } | null>(null)

  const nlQueryMutation = useNLQuery()
  const { data: vizSuggestions } = useVisualizationSuggestions(queryResult?.query_id)

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

  const handleQuerySubmit = async (query: string, mode: AnalysisMode = 'auto') => {
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
        content: '🧠 Starting deep research analysis...\n\n**Progress:**\n⏳ Initializing...'
      }])

      try {
        const apiUrl = import.meta.env.VITE_API_URL || '/api/v1'
        const eventSource = new EventSource(
          `${apiUrl}/deep-research/analyze-stream?` + new URLSearchParams({
            dataset_id: id!,
            question: query,
            max_sub_questions: '10',
            enable_python: 'true',
            enable_world_knowledge: 'true'
          })
        )

        eventSource.onmessage = (event) => {
          const data = JSON.parse(event.data)

          if (data.type === 'complete') {
            // Research completed
            eventSource.close()
            const result = data.result

            // Format comprehensive response
            let response = `## ${result.main_question}\n\n`
            response += `**Direct Answer:**\n${result.direct_answer}\n\n`

            if (result.key_findings?.length > 0) {
              response += `**Key Findings:**\n`
              result.key_findings.forEach((finding: string, idx: number) => {
                response += `${idx + 1}. ${finding}\n`
              })
              response += '\n'
            }

            // Add visualizations section
            if (result.visualizations?.length > 0) {
              response += `**Visualizations:**\n\n`
              result.visualizations.forEach((viz: any, idx: number) => {
                response += `<div class="visualization-container" style="margin: 16px 0; padding: 12px; background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">\n`
                response += `<p style="font-size: 13px; color: #6b7280; margin-bottom: 8px;"><strong>Figure ${idx + 1}:</strong> ${viz.caption}</p>\n`
                response += `<img src="data:${viz.format === 'png' ? 'image/png' : 'image/jpeg'};base64,${viz.data}" style="max-width: 100%; height: auto; border-radius: 4px;" />\n`
                response += `</div>\n\n`
              })
            }

            if (result.data_coverage) {
              response += `**Data Coverage:**\n`
              if (result.data_coverage.questions_answered) {
                response += `✅ Answered: ${result.data_coverage.questions_answered} sub-questions\n`
              }
              if (result.data_coverage.gaps?.length > 0) {
                response += `⚠️ Gaps: ${result.data_coverage.gaps.join(', ')}\n`
              }
              response += '\n'
            }

            if (result.follow_up_questions?.length > 0) {
              response += `**Suggested Follow-ups:**\n`
              result.follow_up_questions.forEach((q: string, idx: number) => {
                response += `${idx + 1}. ${q}\n`
              })
            }

            response += `\n_Analysis completed in ${result.execution_time_seconds.toFixed(1)}s_`

            // Save the full report data
            setDeepResearchReport(result)

            // Switch to report view
            setCurrentView('report')

            // Replace loading message with result
            setMessages((prev) => {
              const newMessages = [...prev]
              newMessages[newMessages.length - 1] = {
                role: 'assistant',
                content: `✅ Deep research complete! View the full report in the **Report** tab.`
              }
              return newMessages
            })
          } else if (data.type === 'error') {
            // Error occurred
            eventSource.close()
            setMessages((prev) => {
              const newMessages = [...prev]
              newMessages[newMessages.length - 1] = {
                role: 'assistant',
                content: `❌ Deep research error: ${data.error}`
              }
              return newMessages
            })
          } else if (data.stage) {
            // Progress update
            const progressBar = '█'.repeat(data.stage) + '░'.repeat(6 - data.stage)
            const progress = `🧠 Deep Research in progress...\n\n**Stage ${data.stage}/6:** ${data.message}\n\n${progressBar} ${Math.round(data.stage / 6 * 100)}%`

            setMessages((prev) => {
              const newMessages = [...prev]
              newMessages[newMessages.length - 1] = {
                role: 'assistant',
                content: progress
              }
              return newMessages
            })
          }
        }

        eventSource.onerror = (error) => {
          console.error('EventSource error:', error)
          eventSource.close()
          setMessages((prev) => {
            const newMessages = [...prev]
            newMessages[newMessages.length - 1] = {
              role: 'assistant',
              content: '❌ Connection error during deep research'
            }
            return newMessages
          })
        }
      } catch (error: any) {
        setMessages((prev) => {
          const newMessages = [...prev]
          newMessages[newMessages.length - 1] = {
            role: 'assistant',
            content: `❌ Deep research error: ${error.message || 'Unknown error'}`
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
    <div className="flex h-screen bg-white overflow-hidden">
      {/* Chat Sidebar */}
      <ChatSidebar
        datasetId={id}
        onQuerySubmit={handleQuerySubmit}
        messages={messages}
        isLoading={nlQueryMutation.isPending || isGeneratingCode || isExecuting}
        analysisMode={analysisMode}
        onModeChange={setAnalysisMode}
      />

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

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top Bar */}
        <div className="border-b border-gray-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">{dataset.name}</h2>
              <p className="text-sm text-gray-500">
                {dataset.row_count.toLocaleString()} rows • {dataset.source_type}
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={async () => {
                  const description = await describeDataset(id!)
                  setOverviewData(description)
                  setShowOverviewModal(true)
                }}
              >
                <Info className="h-4 w-4 mr-2" />
                Describe Dataset
              </Button>
              <Button
                className="bg-blue-600 hover:bg-blue-700 text-white"
                onClick={() => window.location.href = '/'}
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload Dataset
              </Button>
              <Button variant="outline">
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={currentView} onValueChange={(v) => setCurrentView(v as any)} className="flex-1 flex flex-col overflow-hidden">
          <div className="border-b border-gray-200 bg-gray-50 px-4">
            <TabsList className="bg-transparent">
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
          <TabsContent value="report" className="flex-1 m-0 overflow-hidden">
            <ReportView report={deepResearchReport} />
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
      </div>
    </div>
  )
}
