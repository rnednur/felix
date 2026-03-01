import { createContext, useContext, useState, useCallback, useMemo, ReactNode } from 'react'
import { DashboardFilterConfig } from '@/types/dashboard'

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

export interface CrossfilterSelection {
  sourceChartId: string
  field: string
  value: any
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

  // Crossfilter selection (click-to-filter across charts)
  crossfilterSelection: CrossfilterSelection | null
  setCrossfilterSelection: (chartId: string, field: string, value: any) => void
  clearCrossfilterSelection: () => void

  // Cascading filter configuration
  filterConfig: DashboardFilterConfig[]
  setFilterConfig: (config: DashboardFilterConfig[]) => void
  clearFilterConfig: () => void

  // Cascading filter helpers
  getVisibleFilters: () => DashboardFilterConfig[]
  isFilterVisible: (filter: DashboardFilterConfig) => boolean
  getParentFilterValues: (filter: DashboardFilterConfig) => (string | number | boolean)[] | null
}

const FilterContext = createContext<FilterContextType | undefined>(undefined)

export function FilterProvider({ children }: { children: ReactNode }) {
  const [globalFilters, setGlobalFilters] = useState<FilterState>({})
  const [chartFilters, setChartFilters] = useState<{ [chartId: string]: FilterState }>({})
  const [filterConfig, setFilterConfigState] = useState<DashboardFilterConfig[]>([])
  const [crossfilterSelection, setCrossfilterSelectionState] = useState<CrossfilterSelection | null>(null)

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

  // Cascading filter configuration operations
  const setFilterConfig = useCallback((config: DashboardFilterConfig[]) => {
    // Sort by order to ensure proper hierarchy
    const sorted = [...config].sort((a, b) => a.order - b.order)
    setFilterConfigState(sorted)
  }, [])

  const clearFilterConfig = useCallback(() => {
    setFilterConfigState([])
    // Also clear global filters when config is cleared
    setGlobalFilters({})
  }, [])

  // Check if a filter should be visible based on its parent's selection
  const isFilterVisible = useCallback((filter: DashboardFilterConfig): boolean => {
    // Filters without dependencies are always visible
    if (!filter.dependsOn) return true

    // Check if parent filter has a selection
    const parentFilter = globalFilters[filter.dependsOn]
    return parentFilter && parentFilter.values.length > 0
  }, [globalFilters])

  // Get parent filter values for a dependent filter
  const getParentFilterValues = useCallback((filter: DashboardFilterConfig): (string | number | boolean)[] | null => {
    if (!filter.dependsOn) return null
    const parentFilter = globalFilters[filter.dependsOn]
    return parentFilter?.values || null
  }, [globalFilters])

  // Get all visible filters based on current selections
  const getVisibleFilters = useCallback((): DashboardFilterConfig[] => {
    return filterConfig.filter(isFilterVisible)
  }, [filterConfig, isFilterVisible])

  // Crossfilter operations
  const setCrossfilterSelection = useCallback((chartId: string, field: string, value: any) => {
    setCrossfilterSelectionState(prev => {
      // Toggle off if clicking the same chart + field + value
      if (prev && prev.sourceChartId === chartId && prev.field === field && prev.value === value) {
        return null
      }
      return { sourceChartId: chartId, field, value }
    })
  }, [])

  const clearCrossfilterSelection = useCallback(() => {
    setCrossfilterSelectionState(null)
  }, [])

  // When a parent filter changes, clear dependent filter selections
  const setGlobalFilterWithCascade = useCallback((
    column: string,
    values: (string | number | boolean)[],
    type: FilterValue['type']
  ) => {
    // First, set the new filter value
    setGlobalFilters(prev => ({
      ...prev,
      [column]: { column, values, type }
    }))

    // Then, clear any dependent filters (filters that depend on this column)
    const dependentFilters = filterConfig.filter(f => f.dependsOn === column)
    if (dependentFilters.length > 0) {
      setGlobalFilters(prev => {
        const newState = { ...prev, [column]: { column, values, type } }
        dependentFilters.forEach(dep => {
          delete newState[dep.column]
        })
        return newState
      })
    }
  }, [filterConfig])

  return (
    <FilterContext.Provider value={{
      globalFilters,
      setGlobalFilter: setGlobalFilterWithCascade,
      clearGlobalFilter,
      clearAllGlobalFilters,
      chartFilters,
      setChartFilter,
      clearChartFilter,
      clearAllChartFilters,
      getFiltersForChart,
      hasActiveFilters,
      hasActiveGlobalFilters,
      hasActiveChartFilters,
      // Crossfilter
      crossfilterSelection,
      setCrossfilterSelection,
      clearCrossfilterSelection,
      // Cascading filter support
      filterConfig,
      setFilterConfig,
      clearFilterConfig,
      getVisibleFilters,
      isFilterVisible,
      getParentFilterValues
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
