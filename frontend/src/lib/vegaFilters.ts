/**
 * Vega-Lite Filter Utilities
 *
 * Functions to apply filters to Vega-Lite specifications.
 * Filters are applied as transform operations on the data.
 */
import { FilterState, FilterValue, CrossfilterSelection } from '@/contexts/FilterContext'

/**
 * Apply filters to a Vega-Lite specification.
 *
 * Modifies the spec to include filter transforms that will
 * filter the data before visualization.
 *
 * @param spec - Original Vega-Lite specification
 * @param filters - Filters to apply
 * @returns Modified Vega-Lite specification with filters
 */
export function applyFiltersToSpec(spec: any, filters: FilterState): any {
  if (!spec || Object.keys(filters).length === 0) {
    return spec
  }

  // Create filter transforms for each active filter
  const filterTransforms = Object.values(filters)
    .filter((filter: FilterValue) => filter.values.length > 0)
    .map((filter: FilterValue) => createFilterTransform(filter))

  if (filterTransforms.length === 0) {
    return spec
  }

  // Clone the spec to avoid mutations
  const filteredSpec = JSON.parse(JSON.stringify(spec))

  // Add transforms to spec
  // Vega-Lite transforms can be at top-level or within layer/concat specs
  if (filteredSpec.transform) {
    filteredSpec.transform = [...filterTransforms, ...filteredSpec.transform]
  } else {
    filteredSpec.transform = filterTransforms
  }

  // Handle layered specs
  if (filteredSpec.layer) {
    filteredSpec.layer = filteredSpec.layer.map((layer: any) => {
      if (layer.transform) {
        return { ...layer, transform: [...filterTransforms, ...layer.transform] }
      }
      return { ...layer, transform: filterTransforms }
    })
  }

  // Handle concatenated specs
  if (filteredSpec.concat) {
    filteredSpec.concat = filteredSpec.concat.map((subSpec: any) =>
      applyFiltersToSpec(subSpec, filters)
    )
  }
  if (filteredSpec.hconcat) {
    filteredSpec.hconcat = filteredSpec.hconcat.map((subSpec: any) =>
      applyFiltersToSpec(subSpec, filters)
    )
  }
  if (filteredSpec.vconcat) {
    filteredSpec.vconcat = filteredSpec.vconcat.map((subSpec: any) =>
      applyFiltersToSpec(subSpec, filters)
    )
  }

  return filteredSpec
}

/**
 * Create a Vega-Lite filter transform for a single filter.
 */
function createFilterTransform(filter: FilterValue): any {
  const { column, values, type } = filter

  if (values.length === 0) {
    return null
  }

  if (type === 'categorical') {
    // Use oneOf for categorical filters
    return {
      filter: {
        field: column,
        oneOf: values
      }
    }
  }

  if (type === 'numeric' && values.length === 2) {
    // For numeric range filters, values are [min, max]
    const [min, max] = values as number[]
    return {
      filter: {
        and: [
          { field: column, gte: min },
          { field: column, lte: max }
        ]
      }
    }
  }

  if (type === 'date' && values.length === 2) {
    // For date range filters
    const [start, end] = values as string[]
    return {
      filter: {
        and: [
          { field: column, gte: { year: new Date(start).getFullYear(), month: new Date(start).getMonth() + 1, date: new Date(start).getDate() } },
          { field: column, lte: { year: new Date(end).getFullYear(), month: new Date(end).getMonth() + 1, date: new Date(end).getDate() } }
        ]
      }
    }
  }

  // Default: use oneOf
  return {
    filter: {
      field: column,
      oneOf: values
    }
  }
}

/**
 * Apply filters to inline data within a Vega-Lite spec.
 *
 * This is an alternative approach that filters the data array directly
 * instead of using Vega-Lite transforms. Useful when you need the
 * filtered data for other purposes.
 *
 * @param data - Array of data objects
 * @param filters - Filters to apply
 * @returns Filtered data array
 */
