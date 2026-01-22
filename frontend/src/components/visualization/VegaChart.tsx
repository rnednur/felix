import { VegaEmbed } from 'react-vega'
import { useRef, useMemo } from 'react'
import { useTheme } from '@/contexts/ThemeContext'

interface Props {
  spec: any
  onExport?: (format: 'png' | 'svg') => void
}

export function VegaChart({ spec, onExport }: Props) {
  const vegaViewRef = useRef<any>(null)
  const { theme } = useTheme()

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

  const handleEmbed = (result: any) => {
    vegaViewRef.current = result.view
  }

  const handleExport = async (format: 'png' | 'svg') => {
    if (!vegaViewRef.current) return

    const url = await vegaViewRef.current.toImageURL(format)
    const link = document.createElement('a')
    link.download = `chart.${format}`
    link.href = url
    link.click()
  }

  // Generate a key based on theme to force re-render when theme changes
  const themeKey = theme ? `themed-${theme.primary}` : 'default'

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex-1 min-h-0">
        <VegaEmbed
          key={themeKey}
          spec={themedSpec}
          options={{
            actions: false,
            renderer: 'svg',
            width: undefined,  // Let container control
            height: undefined  // Let container control
          }}
          onEmbed={handleEmbed}
          className="w-full h-full"
        />
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
