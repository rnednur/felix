import { createPortal } from 'react-dom'
import { useAnnotation } from '@/contexts/AnnotationContext'
import { useTheme } from '@/contexts/ThemeContext'

/**
 * Shows a highlight overlay around the selected element
 */
export function AnnotationHighlight() {
  const { activeAnnotation, isAnnotationMode } = useAnnotation()
  const { persona } = useTheme()

  if (!activeAnnotation || !isAnnotationMode) return null

  const { rect } = activeAnnotation

  return createPortal(
    <div
      className="fixed pointer-events-none z-[9998] transition-all duration-150"
      style={{
        top: rect.top - 4,
        left: rect.left - 4,
        width: rect.width + 8,
        height: rect.height + 8,
        border: `2px solid ${persona.primary}`,
        borderRadius: '12px',
        boxShadow: `0 0 0 4px ${persona.primary}20, inset 0 0 0 1px ${persona.primary}40`
      }}
    />,
    document.body
  )
}
