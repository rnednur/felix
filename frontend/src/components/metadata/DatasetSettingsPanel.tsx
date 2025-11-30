import { useState } from 'react'
import { Settings, Table2, Shield, Info, Sparkles, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { ColumnMetadataEditor } from './ColumnMetadataEditor'
import { QueryRulesManager } from './QueryRulesManager'
import { AIMetadataSuggestions } from './AIMetadataSuggestions'
import { aiDescribeColumns, ColumnMetadataSuggestion, getColumnMetadata } from '@/services/api'
import { useQuery } from '@tanstack/react-query'

interface Column {
  name: string
  dtype: string
}

interface Props {
  datasetId: string
  columns: Column[]
  onClose: () => void
}

export function DatasetSettingsPanel({ datasetId, columns, onClose }: Props) {
  const [activeTab, setActiveTab] = useState<'metadata' | 'rules' | 'general'>('metadata')
  const [selectedColumn, setSelectedColumn] = useState<string | null>(null)
  const [aiSuggestions, setAiSuggestions] = useState<ColumnMetadataSuggestion[] | null>(null)
  const [isLoadingAI, setIsLoadingAI] = useState(false)
  const [aiError, setAiError] = useState<string | null>(null)

  // Fetch existing metadata
  const { data: existingMetadata, refetch: refetchMetadata } = useQuery({
    queryKey: ['column-metadata', datasetId],
    queryFn: () => getColumnMetadata(datasetId),
    enabled: !!datasetId,
  })

  // Create a map of existing metadata
  const metadataMap = new Map()
  if (existingMetadata) {
    existingMetadata.forEach((m: any) => {
      metadataMap.set(m.column_name, m)
    })
  }

  const handleEditColumn = (columnName: string) => {
    setSelectedColumn(columnName)
  }

  const handleAIDescribe = async () => {
    setIsLoadingAI(true)
    setAiError(null)
    try {
      const result = await aiDescribeColumns(datasetId)
      if (result.success) {
        setAiSuggestions(result.suggestions)
      } else {
        setAiError('Failed to generate AI descriptions')
      }
    } catch (error: any) {
      setAiError(error.message || 'Failed to generate AI descriptions')
    } finally {
      setIsLoadingAI(false)
    }
  }

  const handleAcceptSuggestion = async (columnName: string, metadata: Partial<ColumnMetadataSuggestion>) => {
    try {
      const payload = {
        column_name: columnName,
        ...metadata
      }

      console.log('Updating column metadata:', columnName, payload)

      const response = await fetch(`http://localhost:8000/api/v1/metadata/datasets/${datasetId}/columns/${columnName}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        const error = await response.json()
        console.error('Failed to update column metadata:', error)
        throw new Error(error.detail || 'Failed to update column metadata')
      }

      const result = await response.json()
      console.log('Successfully updated column:', columnName, result)
    } catch (error) {
      console.error('Failed to update column:', error)
      throw error
    }
  }

  const handleAcceptAllSuggestions = async (updates: Record<string, Partial<ColumnMetadataSuggestion>>) => {
    try {
      console.log('Accepting all suggestions:', updates)

      await Promise.all(
        Object.entries(updates).map(([columnName, metadata]) =>
          handleAcceptSuggestion(columnName, metadata)
        )
      )

      console.log('All columns updated successfully')
      setAiSuggestions(null)
      setAiError(null)

      // Refetch metadata to show updates
      await refetchMetadata()

      // Show success message
      alert(`Successfully updated metadata for ${Object.keys(updates).length} columns!`)
    } catch (error: any) {
      console.error('Failed to update columns:', error)
      setAiError(`Failed to save metadata: ${error.message}`)
    }
  }

  if (aiSuggestions) {
    return (
      <AIMetadataSuggestions
        suggestions={aiSuggestions}
        onAccept={handleAcceptSuggestion}
        onAcceptAll={handleAcceptAllSuggestions}
        onCancel={() => setAiSuggestions(null)}
      />
    )
  }

  if (selectedColumn) {
    return (
      <ColumnMetadataEditor
        datasetId={datasetId}
        columnName={selectedColumn}
        onClose={() => setSelectedColumn(null)}
        onSave={() => setSelectedColumn(null)}
      />
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="border-b px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Settings className="w-6 h-6 text-gray-600" />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Dataset Settings</h2>
              <p className="text-sm text-gray-600 mt-1">
                Configure metadata, rules, and general settings
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors text-2xl font-light leading-none"
          >
            ×
          </button>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as any)} className="flex-1 flex flex-col overflow-hidden">
          <div className="border-b bg-gray-50 px-6">
            <TabsList className="bg-transparent">
              <TabsTrigger value="metadata" className="gap-2">
                <Table2 className="h-4 w-4" />
                Column Metadata
              </TabsTrigger>
              <TabsTrigger value="rules" className="gap-2">
                <Shield className="h-4 w-4" />
                Query Rules
              </TabsTrigger>
              <TabsTrigger value="general" className="gap-2">
                <Info className="h-4 w-4" />
                General
              </TabsTrigger>
            </TabsList>
          </div>

          {/* Metadata Tab */}
          <TabsContent value="metadata" className="flex-1 overflow-y-auto p-6 m-0">
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-semibold text-gray-900">Column Metadata</h3>
                <Button
                  onClick={handleAIDescribe}
                  disabled={isLoadingAI}
                  className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                >
                  <Sparkles className="h-4 w-4 mr-2" />
                  {isLoadingAI ? 'Generating...' : 'AI Describe All'}
                </Button>
              </div>
              <p className="text-sm text-gray-600">
                Add descriptions, business definitions, and semantic types to your columns to improve query accuracy.
              </p>
            </div>

            {aiError && (
              <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-800">{aiError}</p>
              </div>
            )}

            <div className="space-y-2 mb-6">
              {columns.map((col) => {
                const hasMetadata = metadataMap.has(col.name)
                const colMeta = metadataMap.get(col.name)

                return (
                  <button
                    key={col.name}
                    onClick={() => handleEditColumn(col.name)}
                    className={`w-full text-left px-4 py-3 border rounded-lg transition-colors group ${
                      hasMetadata
                        ? 'border-green-200 bg-green-50 hover:bg-green-100'
                        : 'hover:bg-blue-50 hover:border-blue-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm font-medium text-gray-900">
                            {col.name}
                          </span>
                          <span className="text-xs text-gray-500">({col.dtype})</span>
                          {hasMetadata && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-600 text-white text-xs rounded">
                              <Check className="h-3 w-3" />
                              Configured
                            </span>
                          )}
                        </div>
                        {colMeta?.description && (
                          <p className="text-xs text-gray-600 mt-1 line-clamp-1">
                            {colMeta.description}
                          </p>
                        )}
                      </div>
                      <span className="text-xs text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity">
                        Edit →
                      </span>
                    </div>
                  </button>
                )
              })}
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">💡 Why add metadata?</h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Helps AI understand your data context and generate better queries</li>
                <li>• Provides business definitions that improve interpretation</li>
                <li>• Enables smarter aggregations and visualizations</li>
              </ul>
            </div>
          </TabsContent>

          {/* Rules Tab */}
          <TabsContent value="rules" className="flex-1 overflow-hidden m-0">
            <QueryRulesManager
              datasetId={datasetId}
              onClose={onClose}
            />
          </TabsContent>

          {/* General Tab */}
          <TabsContent value="general" className="flex-1 overflow-y-auto p-6 m-0">
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">General Settings</h3>
              <p className="text-sm text-gray-600">
                Configure general dataset preferences and behavior.
              </p>
            </div>

            <div className="space-y-6">
              <div className="border rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-3">Dataset Information</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-gray-600">Dataset ID</span>
                    <span className="font-mono text-gray-900">{datasetId}</span>
                  </div>
                  <div className="flex justify-between py-2 border-b">
                    <span className="text-gray-600">Total Columns</span>
                    <span className="font-medium text-gray-900">{columns.length}</span>
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">📋 Quick Tips</h4>
                <ul className="text-sm text-gray-700 space-y-2">
                  <li>• Use the <strong>Column Metadata</strong> tab to add descriptions and semantic types</li>
                  <li>• Set up <strong>Query Rules</strong> to automatically filter data or exclude sensitive columns</li>
                  <li>• Metadata improvements are applied immediately to all future queries</li>
                </ul>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
