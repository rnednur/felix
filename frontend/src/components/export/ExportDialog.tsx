import { useState } from 'react'
import { X, Download, Image, FileText, Loader2, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { exportToPNG, exportToPDF } from '@/lib/exportCanvas'

interface ExportDialogProps {
  isOpen: boolean
  onClose: () => void
  canvasElement: HTMLElement | null
  workspaceName?: string
}

type ExportFormat = 'png' | 'pdf'
type ExportState = 'idle' | 'exporting' | 'success' | 'error'

const FORMAT_OPTIONS: { format: ExportFormat; label: string; description: string; icon: React.ReactNode }[] = [
  {
    format: 'png',
    label: 'PNG Image',
    description: 'High-resolution image, great for sharing',
    icon: <Image className="h-5 w-5" />,
  },
  {
    format: 'pdf',
    label: 'PDF Document',
    description: 'Print-ready document with full layout',
    icon: <FileText className="h-5 w-5" />,
  },
]

export function ExportDialog({
  isOpen,
  onClose,
  canvasElement,
  workspaceName = 'dashboard',
}: ExportDialogProps) {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('png')
  const [exportState, setExportState] = useState<ExportState>('idle')
  const [error, setError] = useState<string | null>(null)

  const handleExport = async () => {
    if (!canvasElement) {
      setError('Canvas element not found')
      return
    }

    setExportState('exporting')
    setError(null)

    try {
      const filename = `${workspaceName.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}`

      if (selectedFormat === 'png') {
        await exportToPNG(canvasElement, { filename })
      } else {
        await exportToPDF(canvasElement, { filename })
      }

      setExportState('success')

      // Reset after showing success
      setTimeout(() => {
        setExportState('idle')
        onClose()
      }, 1500)
    } catch (err) {
      console.error('Export failed:', err)
      setError(err instanceof Error ? err.message : 'Export failed')
      setExportState('error')
    }
  }

  const handleClose = () => {
    if (exportState === 'exporting') return
    setExportState('idle')
    setError(null)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-card rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden border border-border">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Download className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">
                Export Dashboard
              </h2>
              <p className="text-sm text-muted-foreground">
                Choose your export format
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            disabled={exportState === 'exporting'}
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors disabled:opacity-50"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-5">
          {exportState === 'idle' && (
            <>
              {/* Format Selection */}
              <div className="space-y-3">
                {FORMAT_OPTIONS.map((option) => (
                  <button
                    key={option.format}
                    onClick={() => setSelectedFormat(option.format)}
                    className={`w-full flex items-center gap-4 p-4 rounded-lg border-2 transition-all ${
                      selectedFormat === option.format
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-muted-foreground/30 hover:bg-muted/50'
                    }`}
                  >
                    <div
                      className={`p-2 rounded-lg ${
                        selectedFormat === option.format
                          ? 'bg-primary/10 text-primary'
                          : 'bg-muted text-muted-foreground'
                      }`}
                    >
                      {option.icon}
                    </div>
                    <div className="text-left flex-1">
                      <p
                        className={`font-medium ${
                          selectedFormat === option.format
                            ? 'text-primary'
                            : 'text-foreground'
                        }`}
                      >
                        {option.label}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {option.description}
                      </p>
                    </div>
                    {selectedFormat === option.format && (
                      <div className="w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                        <Check className="h-3 w-3 text-primary-foreground" />
                      </div>
                    )}
                  </button>
                ))}
              </div>

              {/* Info */}
              <div className="mt-5 bg-muted/50 rounded-lg p-4">
                <p className="text-sm text-muted-foreground">
                  {selectedFormat === 'png' ? (
                    <>
                      The entire dashboard will be captured as a high-resolution
                      PNG image at 2x scale for crisp display on retina screens.
                    </>
                  ) : (
                    <>
                      Your dashboard will be exported as a PDF document,
                      perfect for printing or sharing as a formal report.
                    </>
                  )}
                </p>
              </div>
            </>
          )}

          {/* Exporting State */}
          {exportState === 'exporting' && (
            <div className="text-center py-8">
              <Loader2 className="h-10 w-10 text-primary animate-spin mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-foreground mb-2">
                Exporting Dashboard...
              </h3>
              <p className="text-sm text-muted-foreground">
                {selectedFormat === 'png'
                  ? 'Capturing canvas and generating image...'
                  : 'Generating PDF document...'}
              </p>
            </div>
          )}

          {/* Success State */}
          {exportState === 'success' && (
            <div className="text-center py-8">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-success/10 rounded-full mb-4">
                <Check className="h-6 w-6 text-success" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                Export Complete!
              </h3>
              <p className="text-sm text-muted-foreground">
                Your {selectedFormat.toUpperCase()} file is downloading...
              </p>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4 mt-4">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border bg-muted/30">
          {exportState === 'idle' && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button onClick={handleExport} disabled={!canvasElement}>
                <Download className="h-4 w-4 mr-2" />
                Export {selectedFormat.toUpperCase()}
              </Button>
            </>
          )}
          {exportState === 'error' && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Close
              </Button>
              <Button onClick={handleExport}>Try Again</Button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
