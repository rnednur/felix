// Canvas item types for Felix

/**
 * Display size for dashboard grid items
 * - small: 1 column (compact view)
 * - medium: 1 column on mobile, flexible on desktop (default)
 * - large: 2 columns on desktop
 * - full: full width (all columns)
 */
export type DisplaySize = 'small' | 'medium' | 'large' | 'full'

export interface CanvasItemPosition {
  x: number
  y: number
  width: number
  height: number
  zIndex?: number
}

export interface QueryResultContent {
  columns: string[]
  rows: any[]
  sql: string
  totalRows: number
  executionTime?: number
}

export interface ChartContent {
  chartType: string
  vegaSpec: any
  title?: string
  sourceQueryId?: string
  data?: any[]
  displaySize?: DisplaySize
}

export interface InsightNoteContent {
  content: string // Markdown
  aiGenerated: boolean
  tags?: string[]
}

export interface CodeBlockContent {
  language: 'sql' | 'python'
  code: string
  editable: boolean
  executionResult?: any
}

export interface MLModelContent {
  modelId: string
  modelType: string
  metrics: Record<string, number>
  features: string[]
  predictions?: any[]
}

export interface KPICardContent {
  id: string
  name: string
  value: string | number
  formattedValue: string
  trend?: number
  trendDirection?: 'up' | 'down' | 'flat'
  comparisonLabel?: string
  column?: string
  aggregation?: string
  sparklineData?: number[]
}

export interface MapContent {
  title?: string
  data: any[]
  spatialColumns: {
    lat: string
    lng: string
  }
  config?: any  // Kepler.gl config
  sourceQueryId?: string
  datasetId?: string
  // For export - captured static image
  staticImageUrl?: string
  displaySize?: DisplaySize
}

export type CanvasItemContent =
  | QueryResultContent
  | ChartContent
  | InsightNoteContent
  | CodeBlockContent
  | MLModelContent
  | KPICardContent
  | MapContent

export type CanvasItemType =
  | 'query-result'
  | 'chart'
  | 'insight-note'
  | 'code-block'
  | 'ml-model'
  | 'kpi-card'
  | 'map'

export interface CanvasItem {
  id: string
  workspaceId: string
  type: CanvasItemType
  x: number
  y: number
  width: number
  height: number
  zIndex: number
  content: CanvasItemContent
  createdAt?: string
  updatedAt?: string
}

export interface Workspace {
  id: string
  name: string
  description?: string
  ownerId: string
  datasetId?: string
  datasetGroupId?: string
  createdAt: string
  updatedAt: string
  deletedAt?: string
  items?: CanvasItem[]
}

// AG-UI Event types
export interface AGUIEvent {
  event: string
  data: any
}

export interface CanvasItemCreateEvent {
  itemType: CanvasItemType
  position: { x: number; y: number }
  width: number
  height: number
  content: CanvasItemContent
}
