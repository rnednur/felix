import { MessageSquarePlus, X } from 'lucide-react'
import { useAnnotation } from '@/contexts/AnnotationContext'
import { useTheme } from '@/contexts/ThemeContext'

interface AnnotationToggleProps {
  className?: string
}

export function AnnotationToggle({ className = '' }: AnnotationToggleProps) {
  const { isAnnotationMode, setAnnotationMode, activeAnnotation, cancelAnnotation } = useAnnotation()
  const { persona } = useTheme()

  const handleToggle = () => {
    if (isAnnotationMode) {
      if (activeAnnotation) {
        cancelAnnotation()
      }
      setAnnotationMode(false)
    } else {
      setAnnotationMode(true)
    }
  }

  return (
    <button
      onClick={handleToggle}
      className={`flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition-all ${className}`}
      style={{
        backgroundColor: isAnnotationMode ? persona.primary : 'transparent',
        color: isAnnotationMode ? '#ffffff' : persona.textPrimary,
        borderWidth: '1px',
        borderStyle: 'solid',
        borderColor: isAnnotationMode ? persona.primary : persona.cardBorder
      }}
      title={isAnnotationMode ? 'Exit annotation mode (Esc)' : 'Enter annotation mode'}
    >
      {isAnnotationMode ? (
        <>
          <X className="h-4 w-4" />
          Exit Annotate
        </>
      ) : (
        <>
          <MessageSquarePlus className="h-4 w-4" />
          Annotate
        </>
      )}
    </button>
  )
}
