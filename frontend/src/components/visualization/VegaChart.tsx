import { VegaEmbed } from 'react-vega'
import { useRef, useMemo, useState, useEffect } from 'react'
import { useTheme } from '@/contexts/ThemeContext'

interface Props {
  spec: any
  onExport?: (format: 'png' | 'svg') => void
  onCrossfilterSelect?: (field: string, value: any) => void
  onCrossfilterClear?: () => void
}

export function VegaChart({ spec, onExport, onCrossfilterSelect, onCrossfilterClear }: Props) {
  const vegaViewRef = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const { theme } = useTheme()

  // Track container dimensions for responsive sizing
  const [containerSize, setContainerSize] = useState({ width: 0, height: 0 })

  // Use ResizeObserver to detect container size changes
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect
        // Use larger threshold to prevent micro-adjustment feedback loops
        setContainerSize(prev => {
          if (Math.abs(prev.width - width) > 10 || Math.abs(prev.height - height) > 10) {
            return { width: Math.floor(width), height: Math.floor(height) }
          }
          return prev
        })
      }
    })

    resizeObserver.observe(container)

    return () => {
      resizeObserver.disconnect()
    }
  }, [])

  // Apply theme colors to the Vega-Lite spec
  const themedSpec = useMemo(() => {
    if (!theme || !theme.colors || theme.colors.length === 0) {
      return spec
    }

    // Extract color palette from theme
    const colorPalette = theme.colors.map(c => c.hex)
    const primaryColor = theme.primary || colorPalette[0]
    const secondaryColor = theme.secondary || colorPalette[1] || primaryColor

    // Create a themed spec with custom config
    return {
      ...spec,
      config: {
        ...spec.config,
        // Apply theme colors to various chart elements
        range: {
          category: colorPalette,
          ordinal: { scheme: colorPalette },
          ramp: { scheme: colorPalette }
        },
        bar: {
          fill: primaryColor,
          ...spec.config?.bar
        },
        line: {
          stroke: primaryColor,
          ...spec.config?.line
        },
        point: {
          fill: primaryColor,
          ...spec.config?.point
        },
        area: {
          fill: primaryColor,
          ...spec.config?.area
        },
        arc: {
          fill: primaryColor,
          ...spec.config?.arc
        },
        mark: {
          color: primaryColor,
          ...spec.config?.mark
        },
        axis: {
          ...spec.config?.axis
        },
        legend: {
          ...spec.config?.legend
        }
      }
    }
  }, [spec, theme])

  // Create responsive spec with container-based dimensions
  const responsiveSpec = useMemo(() => {
    if (!themedSpec) return themedSpec

    // Remove hardcoded width/height from spec to prevent conflicts
    const { width, height, ...restSpec } = themedSpec

    // Use larger padding (40px) to account for axes labels, titles, legends
    const availableWidth = Math.max(200, containerSize.width > 0 ? containerSize.width - 40 : 600)
    const availableHeight = Math.max(200, containerSize.height > 0 ? containerSize.height - 40 : 400)

    return {
      ...restSpec,
      width: availableWidth,
      height: availableHeight,
      autosize: {
        type: 'fit',
        contains: 'padding',
        resize: false  // CRITICAL: prevent Vega auto-resize fighting ResizeObserver
      }
    }
  }, [themedSpec, containerSize])

  const handleEmbed = (result: any) => {
    vegaViewRef.current = result.view

    if (onCrossfilterSelect || onCrossfilterClear) {
      // Single click: select a data point for crossfiltering
      result.view.addEventListener('click', (_event: any, item: any) => {
        if (!item || !item.datum) return
        const datum = item.datum
        const field = pickCrossfilterField(datum, spec)
        if (field && onCrossfilterSelect) {
          onCrossfilterSelect(field, datum[field])
        }
      })

      // Double-click: clear crossfilter selection
      result.view.addEventListener('dblclick', () => {
        if (onCrossfilterClear) onCrossfilterClear()
      })
    }
  }

  // Pick the best categorical field from a clicked datum + spec encoding
  function pickCrossfilterField(datum: any, currentSpec: any): string | null {
    if (!datum) return null

    // Try spec encoding fields in priority order: color > x (nominal/ordinal) > y > any string key
    const enc = currentSpec?.encoding || currentSpec?.layer?.[0]?.encoding
    const candidateFields = [
      enc?.color?.field,
      enc?.x?.type === 'nominal' || enc?.x?.type === 'ordinal' ? enc?.x?.field : null,
      enc?.y?.type === 'nominal' || enc?.y?.type === 'ordinal' ? enc?.y?.field : null,
      enc?.column?.field,
      enc?.row?.field,
    ].filter(Boolean)

    for (const field of candidateFields) {
      if (field && datum[field] !== undefined) return field
    }

    // Fallback: first string-valued key in the datum (skip internal Vega keys starting with _)
    for (const key of Object.keys(datum)) {
      if (key.startsWith('_')) continue
      const val = datum[key]
      if (typeof val === 'string') return key
    }

    return null
  }

  const handleExport = async (format: 'png' | 'svg') => {
    if (!vegaViewRef.current) return

    const url = await vegaViewRef.current.toImageURL(format)
    const link = document.createElement('a')
    link.download = `chart.${format}`
    link.href = url
    link.click()
  }

  // Generate a key based on theme, spec, AND container dimensions to force re-render
  const specHash = useMemo(() => {
    try {
      return JSON.stringify(spec).slice(0, 200)
    } catch {
      return 'spec'
    }
  }, [spec])

  // Include container dimensions in key to force Vega re-render on resize
  const chartKey = useMemo(() => {
    const themeKey = theme ? `themed-${theme.primary}` : 'default'
    const sizeKey = `${containerSize.width}x${containerSize.height}`
    return `${themeKey}-${sizeKey}-${specHash}`
  }, [theme, containerSize, specHash])

  // Don't render until we have container dimensions
  const hasSize = containerSize.width > 0 && containerSize.height > 0

  return (
    <div className="w-full h-full flex flex-col">
      <div ref={containerRef} className="flex-1 min-h-0 overflow-hidden">
        {hasSize && responsiveSpec && (
          <VegaEmbed
            key={chartKey}
            spec={responsiveSpec}
            options={{
              actions: false,
              renderer: 'svg'
              // Do NOT pass explicit width/height here - they conflict with
              // the dimensions already set in responsiveSpec and cause double padding
            }}
            onEmbed={handleEmbed}
            className="w-full h-full"
          />
        )}
      </div>

      {onExport && (
        <div className="flex gap-2 mt-2 flex-shrink-0">
          <button
            onClick={() => handleExport('png')}
            className="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200"
          >
            Export PNG
          </button>
          <button
            onClick={() => handleExport('svg')}
            className="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200"
          >
            Export SVG
          </button>
        </div>
      )}
    </div>
  )
}
