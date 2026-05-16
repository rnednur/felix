import { useState, useEffect } from 'react'
import { X, LayoutDashboard, Sparkles, BarChart3, Lightbulb, Check, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useDashboardGenerator } from '@/hooks/useDashboardGenerator'
import { DashboardPhase } from '@/types/dashboard'

interface DashboardGeneratorModalProps {
  datasetId: string
  datasetName: string
  isOpen: boolean
  onClose: () => void
  onComplete: (workspaceId: string) => void
}

const PHASE_CONFIG: Record<DashboardPhase, { label: string; icon: React.ReactNode; color: string }> = {
  analyzing: {
    label: 'Analyzing Data',
    icon: <Sparkles className="h-4 w-4" />,
    color: 'text-blue-500',
  },
  kpis: {
    label: 'Identifying KPIs',
    icon: <BarChart3 className="h-4 w-4" />,
    color: 'text-purple-500',
  },
  charts: {
    label: 'Generating Charts',
    icon: <BarChart3 className="h-4 w-4" />,
    color: 'text-indigo-500',
  },
  summary: {
    label: 'Creating Summary',
    icon: <LayoutDashboard className="h-4 w-4" />,
    color: 'text-cyan-500',
  },
  insights: {
    label: 'Writing Insights',
    icon: <Lightbulb className="h-4 w-4" />,
    color: 'text-amber-500',
  },
  layout: {
    label: 'Finalizing Layout',
    icon: <LayoutDashboard className="h-4 w-4" />,
    color: 'text-green-500',
  },
  complete: {
    label: 'Complete',
    icon: <Check className="h-4 w-4" />,
    color: 'text-success',
  },
  error: {
    label: 'Error',
    icon: <X className="h-4 w-4" />,
    color: 'text-destructive',
  },
}

export function DashboardGeneratorModal({
  datasetId,
  datasetName,
  isOpen,
  onClose,
  onComplete,
}: DashboardGeneratorModalProps) {
  const [prompt, setPrompt] = useState('')

  const {
    isGenerating,
    progress,
    phase,
    message,
    error,
    kpis,
    charts,
    generate,
    cancel,
    reset,
  } = useDashboardGenerator({
    onComplete: (workspaceId) => {
      // Small delay to show completion state
      setTimeout(() => {
        onComplete(workspaceId)
      }, 1000)
    },
  })

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      reset()
      setPrompt('')
    }
  }, [isOpen, reset])

  const handleGenerate = () => {
    generate(datasetId, undefined, prompt || undefined)
  }

  const handleClose = () => {
    if (isGenerating) {
      cancel()
    }
    onClose()
  }

  if (!isOpen) return null

  const phaseConfig = phase ? PHASE_CONFIG[phase] : null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-card rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden border border-border">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <LayoutDashboard className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">
                Create Dashboard
              </h2>
              <p className="text-sm text-muted-foreground">
                {datasetName}
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-5">
          {!isGenerating && phase !== 'complete' && (
            <>
              {/* Prompt Input */}
              <div className="mb-5">
                <label className="block text-sm font-medium text-foreground mb-2">
                  Focus prompt (optional)
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g., Focus on sales metrics and monthly trends..."
                  className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                  rows={3}
                />
              </div>

              {/* Info */}
              <div className="bg-muted/50 rounded-lg p-4 mb-5">
                <h4 className="text-sm font-medium text-foreground mb-2">
                  What will be generated:
                </h4>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <Check className="h-3 w-3 text-success" />
                    Up to 4 KPI cards with key metrics
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-3 w-3 text-success" />
                    Up to 6 charts (bar, line, scatter, etc.)
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-3 w-3 text-success" />
                    Summary table with aggregations
                  </li>
                  <li className="flex items-center gap-2">
                    <Check className="h-3 w-3 text-success" />
                    AI-generated insights
                  </li>
                </ul>
              </div>
            </>
          )}

          {/* Progress */}
          {isGenerating && (
            <div className="space-y-4">
              {/* Progress Bar */}
              <div className="relative">
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-300 ease-out"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <span className="absolute right-0 -top-6 text-sm text-muted-foreground">
                  {progress}%
                </span>
              </div>

              {/* Current Phase */}
              {phaseConfig && (
                <div className="flex items-center gap-3">
                  <div className={`${phaseConfig.color}`}>
                    {phase === 'complete' || phase === 'error' ? (
                      phaseConfig.icon
                    ) : (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    )}
                  </div>
                  <div>
                    <p className={`text-sm font-medium ${phaseConfig.color}`}>
                      {phaseConfig.label}
                    </p>
                    <p className="text-xs text-muted-foreground">{message}</p>
                  </div>
                </div>
              )}

              {/* Phase Indicators */}
              <div className="flex items-center gap-1 mt-4">
                {(['analyzing', 'kpis', 'charts', 'summary', 'insights', 'layout'] as DashboardPhase[]).map(
                  (p, index) => {
                    const config = PHASE_CONFIG[p]
                    const isActive = phase === p
                    const isCompleted =
                      phase &&
                      ['analyzing', 'kpis', 'charts', 'summary', 'insights', 'layout', 'complete'].indexOf(
                        phase
                      ) > index

                    return (
                      <div
                        key={p}
                        className={`flex-1 h-1.5 rounded-full transition-colors ${
                          isCompleted
                            ? 'bg-primary'
                            : isActive
                            ? 'bg-primary/50'
                            : 'bg-muted'
                        }`}
                      />
                    )
                  }
                )}
              </div>

              {/* Preview of generated items */}
              {(kpis.length > 0 || charts.length > 0) && (
                <div className="mt-4 space-y-2">
                  {kpis.length > 0 && (
                    <div className="text-xs text-muted-foreground">
                      Generated {kpis.length} KPIs: {kpis.map((k) => k.name).join(', ')}
                    </div>
                  )}
                  {charts.length > 0 && (
                    <div className="text-xs text-muted-foreground">
                      Generated {charts.length} charts: {charts.map((c) => c.title).join(', ')}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Complete State */}
          {phase === 'complete' && (
            <div className="text-center py-6">
              <div className="inline-flex items-center justify-center w-12 h-12 bg-success/10 rounded-full mb-4">
                <Check className="h-6 w-6 text-success" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                Dashboard Created!
              </h3>
              <p className="text-sm text-muted-foreground">
                Redirecting to your new dashboard...
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
          {!isGenerating && phase !== 'complete' && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button onClick={handleGenerate}>
                <Sparkles className="h-4 w-4 mr-2" />
                Generate Dashboard
              </Button>
            </>
          )}
          {isGenerating && (
            <Button variant="outline" onClick={cancel}>
              Cancel Generation
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
