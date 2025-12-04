import { useState } from 'react'
import { QueryResultContent } from '@/types/canvas'
import { Edit2, Check } from 'lucide-react'

interface QueryResultItemProps {
  content: QueryResultContent
  onTitleChange?: (newTitle: string) => void
}

export function QueryResultItem({ content, onTitleChange }: QueryResultItemProps) {
  const { columns, rows, totalRows } = content
  const [isEditing, setIsEditing] = useState(false)
  const [editedTitle, setEditedTitle] = useState('Query Results')

  const handleSaveTitle = () => {
    if (onTitleChange && editedTitle.trim()) {
      onTitleChange(editedTitle.trim())
    }
    setIsEditing(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSaveTitle()
    } else if (e.key === 'Escape') {
      setEditedTitle('Query Results')
      setIsEditing(false)
    }
  }

  return (
    <div className="h-full flex flex-col bg-white overflow-hidden">
      {/* Header */}
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between group">
          {isEditing ? (
            <div className="flex items-center gap-2 flex-1">
              <input
                type="text"
                value={editedTitle}
                onChange={(e) => setEditedTitle(e.target.value)}
                onKeyDown={handleKeyDown}
                onBlur={handleSaveTitle}
                className="flex-1 px-2 py-1 text-sm font-semibold text-gray-700 border border-blue-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus
              />
              <button
                onClick={handleSaveTitle}
                className="p-1 text-green-600 hover:bg-green-50 rounded"
              >
                <Check className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <>
              <h3 className="text-sm font-semibold text-gray-700">{editedTitle}</h3>
              {onTitleChange && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Edit title"
                >
                  <Edit2 className="h-3 w-3" />
                </button>
              )}
            </>
          )}
        </div>
        {totalRows && (
          <p className="text-xs text-gray-500 mt-1">
            {totalRows.toLocaleString()} rows
          </p>
        )}
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {rows.slice(0, 50).map((row, i) => (
              <tr key={i} className="hover:bg-gray-50">
                {columns.map((col) => (
                  <td key={col} className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                    {row[col]?.toString() || ''}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      {rows.length > 50 && (
        <div className="bg-gray-50 px-4 py-2 border-t border-gray-200 text-xs text-gray-500">
          Showing first 50 rows
        </div>
      )}
    </div>
  )
}
