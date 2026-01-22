import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Filter, X, ChevronRight, Settings2, Loader2 } from 'lucide-react'
import axios from '@/services/api'
import { FilterDropdown } from './FilterDropdown'
import { useFilters } from '@/contexts/FilterContext'
import { DashboardFilterConfig } from '@/types/dashboard'

interface FilterOption {
  value: string | number | boolean
  label: string
  count?: number
}

interface CascadingGlobalFilterBarProps {
  datasetId: string
  filterConfig?: DashboardFilterConfig[]
  onConfigureClick?: () => void
  className?: string
}

export function CascadingGlobalFilterBar({
  datasetId,
  filterConfig: externalConfig,
  onConfigureClick,
  className = ''
}: CascadingGlobalFilterBarProps) {
  const {
    globalFilters,
    setGlobalFilter,
    clearGlobalFilter,
    clearAllGlobalFilters,
    hasActiveGlobalFilters,
    filterConfig: contextConfig,
    setFilterConfig,
    isFilterVisible,
    getParentFilterValues
  } = useFilters()

  // Use external config if provided, otherwise use context config
  const filterConfig = externalConfig || contextConfig

  // Set filter config to context when external config is provided
  useEffect(() => {
    if (externalConfig && externalConfig.length > 0) {
      setFilterConfig(externalConfig)
    }
  }, [externalConfig, setFilterConfig])

  // State for filter options (lazy loaded)
  const [filterOptions, setFilterOptions] = useState<{ [column: string]: FilterOption[] }>({})
  const [loadingColumn, setLoadingColumn] = useState<string | null>(null)

  // Fetch filter values for a column (with optional parent filter context)
  const fetchColumnValues = async (column: string, parentFilters?: Record<string, (string | number | boolean)[]>) => {
    if (filterOptions[column] && !parentFilters) return

    setLoadingColumn(column)
    try {
      // Build query params with parent filter context
      const params = new URLSearchParams()
      if (parentFilters && Object.keys(parentFilters).length > 0) {
        params.set('filters', JSON.stringify(parentFilters))
      }

      const url = `/filters/datasets/${datasetId}/columns/${column}/values${params.toString() ? '?' + params.toString() : ''}`
      const response = await axios.get(url)

      const options: FilterOption[] = response.data.values.map((v: any) => ({
        value: v.value,
        label: String(v.value),
        count: v.count
      }))

      setFilterOptions(prev => ({ ...prev, [column]: options }))
    } catch (error) {
      console.error('Failed to fetch column values:', error)
      // Set empty options to prevent infinite loading
      setFilterOptions(prev => ({ ...prev, [column]: [] }))
    } finally {
      setLoadingColumn(null)
    }
  }

  // Get parent filter context for a dependent filter
  const getParentFilterContext = (filter: DashboardFilterConfig): Record<string, (string | number | boolean)[]> | undefined => {
    if (!filter.dependsOn) return undefined

    const parentValues = getParentFilterValues(filter)
    if (!parentValues || parentValues.length === 0) return undefined

    return { [filter.dependsOn]: parentValues }
  }

  // Refetch dependent filter values when parent changes
  useEffect(() => {
    filterConfig.forEach(filter => {
      if (filter.dependsOn && isFilterVisible(filter)) {
        const parentContext = getParentFilterContext(filter)
        if (parentContext) {
          fetchColumnValues(filter.column, parentContext)
        }
      }
    })
  }, [globalFilters, filterConfig])

  // Get visible filters (those whose parents have selections)
  const visibleFilters = filterConfig.filter(isFilterVisible)

  // Get pending filters (those waiting for parent selection)
  const pendingFilters = filterConfig.filter(f => f.dependsOn && !isFilterVisible(f))

  if (filterConfig.length === 0) {
    return null
  }

  const activeFilterCount = Object.keys(globalFilters).length

  return (
    <div className={`bg-white border-b border-slate-200 ${className}`}>
      <div className="px-5 py-3 flex items-center gap-4">
        {/* Filter icon and label */}
        <div className="flex items-center gap-2 text-slate-600">
          <Filter className="h-4 w-4" />
          <span className="text-sm font-medium">Filters</span>
        </div>

        {/* Filter dropdowns */}
        <div className="flex items-center gap-2 flex-wrap">
          {visibleFilters.map((filter, index) => {
            const options = filterOptions[filter.column] || []
            const selectedValues = globalFilters[filter.column]?.values || []
            const isLoading = loadingColumn === filter.column
            const parentFilter = filter.dependsOn ? filterConfig.find(f => f.column === filter.dependsOn) : null

            return (
              <div key={filter.id} className="flex items-center gap-1">
                {/* Show arrow between cascading filters */}
                {index > 0 && filter.dependsOn && (
                  <ChevronRight className="h-4 w-4 text-slate-400 mx-1" />
                )}

                <div
                  onMouseEnter={() => {
                    if (!filterOptions[filter.column]) {
                      const parentContext = getParentFilterContext(filter)
                      fetchColumnValues(filter.column, parentContext)
                    }
                  }}
                >
                  <FilterDropdown
                    column={filter.column}
                    label={filter.label}
                    options={options}
                    selectedValues={selectedValues}
                    onSelectionChange={(values) => {
                      if (values.length > 0) {
                        setGlobalFilter(filter.column, values, filter.type)
                      } else {
                        clearGlobalFilter(filter.column)
                      }
                    }}
                    onClear={() => clearGlobalFilter(filter.column)}
                    placeholder={isLoading ? 'Loading...' : 'All'}
                    multiSelect={filter.multiSelect !== false}
                  />
                </div>
              </div>
            )
          })}

          {/* Show pending filter indicators */}
          {pendingFilters.map(filter => {
            const parentFilter = filterConfig.find(f => f.column === filter.dependsOn)
            return (
              <div key={filter.id} className="flex items-center gap-1">
                <ChevronRight className="h-4 w-4 text-slate-300 mx-1" />
                <div className="px-3 py-2 text-sm text-slate-400 bg-slate-50 border border-dashed border-slate-300 rounded-lg">
                  {filter.label}: <span className="italic">Select {parentFilter?.label || 'parent'} first</span>
                </div>
              </div>
            )
          })}
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Active filter count & clear button */}
        {hasActiveGlobalFilters && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded-full">
              {activeFilterCount} active
            </span>
            <button
              onClick={clearAllGlobalFilters}
              className="flex items-center gap-1 px-2 py-1 text-sm text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
            >
              <X className="h-3.5 w-3.5" />
              Clear all
            </button>
          </div>
        )}

        {/* Configure filters button */}
        {onConfigureClick && (
          <button
            onClick={onConfigureClick}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <Settings2 className="h-4 w-4" />
            Configure
          </button>
        )}
      </div>
    </div>
  )
}
