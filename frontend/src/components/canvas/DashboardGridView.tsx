import { useMemo } from 'react'
import { CanvasItem, KPICardContent, ChartContent, InsightNoteContent, MapContent, QueryResultContent, DisplaySize } from '@/types/canvas'
import { DashboardFilterConfig } from '@/types/dashboard'
import { KPICard } from './KPICard'
import { ChartItem } from './ChartItem'
import { InsightNoteItem } from './InsightNoteItem'
import { QueryResultItem } from './QueryResultItem'
import { MapItem } from './MapItem'
import { CascadingGlobalFilterBar } from '@/components/filters/CascadingGlobalFilterBar'
import { CreateZone, DashboardContext, KPIContext, ChartContext, DashboardEdit } from '@/components/annotation'
import { useFilters } from '@/contexts/FilterContext'

/**
 * Get CSS class for grid column span based on display size
 */
function getColSpanClass(displaySize: DisplaySize | undefined, defaultSize: DisplaySize = 'medium'): string {
  const size = displaySize || defaultSize
  switch (size) {
    case 'small':
      return 'col-span-1'
    case 'medium':
      return 'col-span-1 lg:col-span-1'
    case 'large':
      return 'col-span-1 lg:col-span-2'
    case 'full':
      return 'col-span-1 lg:col-span-full'
    default:
      return 'col-span-1'
  }
}

/**
 * Get min height based on display size
 */
function getMinHeight(displaySize: DisplaySize | undefined, baseHeight: number = 350): string {
  const size = displaySize || 'medium'
  switch (size) {
    case 'small':
      return `${baseHeight * 0.8}px`
    case 'large':
    case 'full':
      return `${baseHeight * 1.2}px`
    default:
      return `${baseHeight}px`
  }
}

interface DashboardGridViewProps {
  items: CanvasItem[]
  datasetId?: string
  workspaceId?: string
  filterConfig?: DashboardFilterConfig[]
  onItemContentChange?: (id: string, content: any) => void
  onItemDelete?: (id: string) => void
  onConfigureFilters?: () => void
  onItemAdd?: (edit: DashboardEdit) => void
}

