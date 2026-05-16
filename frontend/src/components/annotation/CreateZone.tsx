import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { Plus, Loader2, Send, X, BarChart3, PieChart, TrendingUp, FileText } from 'lucide-react'
import { useTheme } from '@/contexts/ThemeContext'
import {
  DashboardContext,
  ContextCreateRequest,
  AnnotationResponse,
  DashboardEdit
} from '@/types/annotation'

interface CreateZoneProps {
  context: DashboardContext
  onElementCreated: (edit: DashboardEdit) => void
}

export function CreateZone({ context, onElementCreated }: CreateZoneProps) {
  const { persona } = useTheme()
  const [isOpen, setIsOpen] = useState(false)
  const [feedback, setFeedback] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [popoverPosition, setPopoverPosition] = useState({ top: 0, left: 0 })
  const buttonRef = useRef<HTMLButtonElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Calculate popover position when opened
  useEffect(() => {
    if (isOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      const popoverWidth = 400
      const popoverHeight = 300

      let left = rect.left + rect.width / 2 - popoverWidth / 2
      let top = rect.top - popoverHeight - 10

      // Keep within viewport
      if (left < 10) left = 10
      if (left + popoverWidth > window.innerWidth - 10) {
        left = window.innerWidth - popoverWidth - 10
      }
      if (top < 10) {
        top = rect.bottom + 10
      }

      setPopoverPosition({ top, left })
    }
  }, [isOpen])

  // Focus textarea when opened
  useEffect(() => {
    if (isOpen && textareaRef.current) {
      textareaRef.current.focus()
    }
    setFeedback('')
    setError(null)
  }, [isOpen])

  const handleSubmit = async () => {
    if (!feedback.trim() || isSubmitting) return

    setIsSubmitting(true)
    setError(null)

    try {
      const request: ContextCreateRequest = {
        feedback: feedback.trim(),
        context,
        timestamp: new Date().toISOString()
      }

      console.log('[CreateZone] Submitting request:', request)

      const token = localStorage.getItem('access_token')
      const response = await fetch('/api/v1/annotations/create-from-context', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` })
        },
        body: JSON.stringify(request)
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(errorText || 'Failed to create element')
      }

      const result: AnnotationResponse = await response.json()
      console.log('[CreateZone] Response:', result)

      if (result.success && result.edit) {
        onElementCreated(result.edit)
        setIsOpen(false)
      } else {
        setError(result.message || 'Failed to create element')
      }
    } catch (err) {
      console.error('[CreateZone] Error:', err)
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault()
      handleSubmit()
    }
    if (e.key === 'Escape') {
      setIsOpen(false)
    }
  }

  // Quick action buttons
  const quickActions = [
    { icon: BarChart3, label: 'Compare KPIs', prompt: 'Create a bar chart comparing all KPIs' },
    { icon: PieChart, label: 'Pie Chart', prompt: 'Create a pie chart showing the distribution' },
    { icon: TrendingUp, label: 'Trend Chart', prompt: 'Create a line chart showing trends' },
    { icon: FileText, label: 'Summary', prompt: 'Create an insight summarizing the dashboard' }
  ]

  return (
    <>
      {/* Create Zone Button */}
      <div className="mt-6 mb-4">
        <button
          ref={buttonRef}
          onClick={() => setIsOpen(true)}
          className="w-full py-4 px-6 rounded-xl border-2 border-dashed transition-all duration-200 flex items-center justify-center gap-3 group"
          style={{
            borderColor: persona.isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)',
            backgroundColor: persona.isDark ? 'rgba(255,255,255,0.02)' : 'rgba(0,0,0,0.01)',
            color: persona.textMuted
          }}
        >
          <div
            className="p-2 rounded-lg transition-colors"
            style={{
              backgroundColor: persona.isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'
            }}
          >
            <Plus className="h-5 w-5" />
          </div>
          <div className="text-left">
            <div
              className="font-medium"
              style={{ color: persona.textSecondary }}
            >
              Add new element
            </div>
            <div className="text-sm">
              Click to create charts, KPIs, or insights using dashboard data
            </div>
          </div>
        </button>
      </div>

      {/* Popover */}
      {isOpen && createPortal(
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-[9998]"
            onClick={() => setIsOpen(false)}
          />

          {/* Popover */}
          <div
            className="fixed z-[9999] w-[400px] rounded-xl shadow-2xl overflow-hidden"
            data-annotation-popover="true"
            style={{
              top: popoverPosition.top,
              left: popoverPosition.left,
              backgroundColor: persona.cardBackground,
              borderWidth: '1px',
              borderStyle: 'solid',
              borderColor: persona.cardBorder,
              boxShadow: persona.isDark
                ? '0 20px 50px -10px rgba(0,0,0,0.7)'
                : '0 20px 50px -10px rgba(0,0,0,0.2)'
            }}
          >
            {/* Header */}
            <div
              className="flex items-center justify-between px-4 py-3"
              style={{
                backgroundColor: persona.isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.02)',
                borderBottomWidth: '1px',
                borderBottomStyle: 'solid',
                borderBottomColor: persona.cardBorder
              }}
            >
              <div>
                <h4
                  className="text-sm font-semibold"
                  style={{ color: persona.textPrimary }}
                >
                  Create New Element
                </h4>
                <p
                  className="text-xs mt-0.5"
                  style={{ color: persona.textMuted }}
                >
                  {context.kpis.length} KPIs, {context.charts.length} charts available
                </p>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg transition-colors hover:bg-black/5"
                style={{ color: persona.textMuted }}
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Quick Actions */}
            <div className="p-3 grid grid-cols-2 gap-2">
              {quickActions.map((action, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setFeedback(action.prompt)
                    textareaRef.current?.focus()
                  }}
                  className="flex items-center gap-2 p-2 rounded-lg text-left transition-colors"
                  style={{
                    backgroundColor: persona.isDark ? 'rgba(255,255,255,0.03)' : 'rgba(0,0,0,0.02)',
                    color: persona.textSecondary
                  }}
                >
                  <action.icon className="h-4 w-4" style={{ color: persona.primary }} />
                  <span className="text-xs font-medium">{action.label}</span>
                </button>
              ))}
            </div>

            {/* Input */}
            <div className="px-4 pb-4">
              <textarea
                ref={textareaRef}
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Describe what you want to create..."
                rows={3}
                className="w-full px-3 py-2 text-sm rounded-lg resize-none focus:outline-none focus:ring-2"
                style={{
                  backgroundColor: persona.isDark ? 'rgba(255,255,255,0.05)' : '#ffffff',
                  borderWidth: '1px',
                  borderStyle: 'solid',
                  borderColor: persona.cardBorder,
                  color: persona.textPrimary
                }}
                disabled={isSubmitting}
              />

              {error && (
                <p className="mt-2 text-xs text-red-500">{error}</p>
              )}

              <div className="flex items-center justify-between mt-3">
                <span
                  className="text-xs"
                  style={{ color: persona.textMuted }}
                >
                  {'\u2318'}+Enter to create
                </span>
                <button
                  onClick={handleSubmit}
                  disabled={!feedback.trim() || isSubmitting}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                  style={{
                    backgroundColor: persona.primary,
                    color: '#ffffff'
                  }}
                >
                  {isSubmitting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                  Create
                </button>
              </div>
            </div>
          </div>
        </>,
        document.body
      )}
    </>
  )
}
