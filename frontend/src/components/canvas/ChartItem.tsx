import { useState, useMemo } from 'react'
import { ChartContent } from '@/types/canvas'
import { VegaChart } from '@/components/visualization/VegaChart'
import { ChartFilterButton } from '@/components/filters/ChartFilterButton'
import { useFilters } from '@/contexts/FilterContext'
import { applyFiltersToSpec } from '@/lib/vegaFilters'
import { Edit2, Check } from 'lucide-react'
import { CardBadge } from '@/components/ui/card-badge'

interface ChartItemProps {
  content: ChartContent
  chartId?: string
  chartIndex?: number
  onTitleChange?: (newTitle: string) => void
}

export function ChartItem({ content, chartId, chartIndex, onTitleChange }: ChartItemProps) {
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
    <div className="h-full flex flex-col bg-card rounded-xl border border-border/50 overflow-hidden shadow-[0_2px_8px_-2px_rgba(0,0,0,0.05),0_4px_12px_-4px_rgba(0,0,0,0.05)]">
      {/* Header */}
      <div className="px-5 py-4 flex items-center justify-between group border-b border-border/30">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <CardBadge
            variant="chart"
            label={chartIndex !== undefined ? `Chart ${chartIndex + 1}` : undefined}
          />
          {isEditing ? (
            <div className="flex items-center gap-2 flex-1">
              <input
                type="text"
                value={editedTitle}
                onChange={(e) => setEditedTitle(e.target.value)}
                onKeyDown={handleKeyDown}
                onBlur={handleSaveTitle}
                className="flex-1 px-2 py-1 text-sm font-semibold text-foreground border border-indigo-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                autoFocus
              />
              <button
                onClick={handleSaveTitle}
                className="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded-lg"
              >
                <Check className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <h3 className="text-base font-semibold text-foreground truncate font-display">
              {editedTitle}
            </h3>
          )}
        </div>
        <div className="flex items-center gap-1.5 ml-2">
          {/* Chart filter button */}
          {chartId && chartData.length > 0 && (
            <ChartFilterButton
              chartId={chartId}
              chartData={chartData}
            />
          )}
          {onTitleChange && !isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="p-1.5 text-muted-foreground hover:text-indigo-600 hover:bg-indigo-50 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
              title="Edit title"
            >
              <Edit2 className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Chart - fill container for responsive Vega-Lite */}
      <div className="flex-1 p-5 min-h-0 bg-white">
        <div className="w-full h-full">
          <VegaChart spec={filteredSpec} onExport={() => {}} />
        </div>
      </div>
    </div>
  )
}
