import { useState, useCallback, useRef, useEffect } from 'react'
import {
  DashboardOptions,
  DashboardPhase,
  KPIResult,
  ChartPreview,
  DashboardFilterConfig,
} from '@/types/dashboard'

interface UseDashboardGeneratorOptions {
  onComplete?: (workspaceId: string) => void
  onError?: (error: string) => void
}

interface UseDashboardGeneratorReturn {
  isGenerating: boolean
  progress: number
  phase: DashboardPhase | null
  message: string
  error: string | null
  kpis: KPIResult[]
  charts: ChartPreview[]
  insights: string[]
  filterConfig: DashboardFilterConfig[]
  workspaceId: string | null
  generate: (datasetId: string, options?: DashboardOptions, prompt?: string) => void
  cancel: () => void
  reset: () => void
}

export function useDashboardGenerator(
  options: UseDashboardGeneratorOptions = {}
): UseDashboardGeneratorReturn {
  const { onComplete, onError } = options

  const [isGenerating, setIsGenerating] = useState(false)
  const [progress, setProgress] = useState(0)
  const [phase, setPhase] = useState<DashboardPhase | null>(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [kpis, setKpis] = useState<KPIResult[]>([])
  const [charts, setCharts] = useState<ChartPreview[]>([])
  const [insights, setInsights] = useState<string[]>([])
  const [filterConfig, setFilterConfig] = useState<DashboardFilterConfig[]>([])
  const [workspaceId, setWorkspaceId] = useState<string | null>(null)

  const eventSourceRef = useRef<EventSource | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  const reset = useCallback(() => {
    setIsGenerating(false)
    setProgress(0)
    setPhase(null)
    setMessage('')
    setError(null)
    setKpis([])
    setCharts([])
    setInsights([])
    setFilterConfig([])
    setWorkspaceId(null)
  }, [])

  const cancel = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setIsGenerating(false)
    setMessage('Generation cancelled')
  }, [])

  const generate = useCallback(
    async (datasetId: string, dashboardOptions?: DashboardOptions, prompt?: string) => {
      // Reset state
      reset()
      setIsGenerating(true)
      setPhase('analyzing')
      setMessage('Starting dashboard generation...')

      const token = localStorage.getItem('access_token')
      if (!token) {
        setError('Authentication required')
        setIsGenerating(false)
        onError?.('Authentication required')
        return
      }

      // Build request body
      const requestBody = {
        dataset_id: datasetId,
        prompt: prompt || undefined,
        options: {
          include_kpis: dashboardOptions?.includeKpis ?? true,
          include_charts: dashboardOptions?.includeCharts ?? true,
          include_insights: dashboardOptions?.includeInsights ?? true,
          include_summary_table: dashboardOptions?.includeSummaryTable ?? true,
          max_charts: dashboardOptions?.maxCharts ?? 6,
          max_kpis: dashboardOptions?.maxKpis ?? 4,
        },
      }

      try {
        // Use fetch with ReadableStream for SSE
        abortControllerRef.current = new AbortController()

        const baseUrl = import.meta.env.VITE_API_URL || '/api/v1'
        const response = await fetch(`${baseUrl}/dashboards/generate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(requestBody),
          signal: abortControllerRef.current.signal,
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.detail || `HTTP error ${response.status}`)
        }

        const reader = response.body?.getReader()
        if (!reader) {
          throw new Error('Response body is not readable')
        }

        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })

          // Parse SSE events from buffer
          const lines = buffer.split('\n')
          buffer = lines.pop() || '' // Keep incomplete line in buffer

          let eventType = ''
          let eventData = ''

          for (const line of lines) {
            if (line.startsWith('event: ')) {
              eventType = line.slice(7).trim()
            } else if (line.startsWith('data: ')) {
              eventData = line.slice(6)
            } else if (line === '' && eventData) {
              // End of event, process it
              try {
                const data = JSON.parse(eventData)
                handleEvent(eventType, data)
              } catch (parseError) {
                console.error('Failed to parse SSE data:', parseError)
              }
              eventType = ''
              eventData = ''
            }
          }
        }
      } catch (err) {
        if ((err as Error).name === 'AbortError') {
          // Cancelled, don't show error
          return
        }

        const errorMessage = err instanceof Error ? err.message : 'Dashboard generation failed'
        setError(errorMessage)
        setIsGenerating(false)
        setPhase('error')
        onError?.(errorMessage)
      }
    },
    [reset, onComplete, onError]
  )

  const handleEvent = useCallback(
    (eventType: string, data: any) => {
      switch (eventType) {
        case 'progress':
          setPhase(data.phase as DashboardPhase)
          setProgress(data.progress)
          setMessage(data.message)

          // Update data if provided
          if (data.kpis) {
            setKpis(data.kpis)
          }
          if (data.charts) {
            setCharts(data.charts)
          }
          if (data.insights) {
            setInsights(data.insights)
          }
          break

        case 'filters':
          // Handle filter configuration from LLM extraction
          if (data.filters && Array.isArray(data.filters)) {
            setFilterConfig(data.filters)
          }
          break

        case 'complete':
          setPhase('complete')
          setProgress(100)
          setMessage(data.message || 'Dashboard created successfully!')
          setIsGenerating(false)

          // Update final data
          if (data.kpis) {
            setKpis(data.kpis)
          }
          if (data.charts) {
            setCharts(data.charts)
          }
          if (data.insights) {
            setInsights(data.insights)
          }
          if (data.filters) {
            setFilterConfig(data.filters)
          }

          // Note: workspace_id comes from the backend after creation
          // For now, we signal completion and let the parent component refresh
          onComplete?.(data.workspace_id || '')
          break

        case 'error':
          setPhase('error')
          setError(data.error)
          setMessage(data.error)
          setIsGenerating(false)
          onError?.(data.error)
          break

        default:
          console.log('Unknown SSE event:', eventType, data)
      }
    },
    [onComplete, onError]
  )

  return {
    isGenerating,
    progress,
    phase,
    message,
    error,
    kpis,
    charts,
    insights,
    filterConfig,
    workspaceId,
    generate,
    cancel,
    reset,
  }
}
