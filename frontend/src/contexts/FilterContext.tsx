import { createContext, useContext, useState, useCallback, ReactNode } from 'react'

/**
 * Filter types
 */
export interface FilterValue {
  column: string
  values: (string | number | boolean)[]
  type: 'categorical' | 'numeric' | 'date'
}

export interface FilterState {
  [column: string]: FilterValue
}

export interface ChartFilter {
  chartId: string
  filters: FilterState
}

export interface FilterContextType {
  // Global filters (apply to all charts)
  globalFilters: FilterState
  setGlobalFilter: (column: string, values: (string | number | boolean)[], type: FilterValue['type']) => void
  clearGlobalFilter: (column: string) => void
  clearAllGlobalFilters: () => void

  // Per-chart filters
  chartFilters: { [chartId: string]: FilterState }
  setChartFilter: (chartId: string, column: string, values: (string | number | boolean)[], type: FilterValue['type']) => void
  clearChartFilter: (chartId: string, column: string) => void
  clearAllChartFilters: (chartId: string) => void

  // Combined filters for a chart
  getFiltersForChart: (chartId: string) => FilterState

  // Check if any filters are active
  hasActiveFilters: boolean
  hasActiveGlobalFilters: boolean
  hasActiveChartFilters: (chartId: string) => boolean
}

const FilterContext = createContext<FilterContextType | undefined>(undefined)

export function FilterProvider({ children }: { children: ReactNode }) {
  const [globalFilters, setGlobalFilters] = useState<FilterState>({})
  const [chartFilters, setChartFilters] = useState<{ [chartId: string]: FilterState }>({})

  // Global filter operations
  const setGlobalFilter = useCallback((
    column: string,
    values: (string | number | boolean)[],
    type: FilterValue['type']
  ) => {
    setGlobalFilters(prev => ({
      ...prev,
      [column]: { column, values, type }
    }))
  }, [])

  const clearGlobalFilter = useCallback((column: string) => {
    setGlobalFilters(prev => {
      const { [column]: _, ...rest } = prev
      return rest
    })
  }, [])

  const clearAllGlobalFilters = useCallback(() => {
    setGlobalFilters({})
  }, [])

  // Per-chart filter operations
  const setChartFilter = useCallback((
    chartId: string,
    column: string,
    values: (string | number | boolean)[],
    type: FilterValue['type']
  ) => {
    setChartFilters(prev => ({
      ...prev,
      [chartId]: {
        ...(prev[chartId] || {}),
        [column]: { column, values, type }
      }
    }))
  }, [])

  const clearChartFilter = useCallback((chartId: string, column: string) => {
    setChartFilters(prev => {
      const chartState = prev[chartId] || {}
      const { [column]: _, ...rest } = chartState
      return {
        ...prev,
        [chartId]: rest
      }
    })
  }, [])

  const clearAllChartFilters = useCallback((chartId: string) => {
    setChartFilters(prev => {
      const { [chartId]: _, ...rest } = prev
      return rest
    })
  }, [])

  // Get combined filters for a specific chart
  const getFiltersForChart = useCallback((chartId: string): FilterState => {
    const chartSpecific = chartFilters[chartId] || {}
    // Merge global and chart-specific filters (chart-specific takes precedence)
    return { ...globalFilters, ...chartSpecific }
  }, [globalFilters, chartFilters])

  // Check if any filters are active
  const hasActiveFilters = Object.keys(globalFilters).length > 0 ||
    Object.values(chartFilters).some(cf => Object.keys(cf).length > 0)

  const hasActiveGlobalFilters = Object.keys(globalFilters).length > 0

  const hasActiveChartFilters = useCallback((chartId: string): boolean => {
    return Object.keys(chartFilters[chartId] || {}).length > 0
  }, [chartFilters])

  return (
    <FilterContext.Provider value={{
      globalFilters,
      setGlobalFilter,
      clearGlobalFilter,
      clearAllGlobalFilters,
      chartFilters,
      setChartFilter,
      clearChartFilter,
      clearAllChartFilters,
      getFiltersForChart,
      hasActiveFilters,
      hasActiveGlobalFilters,
      hasActiveChartFilters
    }}>
      {children}
    </FilterContext.Provider>
  )
}

export function useFilters() {
  const context = useContext(FilterContext)
  if (!context) {
    throw new Error('useFilters must be used within a FilterProvider')
  }
  return context
}
