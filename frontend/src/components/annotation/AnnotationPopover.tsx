import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { X, Send, Loader2 } from 'lucide-react'
import { useAnnotation } from '@/contexts/AnnotationContext'
import { useTheme } from '@/contexts/ThemeContext'

console.log('[AnnotationPopover] Module loaded')


export function AnnotationPopover() {
  const { activeAnnotation, submitAnnotation, cancelAnnotation, isSubmitting } = useAnnotation()
  const { persona } = useTheme()
  const [feedback, setFeedback] = useState('')
  const [error, setError] = useState<string | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Debug log to verify component is rendering
  console.log('[AnnotationPopover] Component rendered, activeAnnotation:', !!activeAnnotation)

  // Focus textarea when popover opens
  useEffect(() => {
    if (activeAnnotation && textareaRef.current) {
      console.log('[AnnotationPopover] Popover opened, focusing textarea')
      textareaRef.current.focus()
    }
    // Reset state when annotation changes
    setFeedback('')
    setError(null)
  }, [activeAnnotation])

  if (!activeAnnotation) return null

  const { position, meta } = activeAnnotation

  const handleKeyDown = async (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault()
      console.log('[AnnotationPopover] Cmd+Enter pressed')

      if (!feedback.trim() || isSubmitting) {
        console.log('[AnnotationPopover] Skipping - no feedback or already submitting')
        return
      }

      console.log('[AnnotationPopover] Calling submitAnnotation from keyboard...')
      const result = await submitAnnotation(feedback)
      console.log('[AnnotationPopover] Submit result:', result)

      if (!result.success) {
        setError(result.message || 'Failed to submit. Please try again.')
      }
    }
  }

  // Get element type label
  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      kpi: 'KPI Card',
      chart: 'Chart',
      insight: 'Insight',
      table: 'Table',
      map: 'Map',
      code: 'Code Block'
    }
    return labels[type] || type
  }

  // Render using portal to escape any overflow:hidden containers
  return createPortal(
    <div
      className="fixed z-[9999] w-80 rounded-xl shadow-lg overflow-hidden"
      data-annotation-popover="true"
      style={{
        top: position.top,
        left: position.left,
        backgroundColor: persona.cardBackground,
        borderWidth: '1px',
        borderStyle: 'solid',
        borderColor: persona.cardBorder,
        boxShadow: persona.isDark
          ? '0 8px 32px -4px rgba(0,0,0,0.5)'
          : '0 8px 32px -4px rgba(0,0,0,0.15)'
      }}
      onClick={(e) => e.stopPropagation()}
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
            Add Annotation
          </h4>
          <p
            className="text-xs mt-0.5"
            style={{ color: persona.textMuted }}
          >
            {getTypeLabel(meta.type)} element
          </p>
        </div>
        <button
          onClick={cancelAnnotation}
          className="p-1.5 rounded-lg transition-colors hover:bg-black/5"
          style={{ color: persona.textMuted }}
          type="button"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Input Area - Not using form element to avoid disconnection issues */}
      <div className="p-4">
        <textarea
          ref={textareaRef}
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="What would you like to change?"
          rows={3}
          className="w-full px-3 py-2 text-sm rounded-lg resize-none focus:outline-none focus:ring-2"
          style={{
            backgroundColor: persona.isDark ? 'rgba(255,255,255,0.05)' : '#ffffff',
            borderWidth: '1px',
            borderStyle: 'solid',
            borderColor: persona.cardBorder,
            color: persona.textPrimary,
            // @ts-ignore - CSS custom property
            '--tw-ring-color': persona.primary
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
            {'\u2318'}+Enter to submit
          </span>
          <button
            type="button"
            onClick={async () => {
              console.log('[AnnotationPopover] Submit button clicked')
              if (!feedback.trim() || isSubmitting) {
                console.log('[AnnotationPopover] Skipping - no feedback or already submitting')
                return
              }

              console.log('[AnnotationPopover] Calling submitAnnotation...')
              const result = await submitAnnotation(feedback)
              console.log('[AnnotationPopover] Submit result:', result)

              if (!result.success) {
                setError(result.message || 'Failed to submit. Please try again.')
              }
            }}
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
            Submit
          </button>
        </div>
      </div>
    </div>,
    document.body
  )
}
