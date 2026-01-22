import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Filter, X, RefreshCw } from 'lucide-react'
import axios from '@/services/api'
import { FilterDropdown } from './FilterDropdown'
import { useFilters } from '@/contexts/FilterContext'

interface FilterableColumn {
  name: string
  type: 'categorical' | 'numeric' | 'date'
  dtype: string
  unique_count: number
  null_count: number
}

interface FilterOption {
  value: string | number | boolean
  label: string
  count?: number
}

interface GlobalFilterBarProps {
  datasetId: string
  className?: string
}

export function GlobalFilterBar({ datasetId, className = '' }: GlobalFilterBarProps) {
  const {
    globalFilters,
    setGlobalFilter,
    clearGlobalFilter,
    clearAllGlobalFilters,
    hasActiveGlobalFilters
  } = useFilters()

  const [columnOptions, setColumnOptions] = useState<{ [column: string]: FilterOption[] }>({})
  const [loadingColumn, setLoadingColumn] = useState<string | null>(null)

  // Fetch filterable columns
  const { data: columnsData, isLoading: columnsLoading } = useQuery({
    queryKey: ['filterable-columns', datasetId],
    queryFn: async () => {
      const response = await axios.get(`/filters/datasets/${datasetId}/columns`)
      return response.data
    },
    enabled: !!datasetId,
    staleTime: 5 * 60 * 1000 // 5 minutes
  })

  // Fetch distinct values for a column
  const fetchColumnValues = async (column: string) => {
    if (columnOptions[column]) return

    setLoadingColumn(column)
    try {
      const response = await axios.get(
        `/filters/datasets/${datasetId}/columns/${column}/values`
      )

      const options: FilterOption[] = response.data.values.map((v: any) => ({
        value: v.value,
        label: String(v.value),
        count: v.count
      }))

      setColumnOptions(prev => ({ ...prev, [column]: options }))
    } catch (error) {
      console.error('Failed to fetch column values:', error)
    } finally {
      setLoadingColumn(null)
    }
  }

  const filterableColumns: FilterableColumn[] = columnsData?.columns || []

  // Only show categorical columns with reasonable cardinality
  const displayColumns = filterableColumns.filter(
    col => col.type === 'categorical' && col.unique_count <= 50
  )

  if (columnsLoading) {
    return (
      <div className={`flex items-center gap-2 px-4 py-2 bg-gray-50 border-b border-gray-200 ${className}`}>
        <Filter className="h-4 w-4 text-gray-400" />
        <span className="text-sm text-gray-500">Loading filters...</span>
      </div>
    )
  }

  if (displayColumns.length === 0) {
    return null
  }

  return (
    <div className={`flex items-center gap-3 px-4 py-2 bg-gray-50 border-b border-gray-200 ${className}`}>
      <div className="flex items-center gap-2 text-gray-600">
        <Filter className="h-4 w-4" />
        <span className="text-sm font-medium">Filters:</span>
      </div>

      {/* Filter dropdowns */}
      <div className="flex items-center gap-2 flex-wrap">
        {displayColumns.slice(0, 5).map((col) => {
          const options = columnOptions[col.name] || []
          const selectedValues = globalFilters[col.name]?.values || []

          return (
            <div key={col.name} onMouseEnter={() => fetchColumnValues(col.name)}>
              <FilterDropdown
                column={col.name}
                label={col.name}
                options={options}
                selectedValues={selectedValues}
                onSelectionChange={(values) => {
                  if (values.length > 0) {
                    setGlobalFilter(col.name, values, 'categorical')
                  } else {
                    clearGlobalFilter(col.name)
                  }
                }}
                onClear={() => clearGlobalFilter(col.name)}
                placeholder={loadingColumn === col.name ? 'Loading...' : 'All'}
              />
            </div>
          )
        })}
      </div>

      {/* Clear all button */}
      {hasActiveGlobalFilters && (
        <button
          onClick={clearAllGlobalFilters}
          className="flex items-center gap-1 px-2 py-1 text-sm text-red-600 hover:bg-red-50 rounded transition-colors"
        >
          <X className="h-3 w-3" />
          Clear all
        </button>
      )}

      {/* Active filter count */}
      {hasActiveGlobalFilters && (
        <span className="text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded">
          {Object.keys(globalFilters).length} active
        </span>
      )}
    </div>
  )
}
