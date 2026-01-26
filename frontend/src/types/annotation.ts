// Annotation types for Felix Canvas

/**
 * Metadata extracted from a data-felix-* annotated element
 */
export interface FelixElementMeta {
  id: string           // from data-felix-id
  type: string         // from data-felix-type (e.g., 'kpi', 'chart', 'insight')
  config: Record<string, any>  // parsed from data-felix-config JSON
}

/**
 * Position for the annotation popover
 */
export interface PopoverPosition {
  top: number
  left: number
}

/**
 * Active annotation state
 */
export interface ActiveAnnotation {
  element: HTMLElement
  rect: DOMRect
  meta: FelixElementMeta
  position: PopoverPosition
}

/**
 * Payload sent to backend API
 */
export interface AnnotationPayload {
  elementSelector: string      // CSS selector to identify the element
  elementType: string          // e.g., 'kpi', 'chart', 'insight', 'table', 'map', 'code'
  elementConfig: Record<string, any>  // Current config of the element
  feedback: string             // User's annotation text
  timestamp: string            // ISO timestamp
  workspaceId?: string         // Optional workspace context
}

/**
 * Response from backend after processing annotation
 */
export interface DashboardEdit {
  elementId: string
  action: 'modify' | 'add' | 'remove'
  changes: Record<string, any>
  reasoning?: string
}

/**
 * API response wrapper
 */
export interface AnnotationResponse {
  success: boolean
  edit?: DashboardEdit
  message?: string
}

/**
 * Context type for the AnnotationProvider
 */
export interface AnnotationContextType {
  isAnnotationMode: boolean
  setAnnotationMode: (enabled: boolean) => void
  activeAnnotation: ActiveAnnotation | null
  submitAnnotation: (feedback: string) => Promise<AnnotationResponse>
  cancelAnnotation: () => void
  isSubmitting: boolean
  lastEdit: DashboardEdit | null
}

/**
 * KPI context for dashboard-aware creation
 */
export interface KPIContext {
  id: string
  name: string
  value: number | string | null
  formattedValue: string
  trend?: number
  trendDirection?: 'up' | 'down' | 'flat'
}

/**
 * Chart context for dashboard-aware creation
 */
export interface ChartContext {
  id: string
  chartType: string
  title?: string
  data: any[]
}

/**
 * Full dashboard context for creating elements with awareness of all data
 */
export interface DashboardContext {
  datasetId?: string
  workspaceId?: string
  kpis: KPIContext[]
  charts: ChartContext[]
  columns: string[]
  sampleData: any[]
}

/**
 * Request to create an element with full dashboard context
 */
export interface ContextCreateRequest {
  feedback: string
  context: DashboardContext
  timestamp?: string
}
