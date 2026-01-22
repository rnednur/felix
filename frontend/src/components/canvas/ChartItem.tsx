import { useState, useMemo } from 'react'
import { ChartContent } from '@/types/canvas'
import { VegaChart } from '@/components/visualization/VegaChart'
import { ChartFilterButton } from '@/components/filters/ChartFilterButton'
import { useFilters } from '@/contexts/FilterContext'
import { applyFiltersToSpec } from '@/lib/vegaFilters'
import { Edit2, Check } from 'lucide-react'

interface ChartItemProps {
  content: ChartContent
  chartId?: string
  onTitleChange?: (newTitle: string) => void
}

export function ChartItem({ content, chartId, onTitleChange }: ChartItemProps) {
  const { vegaSpec, title, chartType, data } = content
  const [isEditing, setIsEditing] = useState(false)
  const [editedTitle, setEditedTitle] = useState(title || `${chartType} Chart`)

  // Get filters from context
  const { getFiltersForChart } = useFilters()
  const filters = chartId ? getFiltersForChart(chartId) : {}

  // Apply filters to the Vega spec
  const filteredSpec = useMemo(() => {
    if (!vegaSpec || Object.keys(filters).length === 0) {
      return vegaSpec
    }
    return applyFiltersToSpec(vegaSpec, filters)
  }, [vegaSpec, filters])

  // Chart data for filter options
  const chartData = data || vegaSpec?.data?.values || []

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
      setEditedTitle(title || `${chartType} Chart`)
      setIsEditing(false)
    }
  }

  return (
    <div className="h-full flex flex-col bg-white overflow-hidden">
      {/* Header */}
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center justify-between group">
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
            <h3 className="text-sm font-semibold text-gray-700 capitalize flex-1">
              {editedTitle}
            </h3>
            <div className="flex items-center gap-1">
              {/* Chart filter button */}
              {chartId && chartData.length > 0 && (
                <ChartFilterButton
                  chartId={chartId}
                  chartData={chartData}
                />
              )}
              {onTitleChange && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Edit title"
                >
                  <Edit2 className="h-3 w-3" />
                </button>
              )}
            </div>
          </>
        )}
      </div>

      {/* Chart - fill container for responsive Vega-Lite */}
      <div className="flex-1 p-4 min-h-0">
        <div className="w-full h-full">
          <VegaChart spec={filteredSpec} onExport={() => {}} />
        </div>
      </div>
    </div>
  )
}