export function filterData(data: any[], filters: FilterState): any[] {
  if (!data || data.length === 0 || Object.keys(filters).length === 0) {
    return data
  }

  return data.filter(row => {
    return Object.values(filters).every((filter: FilterValue) => {
      const { column, values, type } = filter

      if (values.length === 0) return true

      const cellValue = row[column]

      if (cellValue === null || cellValue === undefined) {
        return false
      }

      if (type === 'categorical') {
        return values.includes(cellValue)
      }

      if (type === 'numeric' && values.length === 2) {
        const [min, max] = values as number[]
        const numValue = Number(cellValue)
        return numValue >= min && numValue <= max
      }

      if (type === 'date' && values.length === 2) {
        const [start, end] = values as string[]
        const dateValue = new Date(cellValue)
        return dateValue >= new Date(start) && dateValue <= new Date(end)
      }

      return values.includes(cellValue)
    })
  })
}

/**
 * Extract unique values from data for a column.
 * Useful for populating filter dropdowns from inline data.
 */
export function getUniqueValues(data: any[], column: string): any[] {
  if (!data || data.length === 0) return []

  const values = new Set<any>()
  data.forEach(row => {
    const value = row[column]
    if (value !== null && value !== undefined) {
      values.add(value)
    }
  })

  return Array.from(values).sort()
}

/**
 * Get column names from data.
 */
export function getColumnNames(data: any[]): string[] {
  if (!data || data.length === 0) return []
  return Object.keys(data[0])
}

/**
 * Apply a crossfilter selection to a Vega-Lite spec.
 *
 * When a user clicks a data point on another chart, this dims non-matching
 * data points in this chart by adding a conditional opacity encoding.
 * The source chart (the one clicked) is left unchanged.
 *
 * @param spec - Vega-Lite specification to modify
 * @param crossfilter - The active crossfilter selection, or null
 * @param thisChartId - The ID of the chart being rendered
 * @returns Modified spec with conditional opacity, or original spec unchanged
 */
export function applyCrossfilterToSpec(
  spec: any,
  crossfilter: CrossfilterSelection | null,
  thisChartId: string | undefined
): any {
  // No active crossfilter or no chart ID — nothing to do
  if (!crossfilter || !thisChartId) return spec

  // The source chart keeps full opacity — only other charts are dimmed
  if (crossfilter.sourceChartId === thisChartId) return spec

  // No spec — nothing to do
  if (!spec) return spec

  const { field, value } = crossfilter

  // Build the Vega expression test string
  // Escape string values in quotes; numbers/booleans used directly
  const valueExpr = typeof value === 'string'
    ? `'${value.replace(/'/g, "\\'")}'`
    : String(value)
  const testExpr = `datum['${field}'] == ${valueExpr}`

  const opacityEncoding = {
    condition: { test: testExpr, value: 1 },
    value: 0.15
  }

  return injectOpacityIntoSpec(JSON.parse(JSON.stringify(spec)), opacityEncoding)
}

/**
 * Recursively inject a conditional opacity encoding into a Vega-Lite spec.
 * Handles single specs, layered specs, and concatenated specs.
 */
function injectOpacityIntoSpec(spec: any, opacityEncoding: any): any {
  // Layered spec: apply to each layer
  if (spec.layer) {
    spec.layer = spec.layer.map((layer: any) => injectOpacityIntoSpec(layer, opacityEncoding))
    return spec
  }

  // Concatenated specs: recurse into each
  if (spec.concat) {
    spec.concat = spec.concat.map((s: any) => injectOpacityIntoSpec(s, opacityEncoding))
    return spec
  }
  if (spec.hconcat) {
    spec.hconcat = spec.hconcat.map((s: any) => injectOpacityIntoSpec(s, opacityEncoding))
    return spec
  }
  if (spec.vconcat) {
    spec.vconcat = spec.vconcat.map((s: any) => injectOpacityIntoSpec(s, opacityEncoding))
    return spec
  }

  // Single mark spec: add opacity to encoding
  if (spec.mark || spec.encoding) {
    if (!spec.encoding) spec.encoding = {}
    // Only inject if no opacity encoding is already present
    if (!spec.encoding.opacity) {
      spec.encoding.opacity = opacityEncoding
    }
  }

  return spec
}
