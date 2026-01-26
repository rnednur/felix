import { useMemo } from 'react'
import { CanvasItem, KPICardContent, ChartContent, InsightNoteContent, MapContent, QueryResultContent } from '@/types/canvas'
import { DashboardFilterConfig } from '@/types/dashboard'
import { KPICard } from './KPICard'
import { ChartItem } from './ChartItem'
import { InsightNoteItem } from './InsightNoteItem'
import { QueryResultItem } from './QueryResultItem'
import { MapItem } from './MapItem'
import { CascadingGlobalFilterBar } from '@/components/filters/CascadingGlobalFilterBar'
import { CreateZone, DashboardContext, KPIContext, ChartContext, DashboardEdit } from '@/components/annotation'

interface DashboardGridViewProps {
  items: CanvasItem[]
  datasetId?: string
  workspaceId?: string
  filterConfig?: DashboardFilterConfig[]
  onItemContentChange?: (id: string, content: any) => void
  onConfigureFilters?: () => void
  onItemAdd?: (edit: DashboardEdit) => void
}

export function DashboardGridView({
  items,
  datasetId,
  workspaceId,
  filterConfig,
  onItemContentChange,
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
      // Pass up to 200 rows to support maps and aggregations
      sampleData = (tableContent.rows || []).slice(0, 200)
    } else if (charts.length > 0) {
      // Try to get data from charts - charts often have aggregated data
      const chartWithData = charts.find(c => (c.content as ChartContent).data?.length)
      if (chartWithData) {
        const chartData = (chartWithData.content as ChartContent).data || []
        if (chartData.length > 0) {
          columns = Object.keys(chartData[0])
          // Pass all chart data (typically already aggregated)
          sampleData = chartData.slice(0, 200)
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

          {/* Charts and Insights Grid */}
          {(charts.length > 0 || insights.length > 0) && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Charts - takes 2 columns on large screens */}
              <div className={`${insights.length > 0 ? 'lg:col-span-2' : 'lg:col-span-3'} space-y-6`}>
                <div className={`grid gap-6 ${charts.length === 1 ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2'}`}>
                  {charts.map((item, index) => (
                    <div key={item.id} className="min-h-[350px]">
                      <ChartItem
                        content={item.content as ChartContent}
                        chartId={item.id}
                        chartIndex={index}
                        onTitleChange={onItemContentChange ? (newTitle) => {
                          const updatedContent = { ...item.content as ChartContent, title: newTitle }
                          onItemContentChange(item.id, updatedContent)
                        } : undefined}
                      />
                    </div>
                  ))}
                </div>
              </div>

              {/* Insights Panel - takes 1 column on large screens */}
              {insights.length > 0 && (
                <div className="lg:col-span-1 space-y-4">
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
            </div>
          )}

          {/* Maps Section */}
          {maps.length > 0 && (
            <div className="space-y-6">
              <div className={`grid gap-6 ${maps.length === 1 ? 'grid-cols-1' : 'grid-cols-1 lg:grid-cols-2'}`}>
                {maps.map((item, index) => (
                  <div key={item.id} className="min-h-[450px]">
                    <MapItem
                      content={item.content as MapContent}
                      mapId={item.id}
                      mapIndex={index}
                      onTitleChange={onItemContentChange ? (newTitle) => {
                        const updatedContent = { ...item.content as MapContent, title: newTitle }
                        onItemContentChange(item.id, updatedContent)
                      } : undefined}
                    />
                  </div>
                ))}
              </div>
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
