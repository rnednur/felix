import { useState, useMemo } from 'react'
import { ChartContent, DisplaySize } from '@/types/canvas'
import { VegaChart } from '@/components/visualization/VegaChart'
import { ChartFilterButton } from '@/components/filters/ChartFilterButton'
import { useFilters } from '@/contexts/FilterContext'
import { useTheme } from '@/contexts/ThemeContext'
import { applyFiltersToSpec } from '@/lib/vegaFilters'
import { Edit2, Check, Minimize2, Square, Maximize2, RectangleHorizontal, Trash2 } from 'lucide-react'
import { CardBadge } from '@/components/ui/card-badge'

interface ChartItemProps {
  content: ChartContent
  chartId?: string
  chartIndex?: number
  onTitleChange?: (newTitle: string) => void
  onSizeChange?: (newSize: DisplaySize) => void
  onDelete?: () => void
}

const SIZE_OPTIONS: { size: DisplaySize; icon: typeof Square; label: string; tooltip: string }[] = [
  { size: 'small', icon: Minimize2, label: 'S', tooltip: 'Small (1 column)' },
  { size: 'medium', icon: Square, label: 'M', tooltip: 'Medium (1 column)' },
  { size: 'large', icon: Maximize2, label: 'L', tooltip: 'Large (2 columns)' },
  { size: 'full', icon: RectangleHorizontal, label: 'Full', tooltip: 'Full width' },
]

export function ChartItem({ content, chartId, chartIndex, onTitleChange, onSizeChange, onDelete }: ChartItemProps) {
  const { vegaSpec, title, chartType, data, displaySize } = content
  const currentSize = displaySize || 'medium'

  // Serialize config for annotation system - include vegaSpec for LLM to modify
  const felixConfig = chartId ? JSON.stringify({
    chartType,
    title: title || `${chartType} Chart`,
    hasData: !!data?.length,
    vegaSpec: vegaSpec  // Include full spec for LLM modifications
  }) : undefined
  const { persona } = useTheme()
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

  // Chart area background - always light for chart readability
  const chartBgColor = persona.isDark ? '#1f2937' : '#ffffff'

  return (
    <div
      className="h-full flex flex-col rounded-xl overflow-hidden"
      data-felix-id={chartId}
      data-felix-type="chart"
      data-felix-config={felixConfig}
      style={{
        backgroundColor: persona.cardBackground,
        borderWidth: '1px',
        borderStyle: 'solid',
        borderColor: persona.cardBorder,
        boxShadow: persona.isDark
          ? '0 2px 8px -2px rgba(0,0,0,0.3), 0 4px 12px -4px rgba(0,0,0,0.2)'
          : '0 2px 8px -2px rgba(0,0,0,0.05), 0 4px 12px -4px rgba(0,0,0,0.05)'
      }}
    >
      {/* Header */}
      <div
        className="px-5 py-4 flex items-center justify-between group"
        style={{
          borderBottomWidth: '1px',
          borderBottomStyle: 'solid',
          borderBottomColor: persona.isDark ? `${persona.cardBorder}50` : `${persona.cardBorder}80`
        }}
      >
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <CardBadge
            variant="chart"
            label={chartIndex !== undefined ? `Chart ${chartIndex + 1}` : undefined}
            themeStyle={persona.badgeStyle}
          />
          {isEditing ? (
            <div className="flex items-center gap-2 flex-1">
              <input
                type="text"
                value={editedTitle}
                onChange={(e) => setEditedTitle(e.target.value)}
                onKeyDown={handleKeyDown}
                onBlur={handleSaveTitle}
                className="flex-1 px-2 py-1 text-sm font-semibold rounded-lg focus:outline-none focus:ring-2"
                style={{
                  color: persona.textPrimary,
                  backgroundColor: persona.isDark ? '#374151' : '#ffffff',
                  borderWidth: '1px',
                  borderStyle: 'solid',
                  borderColor: persona.primary,
                }}
                autoFocus
              />
              <button
                onClick={handleSaveTitle}
                className="p-1.5 rounded-lg"
                style={{
                  color: persona.isDark ? '#34d399' : '#059669',
                  backgroundColor: persona.isDark ? 'rgba(16, 185, 129, 0.15)' : '#ecfdf5'
                }}
              >
                <Check className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <h3
              className="text-base font-semibold truncate font-display"
              style={{ color: persona.textPrimary }}
            >
              {editedTitle}
            </h3>
          )}
        </div>
        <div className="flex items-center gap-1.5 ml-2">
          {/* Size controls */}
          {onSizeChange && (
            <div
              className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-all rounded-lg p-0.5"
              style={{
                backgroundColor: persona.isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)'
              }}
            >
              {SIZE_OPTIONS.map(({ size, icon: Icon, tooltip }) => (
                <button
                  key={size}
                  onClick={() => onSizeChange(size)}
                  className="p-1 rounded transition-all"
                  style={{
                    color: currentSize === size ? persona.primary : persona.textMuted,
                    backgroundColor: currentSize === size
                      ? (persona.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)')
                      : 'transparent'
                  }}
                  title={tooltip}
                >
                  <Icon className="h-3.5 w-3.5" />
                </button>
              ))}
            </div>
          )}
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
              className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
              style={{
                color: persona.textMuted,
              }}
              title="Edit title"
            >
              <Edit2 className="h-3.5 w-3.5" />
            </button>
          )}
          {onDelete && (
            <button
              onClick={onDelete}
              className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-all hover:bg-red-50 dark:hover:bg-red-900/20"
              style={{
                color: persona.textMuted,
              }}
              title="Delete chart"
            >
              <Trash2 className="h-3.5 w-3.5 hover:text-red-500" />
            </button>
          )}
        </div>
      </div>

      {/* Chart - fill container for responsive Vega-Lite */}
      <div
        className="flex-1 p-5 min-h-0"
        style={{ backgroundColor: chartBgColor }}
      >
        <div className="w-full h-full">
          <VegaChart spec={filteredSpec} />
        </div>
      </div>
    </div>
  )
}
