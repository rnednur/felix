import { useState, useEffect } from 'react'
import { X, Save, Info } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ColumnMetadata {
  id?: string
  column_name: string
  display_name?: string
  description?: string
  business_definition?: string
  semantic_type?: string
  data_format?: string
  unit?: string
  is_pii?: boolean
  is_required?: boolean
  default_aggregation?: string
  is_dimension?: boolean
  is_measure?: boolean
}

interface Props {
  datasetId: string
  columnName: string
  existingMetadata?: ColumnMetadata
  onClose: () => void
  onSave: () => void
}

const SEMANTIC_TYPES = [
  'text', 'email', 'phone', 'url', 'currency', 'percentage',
  'date', 'datetime', 'time', 'number', 'integer', 'boolean'
]

const AGGREGATIONS = ['SUM', 'AVG', 'COUNT', 'MIN', 'MAX', 'COUNT_DISTINCT']

export function ColumnMetadataEditor({ datasetId, columnName, existingMetadata, onClose, onSave }: Props) {
  const [metadata, setMetadata] = useState<ColumnMetadata>({
    column_name: columnName,
    ...existingMetadata
  })
  const [isSaving, setIsSaving] = useState(false)

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/metadata/datasets/${datasetId}/columns/${columnName}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(metadata)
        }
      )

      if (!response.ok) throw new Error('Failed to save metadata')

      onSave()
      onClose()
    } catch (error) {
      console.error('Error saving metadata:', error)
      alert('Failed to save metadata')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Edit Column Metadata</h2>
            <p className="text-sm text-gray-600 mt-1">
              Configure metadata for column: <span className="font-mono font-medium">{columnName}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <div className="p-6 space-y-6">
          {/* Display Information */}
          <div className="space-y-4">
            <h3 className="font-medium text-gray-900 flex items-center gap-2">
              <Info className="w-4 h-4" />
              Display Information
            </h3>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Display Name
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Friendly name for display"
                value={metadata.display_name || ''}
                onChange={(e) => setMetadata({ ...metadata, display_name: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="What this column represents"
                rows={2}
                value={metadata.description || ''}
                onChange={(e) => setMetadata({ ...metadata, description: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Business Definition
              </label>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Business context and how to use this field"
                rows={3}
                value={metadata.business_definition || ''}
                onChange={(e) => setMetadata({ ...metadata, business_definition: e.target.value })}
              />
            </div>
          </div>

          {/* Data Semantics */}
          <div className="space-y-4 pt-4 border-t">
            <h3 className="font-medium text-gray-900">Data Semantics</h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Semantic Type
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  value={metadata.semantic_type || ''}
                  onChange={(e) => setMetadata({ ...metadata, semantic_type: e.target.value })}
                >
                  <option value="">Select type...</option>
                  {SEMANTIC_TYPES.map((type) => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Unit
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., USD, meters, seconds"
                  value={metadata.unit || ''}
                  onChange={(e) => setMetadata({ ...metadata, unit: e.target.value })}
                />
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Data Format
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., MM/DD/YYYY, $#,##0.00"
                  value={metadata.data_format || ''}
                  onChange={(e) => setMetadata({ ...metadata, data_format: e.target.value })}
                />
              </div>
            </div>
          </div>

          {/* Query Hints */}
          <div className="space-y-4 pt-4 border-t">
            <h3 className="font-medium text-gray-900">Query Hints</h3>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Default Aggregation
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={metadata.default_aggregation || ''}
                onChange={(e) => setMetadata({ ...metadata, default_aggregation: e.target.value })}
              >
                <option value="">None</option>
                {AGGREGATIONS.map((agg) => (
                  <option key={agg} value={agg}>{agg}</option>
                ))}
              </select>
            </div>

            <div className="flex gap-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  checked={metadata.is_dimension || false}
                  onChange={(e) => setMetadata({ ...metadata, is_dimension: e.target.checked })}
                />
                <span className="text-sm text-gray-700">Is Dimension (for GROUP BY)</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  checked={metadata.is_measure || false}
                  onChange={(e) => setMetadata({ ...metadata, is_measure: e.target.checked })}
                />
                <span className="text-sm text-gray-700">Is Measure (for aggregation)</span>
              </label>
            </div>
          </div>

          {/* Constraints */}
          <div className="space-y-4 pt-4 border-t">
            <h3 className="font-medium text-gray-900">Constraints</h3>

            <div className="flex gap-6">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  checked={metadata.is_pii || false}
                  onChange={(e) => setMetadata({ ...metadata, is_pii: e.target.checked })}
                />
                <span className="text-sm text-gray-700">Contains PII</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  checked={metadata.is_required || false}
                  onChange={(e) => setMetadata({ ...metadata, is_required: e.target.checked })}
                />
                <span className="text-sm text-gray-700">Required (not null)</span>
              </label>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 border-t px-6 py-4 flex justify-end gap-3">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isSaving}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            {isSaving ? 'Saving...' : 'Save Metadata'}
          </Button>
        </div>
      </div>
    </div>
  )
}
