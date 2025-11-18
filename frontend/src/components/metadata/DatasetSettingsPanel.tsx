import { useState } from 'react'
import { Settings, Table2, Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ColumnMetadataEditor } from './ColumnMetadataEditor'
import { QueryRulesManager } from './QueryRulesManager'

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
  const [view, setView] = useState<'main' | 'column-metadata' | 'query-rules'>('main')
  const [selectedColumn, setSelectedColumn] = useState<string | null>(null)

  const handleEditColumn = (columnName: string) => {
    setSelectedColumn(columnName)
    setView('column-metadata')
  }

  if (view === 'column-metadata' && selectedColumn) {
    return (
      <ColumnMetadataEditor
        datasetId={datasetId}
        columnName={selectedColumn}
        onClose={() => {
          setSelectedColumn(null)
          setView('main')
        }}
        onSave={() => {
          setSelectedColumn(null)
          setView('main')
        }}
      />
    )
  }

  if (view === 'query-rules') {
    return (
      <QueryRulesManager
        datasetId={datasetId}
        onClose={() => setView('main')}
      />
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Settings className="w-6 h-6 text-gray-600" />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Dataset Settings</h2>
              <p className="text-sm text-gray-600 mt-1">
                Configure metadata and query rules
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors text-xl"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Column Metadata Section */}
            <div className="border rounded-lg p-6 hover:border-blue-500 transition-colors">
              <div className="flex items-center gap-3 mb-4">
                <Table2 className="w-6 h-6 text-blue-600" />
                <h3 className="text-lg font-semibold text-gray-900">Column Metadata</h3>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Add descriptions, business definitions, and semantic types to your columns to improve query accuracy.
              </p>

              <div className="max-h-64 overflow-y-auto space-y-2 mb-4">
                {columns.map((col) => (
                  <button
                    key={col.name}
                    onClick={() => handleEditColumn(col.name)}
                    className="w-full text-left px-3 py-2 border rounded hover:bg-blue-50 hover:border-blue-300 transition-colors group"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-mono text-sm font-medium text-gray-900">
                          {col.name}
                        </span>
                        <span className="text-xs text-gray-500 ml-2">({col.dtype})</span>
                      </div>
                      <span className="text-xs text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity">
                        Edit →
                      </span>
                    </div>
                  </button>
                ))}
              </div>

              <p className="text-xs text-gray-500 italic">
                Click on any column to edit its metadata
              </p>
            </div>

            {/* Query Rules Section */}
            <div className="border rounded-lg p-6 hover:border-purple-500 transition-colors">
              <div className="flex items-center gap-3 mb-4">
                <Shield className="w-6 h-6 text-purple-600" />
                <h3 className="text-lg font-semibold text-gray-900">Query Rules</h3>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Set up automatic filters and exclusions that apply to all queries on this dataset.
              </p>

              <div className="space-y-3 mb-6">
                <div className="flex items-start gap-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full mt-1.5"></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">Always Apply Filters</p>
                    <p className="text-xs text-gray-600">
                      Add WHERE clause conditions to every query
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full mt-1.5"></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">Exclude Columns</p>
                    <p className="text-xs text-gray-600">
                      Hide sensitive columns from all queries
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full mt-1.5"></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">Required Conditions</p>
                    <p className="text-xs text-gray-600">
                      Enforce business rules automatically
                    </p>
                  </div>
                </div>
              </div>

              <Button
                onClick={() => setView('query-rules')}
                className="w-full"
              >
                Manage Query Rules
              </Button>
            </div>
          </div>

          {/* Info Section */}
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">💡 How this improves your queries</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Column metadata helps the AI understand your data better and generate more accurate queries</li>
              <li>• Query rules ensure data governance and security by automatically applying filters</li>
              <li>• Business definitions provide context that improves query interpretation</li>
              <li>• Semantic types enable smarter aggregations and visualizations</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
