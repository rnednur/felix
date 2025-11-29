import { useState } from 'react'
import { Table2, ChevronDown } from 'lucide-react'

interface TablePreview {
  dataset_id: string
  dataset_name: string
  alias: string
  row_count: number
  preview_rows: number
  columns: string[]
  data: any[]
}

interface GroupDataPreviewProps {
  previews: TablePreview[]
}

export function GroupDataPreview({ previews }: GroupDataPreviewProps) {
  const [selectedTable, setSelectedTable] = useState<string>(previews[0]?.dataset_id || '')

  const currentPreview = previews.find(p => p.dataset_id === selectedTable)

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Table Selector */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center gap-3">
          <Table2 className="w-5 h-5 text-gray-600" />
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Select Table
            </label>
            <div className="relative">
              <select
                value={selectedTable}
                onChange={(e) => setSelectedTable(e.target.value)}
                className="w-full px-4 py-2 pr-10 border border-gray-300 rounded-lg appearance-none focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
              >
                {previews.map((preview) => (
                  <option key={preview.dataset_id} value={preview.dataset_id}>
                    {preview.alias} ({preview.row_count.toLocaleString()} rows)
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none" />
            </div>
          </div>
        </div>

        {currentPreview && (
          <div className="mt-3 text-sm text-gray-600">
            Showing {currentPreview.preview_rows} of {currentPreview.row_count.toLocaleString()} rows • {currentPreview.columns.length} columns
          </div>
        )}
      </div>

      {/* Data Table */}
      <div className="flex-1 overflow-auto p-4">
        {currentPreview ? (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full">
              <thead className="bg-gray-50 border-b border-gray-200 sticky top-0 z-10">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600 border-r border-gray-200">
                    #
                  </th>
                  {currentPreview.columns.map((col) => (
                    <th
                      key={col}
                      className="px-4 py-3 text-left text-xs font-medium text-gray-600 border-r border-gray-200 last:border-r-0 whitespace-nowrap"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {currentPreview.data.map((row, i) => (
                  <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="px-4 py-3 text-xs text-gray-500 border-r border-gray-200 font-mono">
                      {i + 1}
                    </td>
                    {currentPreview.columns.map((col) => (
                      <td
                        key={col}
                        className="px-4 py-3 text-sm text-gray-900 border-r border-gray-200 last:border-r-0"
                      >
                        {row[col] !== null && row[col] !== undefined
                          ? String(row[col])
                          : <span className="text-gray-400 italic">null</span>
                        }
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            No preview data available
          </div>
        )}
      </div>
    </div>
  )
}
