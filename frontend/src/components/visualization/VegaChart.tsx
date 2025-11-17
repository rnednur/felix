import { Vega } from 'react-vega'

interface Props {
  spec: any
  onExport?: (format: 'png' | 'svg') => void
}

export function VegaChart({ spec, onExport }: Props) {
  let vegaView: any

  const handleNewView = (view: any) => {
    vegaView = view
  }

  const handleExport = async (format: 'png' | 'svg') => {
    if (!vegaView) return

    const url = await vegaView.toImageURL(format)
    const link = document.createElement('a')
    link.download = `chart.${format}`
    link.href = url
    link.click()
  }

  return (
    <div className="space-y-2">
      <div className="bg-white p-4 rounded-lg shadow">
        <Vega spec={spec} actions={false} onNewView={handleNewView} />
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
