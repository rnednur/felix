import { VegaEmbed } from 'react-vega'
import { useRef } from 'react'

interface Props {
  spec: any
  onExport?: (format: 'png' | 'svg') => void
}

export function VegaChart({ spec, onExport }: Props) {
  const vegaViewRef = useRef<any>(null)

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

  return (
    <div className="space-y-2">
      <div className="bg-white p-4 rounded-lg shadow">
        <VegaEmbed spec={spec} options={{ actions: false }} onEmbed={handleEmbed} />
      </div>

      {onExport && (
        <div className="flex gap-2">
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
