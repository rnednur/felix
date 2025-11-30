import { useState } from 'react'
import { Sparkles, Check, X, Edit2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ColumnMetadataSuggestion } from '@/services/api'

interface Props {
  suggestions: ColumnMetadataSuggestion[]
  onAccept: (columnName: string, metadata: Partial<ColumnMetadataSuggestion>) => void
  onAcceptAll: (updates: Record<string, Partial<ColumnMetadataSuggestion>>) => void
  onCancel: () => void
}

export function AIMetadataSuggestions({ suggestions, onAccept, onAcceptAll, onCancel }: Props) {
  const [editingColumn, setEditingColumn] = useState<string | null>(null)
  const [editedSuggestions, setEditedSuggestions] = useState<Record<string, ColumnMetadataSuggestion>>(
    suggestions.reduce((acc, s) => ({ ...acc, [s.column]: s }), {})
  )
  const [acceptedColumns, setAcceptedColumns] = useState<Set<string>>(new Set())

  const handleEdit = (columnName: string, field: keyof ColumnMetadataSuggestion, value: string) => {
    setEditedSuggestions(prev => ({
      ...prev,
      [columnName]: {
        ...prev[columnName],
        [field]: value
      }
    }))
  }

  const handleAcceptColumn = (columnName: string) => {
    const suggestion = editedSuggestions[columnName]
    onAccept(columnName, {
      description: suggestion.description,
      business_definition: suggestion.business_definition,
      semantic_type: suggestion.semantic_type
    })
    setAcceptedColumns(prev => new Set([...prev, columnName]))
  }

  const handleAcceptAll = () => {
    const updates: Record<string, Partial<ColumnMetadataSuggestion>> = {}
    Object.entries(editedSuggestions).forEach(([column, suggestion]) => {
      updates[column] = {
        description: suggestion.description,
        business_definition: suggestion.business_definition,
        semantic_type: suggestion.semantic_type
      }
    })
    onAcceptAll(updates)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">AI-Generated Column Descriptions</h2>
                <p className="text-sm text-gray-600 mt-1">
                  Review and edit the AI's suggestions before applying
                </p>
              </div>
            </div>
            <button
              onClick={onCancel}
              className="text-gray-400 hover:text-gray-600 transition-colors text-2xl font-light leading-none"
            >
              ×
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4">
            {suggestions.map((suggestion) => {
              const isEditing = editingColumn === suggestion.column
              const isAccepted = acceptedColumns.has(suggestion.column)
              const current = editedSuggestions[suggestion.column]

              return (
                <div
                  key={suggestion.column}
                  className={`border rounded-lg p-4 transition-all ${
                    isAccepted
                      ? 'bg-green-50 border-green-300'
                      : 'bg-white hover:border-blue-300'
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-base font-semibold text-gray-900">
                        {suggestion.column}
                      </span>
                      {isAccepted && (
                        <span className="flex items-center gap-1 text-xs bg-green-600 text-white px-2 py-1 rounded">
                          <Check className="h-3 w-3" />
                          Applied
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {!isAccepted && (
                        <>
                          <button
                            onClick={() => setEditingColumn(isEditing ? null : suggestion.column)}
                            className="text-blue-600 hover:text-blue-700 text-sm flex items-center gap-1"
                          >
                            <Edit2 className="h-3 w-3" />
                            {isEditing ? 'Done' : 'Edit'}
                          </button>
                          <button
                            onClick={() => handleAcceptColumn(suggestion.column)}
                            className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm flex items-center gap-1"
                          >
                            <Check className="h-3 w-3" />
                            Accept
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Description */}
                  <div className="mb-3">
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Description
                    </label>
                    {isEditing ? (
                      <textarea
                        value={current.description}
                        onChange={(e) => handleEdit(suggestion.column, 'description', e.target.value)}
                        className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        rows={2}
                      />
                    ) : (
                      <p className="text-sm text-gray-800">{current.description}</p>
                    )}
                  </div>

                  {/* Business Definition */}
                  {current.business_definition && (
                    <div className="mb-3">
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Business Definition
                      </label>
                      {isEditing ? (
                        <textarea
                          value={current.business_definition}
                          onChange={(e) => handleEdit(suggestion.column, 'business_definition', e.target.value)}
                          className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          rows={2}
                        />
                      ) : (
                        <p className="text-sm text-gray-700">{current.business_definition}</p>
                      )}
                    </div>
                  )}

                  {/* Semantic Type */}
                  {current.semantic_type && (
                    <div className="mb-3">
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Semantic Type
                      </label>
                      {isEditing ? (
                        <input
                          type="text"
                          value={current.semantic_type}
                          onChange={(e) => handleEdit(suggestion.column, 'semantic_type', e.target.value)}
                          className="w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      ) : (
                        <span className="inline-block px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                          {current.semantic_type}
                        </span>
                      )}
                    </div>
                  )}

                  {/* Examples */}
                  {current.examples && current.examples.length > 0 && (
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Example Values
                      </label>
                      <div className="flex flex-wrap gap-1">
                        {current.examples.map((ex, idx) => (
                          <span
                            key={idx}
                            className="inline-block px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded font-mono"
                          >
                            {ex}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t px-6 py-4 bg-gray-50">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">
              {acceptedColumns.size} of {suggestions.length} columns accepted
            </p>
            <div className="flex gap-3">
              <Button variant="outline" onClick={onCancel}>
                Cancel
              </Button>
              <Button
                onClick={handleAcceptAll}
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
              >
                <Check className="h-4 w-4 mr-2" />
                Accept All
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