export function DashboardGridView({
  items,
  datasetId,
  workspaceId,
  filterConfig,
  onItemContentChange,
  onItemDelete,
  onConfigureFilters,
  onItemAdd
}: DashboardGridViewProps) {
  // Categorize items by type
  const categorizedItems = useMemo(() => {
    const kpis: CanvasItem[] = []
    const charts: CanvasItem[] = []
    const insights: CanvasItem[] = []
    const tables: CanvasItem[] = []
    const headers: CanvasItem[] = []
    const maps: CanvasItem[] = []

    items.forEach(item => {
      switch (item.type) {
        case 'kpi-card':
          kpis.push(item)
          break
        case 'chart':
          charts.push(item)
          break
        case 'insight-note':
          const content = item.content as InsightNoteContent
          if (content.tags?.includes('query-header')) {
            headers.push(item)
          } else {
            insights.push(item)
          }
          break
        case 'query-result':
          tables.push(item)
          break
        case 'map':
          maps.push(item)
          break
      }
    })

    return { kpis, charts, insights, tables, headers, maps }
  }, [items])

  const { kpis, charts, insights, tables, headers, maps } = categorizedItems

  // Crossfilter state
  const { crossfilterSelection, clearCrossfilterSelection } = useFilters()

  // Build dashboard context for CreateZone
  const dashboardContext = useMemo((): DashboardContext => {
    // Extract KPI context
    const kpiContexts: KPIContext[] = kpis.map(item => {
      const content = item.content as KPICardContent
      return {
        id: item.id,
        name: content.name,
        value: content.value,
        formattedValue: content.formattedValue || String(content.value),
        trend: content.trend,
        trendDirection: content.trendDirection
      }
    })

    // Extract chart context
    const chartContexts: ChartContext[] = charts.map(item => {
      const content = item.content as ChartContent
      return {
        id: item.id,
        chartType: content.chartType,
        title: content.title,
        data: content.data || []
      }
    })

    // Extract columns and full data from tables if available
    // Note: We pass more data to enable features like geospatial maps that need all rows
    let columns: string[] = []
    let sampleData: any[] = []

    if (tables.length > 0) {
      const tableContent = tables[0].content as QueryResultContent
      columns = tableContent.columns || []
      // Pass up to 100000 rows to support geospatial maps and aggregations
      sampleData = (tableContent.rows || []).slice(0, 100000)
    } else if (charts.length > 0) {
      // Try to get data from charts - charts often have aggregated data
      const chartWithData = charts.find(c => (c.content as ChartContent).data?.length)
      if (chartWithData) {
        const chartData = (chartWithData.content as ChartContent).data || []
        if (chartData.length > 0) {
          columns = Object.keys(chartData[0])
          // Pass up to 100000 rows for geospatial maps
          sampleData = chartData.slice(0, 100000)
        }
      }
    }

    return {
      datasetId,
      workspaceId,
      kpis: kpiContexts,
      charts: chartContexts,
      columns,
      sampleData
    }
  }, [kpis, charts, tables, datasetId, workspaceId])

  // If no items, show empty state
  if (items.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-muted-foreground">
        <div className="text-center">
          <div className="h-16 w-16 mx-auto mb-4 rounded-full bg-slate-100 flex items-center justify-center">
            <svg className="h-8 w-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <p className="text-lg font-medium text-slate-700">No dashboard items yet</p>
          <p className="text-sm mt-1 text-slate-500">Ask a question in the chat to generate a dashboard</p>
        </div>
      </div>
    )
  }

  // Check if we should show the filter bar
  const showFilterBar = datasetId && filterConfig && filterConfig.length > 0

  return (
    <div className="h-full flex flex-col bg-slate-50/50">
      {/* Cascading Global Filter Bar */}
      {showFilterBar && (
        <CascadingGlobalFilterBar
          datasetId={datasetId}
          filterConfig={filterConfig}
          onConfigureClick={onConfigureFilters}
        />
      )}

      {/* Crossfilter active banner */}
      {crossfilterSelection && (
        <div className="flex items-center justify-between px-4 py-2 bg-indigo-50 border-b border-indigo-100">
          <div className="flex items-center gap-2 text-sm text-indigo-700">
            <span className="inline-block w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
            <span>
              Crossfilter active: <strong>{crossfilterSelection.field}</strong> = <strong>{String(crossfilterSelection.value)}</strong>
              <span className="ml-1 text-indigo-500 text-xs">(double-click a chart to clear)</span>
            </span>
          </div>
          <button
            onClick={clearCrossfilterSelection}
            className="text-xs px-2.5 py-1 rounded-full bg-indigo-100 text-indigo-700 hover:bg-indigo-200 transition-colors font-medium"
          >
            Clear
          </button>
        </div>
      )}

      <div className="flex-1 overflow-auto">
        <div className="p-6 space-y-6 max-w-7xl mx-auto">
          {/* Headers */}
          {headers.length > 0 && (
            <div className="space-y-4">
              {headers.map(item => (
                <div key={item.id} className="max-w-3xl">
                  <InsightNoteItem content={item.content as InsightNoteContent} itemId={item.id} />
                </div>
              ))}
            </div>
          )}

          {/* KPI Cards Row */}
          {kpis.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {kpis.map(item => (
                <div key={item.id} className="min-h-[140px]">
                  <KPICard content={item.content as KPICardContent} itemId={item.id} />
                </div>
              ))}
            </div>
          )}

          {/* Charts Section - flexible grid with per-item sizing */}
          {charts.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {charts.map((item, index) => {
                const content = item.content as ChartContent
                const colSpanClass = getColSpanClass(content.displaySize, 'medium')
                const minHeight = getMinHeight(content.displaySize, 350)

                return (
                  <div
                    key={item.id}
                    className={`${colSpanClass}`}
                    style={{ minHeight }}
                  >
                    <ChartItem
                      content={content}
                      chartId={item.id}
                      chartIndex={index}
                      onTitleChange={onItemContentChange ? (newTitle) => {
                        const updatedContent = { ...content, title: newTitle }
                        onItemContentChange(item.id, updatedContent)
                      } : undefined}
                      onSizeChange={onItemContentChange ? (newSize: DisplaySize) => {
                        const updatedContent = { ...content, displaySize: newSize }
                        onItemContentChange(item.id, updatedContent)
                      } : undefined}
                      onDelete={onItemDelete ? () => onItemDelete(item.id) : undefined}
                    />
                  </div>
                )
              })}
            </div>
          )}

          {/* Insights Section */}
          {insights.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {insights.map(item => (
                <div key={item.id} className="min-h-[200px]">
                  <InsightNoteItem
                    content={item.content as InsightNoteContent}
                    variant="dashboard"
                    itemId={item.id}
                  />
                </div>
              ))}
            </div>
          )}

          {/* Maps Section - flexible grid with per-item sizing */}
          {maps.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {maps.map((item, index) => {
                const content = item.content as MapContent
                const colSpanClass = getColSpanClass(content.displaySize, 'large')
                const minHeight = getMinHeight(content.displaySize, 450)

                return (
                  <div
                    key={item.id}
                    className={`${colSpanClass}`}
                    style={{ minHeight }}
                  >
                    <MapItem
                      content={content}
                      mapId={item.id}
                      mapIndex={index}
                      onTitleChange={onItemContentChange ? (newTitle) => {
                        const updatedContent = { ...content, title: newTitle }
                        onItemContentChange(item.id, updatedContent)
                      } : undefined}
                      onSizeChange={onItemContentChange ? (newSize: DisplaySize) => {
                        const updatedContent = { ...content, displaySize: newSize }
                        onItemContentChange(item.id, updatedContent)
                      } : undefined}
                      onDelete={onItemDelete ? () => onItemDelete(item.id) : undefined}
                    />
                  </div>
                )
              })}
            </div>
          )}

          {/* Tables Section */}
          {tables.length > 0 && (
            <div className="space-y-6">
              {tables.map(item => (
                <div key={item.id} className="bg-card rounded-xl border border-border/50 overflow-hidden shadow-sm">
                  <QueryResultItem
                    content={item.content as any}
                    itemId={item.id}
                    onTitleChange={onItemContentChange ? (newTitle) => {
                      const updatedContent = { ...item.content as any, title: newTitle }
                      onItemContentChange(item.id, updatedContent)
                    } : undefined}
                  />
                </div>
              ))}
            </div>
          )}

          {/* Create Zone - Add new elements with dashboard context */}
          {onItemAdd && (
            <CreateZone
              context={dashboardContext}
              onElementCreated={onItemAdd}
            />
          )}
        </div>
      </div>
    </div>
  )
}
