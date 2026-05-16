import { useState, useRef, useEffect } from 'react'
import { Filter, X, Check } from 'lucide-react'
import { useFilters } from '@/contexts/FilterContext'
import { getUniqueValues, getColumnNames } from '@/lib/vegaFilters'

interface ChartFilterButtonProps {
  chartId: string
  chartData: any[]
  className?: string
}

export function ChartFilterButton({
  chartId,
  chartData,
  className = ''
}: ChartFilterButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [selectedColumn, setSelectedColumn] = useState<string | null>(null)
  const panelRef = useRef<HTMLDivElement>(null)

  const {
    chartFilters,
    setChartFilter,
    clearChartFilter,
    clearAllChartFilters,
    hasActiveChartFilters
  } = useFilters()

  const currentFilters = chartFilters[chartId] || {}
  const hasFilters = hasActiveChartFilters(chartId)

  // Get columns and their unique values from chart data
  const columns = getColumnNames(chartData)
  const columnValues = selectedColumn ? getUniqueValues(chartData, selectedColumn) : []

  // Close panel when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setSelectedColumn(null)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleToggleValue = (column: string, value: any) => {
    const filter = currentFilters[column]
    const currentValues = filter?.values || []

    if (currentValues.includes(value)) {
      const newValues = currentValues.filter(v => v !== value)
      if (newValues.length > 0) {
        setChartFilter(chartId, column, newValues, 'categorical')
      } else {
        clearChartFilter(chartId, column)
      }
    } else {
      setChartFilter(chartId, column, [...currentValues, value], 'categorical')
    }
  }

  // Filter out columns with too many unique values
  const filterableColumns = columns.filter(col => {
    const uniqueCount = getUniqueValues(chartData, col).length
    return uniqueCount > 1 && uniqueCount <= 20
  })

  if (filterableColumns.length === 0) {
    return null
  }

  return (
    <div className={`relative ${className}`} ref={panelRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`p-1.5 rounded transition-colors ${
          hasFilters
            ? 'bg-primary/10 text-primary'
            : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
        }`}
        title="Filter chart data"
      >
        <Filter className="h-4 w-4" />
        {hasFilters && (
          <span className="absolute -top-1 -right-1 w-4 h-4 bg-primary text-white text-xs rounded-full flex items-center justify-center">
            {Object.keys(currentFilters).length}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-1 w-72 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2 border-b border-gray-100">
            <span className="text-sm font-medium text-gray-700">Chart Filters</span>
            {hasFilters && (
              <button
                onClick={() => clearAllChartFilters(chartId)}
                className="text-xs text-red-600 hover:text-red-700"
              >
                Clear all
              </button>
            )}
          </div>

          {/* Column Selection */}
          {!selectedColumn ? (
            <div className="p-2">
              <p className="text-xs text-gray-500 mb-2">Select a column to filter:</p>
              <div className="space-y-1">
                {filterableColumns.map(col => {
                  const isFiltered = !!currentFilters[col]
                  const filterCount = currentFilters[col]?.values.length || 0

                  return (
                    <button
                      key={col}
                      onClick={() => setSelectedColumn(col)}
                      className={`w-full flex items-center justify-between px-3 py-2 text-sm rounded transition-colors ${
                        isFiltered
                          ? 'bg-primary/10 text-primary'
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <span className="truncate">{col}</span>
                      {isFiltered && (
                        <span className="text-xs bg-primary/20 px-1.5 py-0.5 rounded">
                          {filterCount} selected
                        </span>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>
          ) : (
            // Value Selection
            <div className="p-2">
              <div className="flex items-center justify-between mb-2">
                <button
                  onClick={() => setSelectedColumn(null)}
                  className="text-xs text-primary hover:text-primary/80"
                >
                  &larr; Back
                </button>
                <span className="text-xs text-gray-500 font-medium">{selectedColumn}</span>
              </div>

              <div className="max-h-48 overflow-y-auto space-y-1">
                {columnValues.map((value, idx) => {
                  const isSelected = currentFilters[selectedColumn]?.values.includes(value)

                  return (
                    <button
                      key={idx}
                      onClick={() => handleToggleValue(selectedColumn, value)}
                      className={`w-full flex items-center gap-2 px-3 py-2 text-sm rounded transition-colors ${
                        isSelected
                          ? 'bg-primary/10 text-primary'
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <div className={`w-4 h-4 border rounded flex items-center justify-center flex-shrink-0 ${
                        isSelected ? 'bg-primary border-primary' : 'border-gray-300'
                      }`}>
                        {isSelected && <Check className="h-3 w-3 text-white" />}
                      </div>
                      <span className="truncate">{String(value)}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
