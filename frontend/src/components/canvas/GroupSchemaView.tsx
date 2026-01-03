import { useState } from 'react'
import { ChevronDown, ChevronRight, Search, Table2, Hash, Type, Calendar, ToggleLeft } from 'lucide-react'

interface Column {
  name: string
  dtype: string
  stats?: {
    top_values?: any[]
    min?: any
    max?: any
    null_count?: number
  }
}

interface TableSchema {
  dataset_id: string
  dataset_name: string
  alias: string
  row_count: number
  schema: {
    columns: Column[]
  }
}

interface GroupSchemaViewProps {
  schemas: TableSchema[]
}

export function GroupSchemaView({ schemas }: GroupSchemaViewProps) {
  const [expandedTables, setExpandedTables] = useState<Set<string>>(new Set(schemas.map(s => s.dataset_id)))
  const [searchTerm, setSearchTerm] = useState('')

  const toggleTable = (datasetId: string) => {
    setExpandedTables(prev => {
      const next = new Set(prev)
      if (next.has(datasetId)) {
        next.delete(datasetId)
      } else {
        next.add(datasetId)
      }
      return next
    })
  }

  const getTypeIcon = (dtype: string) => {
    if (dtype.includes('int') || dtype.includes('float')) return <Hash className="w-4 h-4 text-blue-600" />
    if (dtype.includes('str') || dtype.includes('object')) return <Type className="w-4 h-4 text-green-600" />
    if (dtype.includes('date') || dtype.includes('time')) return <Calendar className="w-4 h-4 text-purple-600" />
    if (dtype.includes('bool')) return <ToggleLeft className="w-4 h-4 text-orange-600" />
    return <Type className="w-4 h-4 text-gray-600" />
  }

  const formatValue = (value: any) => {
    if (value === null || value === undefined) return 'null'
    if (typeof value === 'number') return value.toLocaleString()
    return String(value)
  }

  const filteredSchemas = schemas.map(table => ({
    ...table,
    filteredColumns: searchTerm
      ? table.schema.columns.filter(col =>
          col.name.toLowerCase().includes(searchTerm.toLowerCase())
        )
      : table.schema.columns
  })).filter(table => table.filteredColumns.length > 0)

  const totalColumns = schemas.reduce((sum, s) => sum + s.schema.columns.length, 0)

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Schema Overview</h2>
            <p className="text-sm text-gray-600">
              {schemas.length} table{schemas.length !== 1 ? 's' : ''} • {totalColumns} total columns
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search columns..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Tables List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {filteredSchemas.map((table) => (
          <div key={table.dataset_id} className="bg-white rounded-lg border border-gray-200 shadow-sm">
            {/* Table Header */}
            <div
              className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
              onClick={() => toggleTable(table.dataset_id)}
            >
              <div className="flex items-center gap-3">
                {expandedTables.has(table.dataset_id) ? (
                  <ChevronDown className="w-5 h-5 text-gray-600" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-gray-600" />
                )}
                <Table2 className="w-5 h-5 text-blue-600" />
                <div>
                  <div className="font-semibold text-gray-900">{table.alias}</div>
                  <div className="text-xs text-gray-500">
                    {table.dataset_name} • {table.row_count.toLocaleString()} rows • {table.schema.columns.length} columns
                  </div>
                </div>
              </div>
              <div className="text-xs text-gray-500 font-mono bg-gray-100 px-2 py-1 rounded">
                {table.alias}
              </div>
            </div>

            {/* Columns List */}
            {expandedTables.has(table.dataset_id) && (
              <div className="border-t border-gray-200">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-600">Column</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-600">Type</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-600">Sample Values</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-600">Stats</th>
                    </tr>
                  </thead>
                  <tbody>
                    {table.filteredColumns.map((column, idx) => (
                      <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            {getTypeIcon(column.dtype)}
                            <span className="font-mono text-sm text-gray-900">{column.name}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded text-gray-600">
                            {column.dtype}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex gap-1 flex-wrap">
                            {column.stats?.top_values?.slice(0, 3).map((val, i) => (
                              <span key={i} className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">
                                {formatValue(val[0])}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-600">
                          {column.stats?.min !== undefined && column.stats?.max !== undefined && (
                            <div>Range: {formatValue(column.stats.min)} - {formatValue(column.stats.max)}</div>
                          )}
                          {column.stats?.null_count !== undefined && column.stats.null_count > 0 && (
                            <div className="text-orange-600">{column.stats.null_count} nulls</div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ))}

        {filteredSchemas.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            No columns found matching "{searchTerm}"
          </div>
        )}
      </div>
    </div>
  )
}
