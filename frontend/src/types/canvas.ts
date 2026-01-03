// Canvas item types for Felix

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

export type CanvasItemContent =
  | QueryResultContent
  | ChartContent
  | InsightNoteContent
  | CodeBlockContent
  | MLModelContent

export type CanvasItemType =
  | 'query-result'
  | 'chart'
  | 'insight-note'
  | 'code-block'
  | 'ml-model'

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
