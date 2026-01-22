// Dashboard Generation Types

export type DashboardPhase =
  | 'analyzing'
  | 'kpis'
  | 'charts'
  | 'summary'
  | 'insights'
  | 'layout'
  | 'complete'
  | 'error'

export interface KPIResult {
  id: string
  name: string
  value: string | number
  formattedValue: string
  trend?: number
  trendDirection?: 'up' | 'down' | 'flat'
  comparisonLabel?: string
  column: string
  aggregation: string
  sparklineData?: number[]
}

export interface ChartPreview {
  id: string
  type: string
  title: string
}

export interface DashboardProgressData {
  kpis?: KPIResult[]
  charts?: ChartPreview[]
  insights?: string[]
}

export interface DashboardProgress {
  phase: DashboardPhase
  progress: number
  message: string
  data?: DashboardProgressData
}

export interface DashboardOptions {
  includeKpis?: boolean
  includeCharts?: boolean
  includeInsights?: boolean
  includeSummaryTable?: boolean
  maxCharts?: number
  maxKpis?: number
}

export interface DashboardGenerateRequest {
  dataset_id: string
  prompt?: string
  options?: DashboardOptions
  name?: string
}

export interface DashboardGenerateResult {
  workspace_id: string
  name: string
  dataset_id: string
  kpi_count: number
  chart_count: number
  insight_count: number
  summary_table_included: boolean
  generation_time_seconds: number
}

export interface DashboardGenerateError {
  error: string
  details?: string
  phase?: DashboardPhase
}
