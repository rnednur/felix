export interface Dataset {
  id: string
  name: string
  description?: string
  source_type: string
  status: string
  row_count: number
  size_bytes: number
  dataset_version: number
  created_at: string
  updated_at: string
}

export interface Column {
  name: string
  dtype: string
  nullable: boolean
  stats: Record<string, any>
  tags: string[]
  embedding_index: number
}

export interface Schema {
  version: number
  columns: Column[]
  computed_at: string
  total_rows: number
}

export interface QueryResult {
  query_id: string
  sql: string
  rows: any[]
  total_rows: number
  execution_time_ms?: number
  retrieved_columns?: string[]
  status: string
}

export interface ChartSuggestion {
  type: string
  spec: any
}

export interface Visualization {
  id: string
  query_id: string
  name: string
  chart_type: string
  vega_spec: any
}
