import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  ReactNode
} from 'react'
import {
  AnnotationContextType,
  ActiveAnnotation,
  FelixElementMeta,
  AnnotationPayload,
  AnnotationResponse,
  PopoverPosition,
  DashboardEdit
} from '@/types/annotation'

const AnnotationContext = createContext<AnnotationContextType | undefined>(undefined)

const POPOVER_WIDTH = 320
const POPOVER_OFFSET = 8

interface AnnotationProviderProps {
  children: ReactNode
  workspaceId?: string
  onAnnotationSubmit?: (payload: AnnotationPayload) => Promise<AnnotationResponse>
  onEditReceived?: (edit: DashboardEdit) => void
}

/**
 * Extracts felix metadata from an element's data attributes
 */
function extractFelixMeta(element: HTMLElement): FelixElementMeta | null {
  const id = element.dataset.felixId
  const type = element.dataset.felixType
  const configStr = element.dataset.felixConfig

  if (!id || !type) return null

  let config: Record<string, any> = {}
  if (configStr) {
    try {
      config = JSON.parse(configStr)
    } catch (e) {
      console.warn('Failed to parse felix config:', e)
    }
  }

  return { id, type, config }
}

/**
 * Finds the closest ancestor with data-felix-id attribute
 */
function findFelixElement(target: HTMLElement): HTMLElement | null {
  return target.closest('[data-felix-id]') as HTMLElement | null
}

/**
 * Calculates popover position relative to element
 */
function calculatePopoverPosition(rect: DOMRect): PopoverPosition {
  // Position below the element, centered horizontally
  let left = rect.left + rect.width / 2 - POPOVER_WIDTH / 2
  let top = rect.bottom + POPOVER_OFFSET

  // Ensure popover stays within viewport
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  // Clamp horizontal position
  if (left < 8) left = 8
  if (left + POPOVER_WIDTH > viewportWidth - 8) {
    left = viewportWidth - POPOVER_WIDTH - 8
  }

  // If not enough space below, position above
  if (top + 200 > viewportHeight) {
    top = rect.top - 200 - POPOVER_OFFSET
  }

  return { top, left }
}

/**
 * Generates a CSS selector for an element
 */
function generateSelector(element: HTMLElement): string {
  const felixId = element.dataset.felixId
  if (felixId) {
    return `[data-felix-id="${felixId}"]`
  }

  // Fallback to a more complex selector
  const tag = element.tagName.toLowerCase()
  const classes = Array.from(element.classList).slice(0, 2).join('.')
  return classes ? `${tag}.${classes}` : tag
}

export function AnnotationProvider({
  children,
  workspaceId,
  onAnnotationSubmit,
  onEditReceived
}: AnnotationProviderProps) {
  const [isAnnotationMode, setAnnotationMode] = useState(false)
  const [activeAnnotation, setActiveAnnotation] = useState<ActiveAnnotation | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [lastEdit, setLastEdit] = useState<DashboardEdit | null>(null)

  console.log('[AnnotationProvider] Rendered, activeAnnotation:', !!activeAnnotation, 'isSubmitting:', isSubmitting)

  // Handle click events to detect felix elements
  const handleClick = useCallback((event: MouseEvent) => {
    console.log('[AnnotationContext] handleClick called, isAnnotationMode:', isAnnotationMode)
    if (!isAnnotationMode) return

    const target = event.target as HTMLElement

    // Ignore clicks inside the annotation popover (z-index 9999 portal)
    const isInsidePopover = target.closest('[data-annotation-popover]')
    if (isInsidePopover) {
      console.log('[AnnotationContext] Click inside popover, ignoring')
      return
    }

    const felixElement = findFelixElement(target)

    if (!felixElement) {
      // Clicked outside a felix element - cancel current annotation
      console.log('[AnnotationContext] Clicked outside felix element, clearing annotation')
      setActiveAnnotation(null)
      return
    }

    const meta = extractFelixMeta(felixElement)
    if (!meta) return

    // Prevent default click behavior when in annotation mode
    event.preventDefault()
    event.stopPropagation()

    const rect = felixElement.getBoundingClientRect()
    const position = calculatePopoverPosition(rect)

    console.log('[AnnotationContext] Setting activeAnnotation for element:', meta.type)
    setActiveAnnotation({
      element: felixElement,
      rect,
      meta,
      position
    })
  }, [isAnnotationMode])

  // Submit annotation to backend
  const submitAnnotation = useCallback(async (feedback: string): Promise<AnnotationResponse> => {
    console.log('[AnnotationContext] submitAnnotation called with feedback:', feedback)

    if (!activeAnnotation || !feedback.trim()) {
      console.log('[AnnotationContext] No annotation or feedback, returning early')
      return { success: false, message: 'No annotation or feedback' }
    }

    console.log('[AnnotationContext] Setting isSubmitting to true')
    setIsSubmitting(true)

    const payload: AnnotationPayload = {
      elementSelector: generateSelector(activeAnnotation.element),
      elementType: activeAnnotation.meta.type,
      elementConfig: activeAnnotation.meta.config,
      feedback: feedback.trim(),
      timestamp: new Date().toISOString(),
      workspaceId
    }

    console.log('[AnnotationContext] Prepared payload:', payload)

    try {
      let response: AnnotationResponse

      if (onAnnotationSubmit) {
        console.log('[AnnotationContext] Using custom onAnnotationSubmit handler')
        response = await onAnnotationSubmit(payload)
      } else {
        // Default API call
        console.log('[AnnotationContext] Making API call to /api/v1/annotations')
        const token = localStorage.getItem('access_token')
        const res = await fetch('/api/v1/annotations', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` })
          },
          body: JSON.stringify(payload)
        })

        console.log('[AnnotationContext] API response status:', res.status)

        if (!res.ok) {
          const error = await res.text()
          console.error('[AnnotationContext] API error:', error)
          throw new Error(error || 'Failed to submit annotation')
        }

        response = await res.json()
        console.log('[AnnotationContext] API success response:', response)
      }

      // Handle successful edit
      if (response.success && response.edit) {
        console.log('[AnnotationContext] Setting lastEdit:', response.edit)
        setLastEdit(response.edit)
        console.log('[AnnotationContext] Calling onEditReceived callback...')
        if (onEditReceived) {
          console.log('[AnnotationContext] onEditReceived is defined, calling it')
          onEditReceived(response.edit)
        } else {
          console.log('[AnnotationContext] WARNING: onEditReceived is undefined!')
        }
      } else {
        console.log('[AnnotationContext] No edit to apply - success:', response.success, 'edit:', response.edit)
      }

      // Clear annotation after a brief delay to allow form submission to complete
      // This prevents "Form submission canceled because the form is not connected" error
      console.log('[AnnotationContext] Scheduling annotation clear in 50ms')
      setTimeout(() => {
        console.log('[AnnotationContext] Clearing activeAnnotation')
        setActiveAnnotation(null)
      }, 50)

      console.log('[AnnotationContext] Returning success response')
      return response
    } catch (error) {
      console.error('[AnnotationContext] Annotation submission failed:', error)
      return {
        success: false,
        message: error instanceof Error ? error.message : 'Failed to submit annotation'
      }
    } finally {
      console.log('[AnnotationContext] Setting isSubmitting to false')
      setIsSubmitting(false)
    }
  }, [activeAnnotation, workspaceId, onAnnotationSubmit, onEditReceived])

  // Cancel current annotation
  const cancelAnnotation = useCallback(() => {
    setActiveAnnotation(null)
  }, [])

  // Register/unregister click listener based on mode
  useEffect(() => {
    if (isAnnotationMode) {
      // Use capture phase to intercept clicks before components handle them
      document.addEventListener('click', handleClick, true)
      document.body.style.cursor = 'crosshair'

      return () => {
        document.removeEventListener('click', handleClick, true)
        document.body.style.cursor = ''
      }
    }
  }, [isAnnotationMode, handleClick])

  // Close annotation on Escape key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        if (activeAnnotation) {
          cancelAnnotation()
        } else if (isAnnotationMode) {
          setAnnotationMode(false)
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [activeAnnotation, isAnnotationMode, cancelAnnotation])

  return (
    <AnnotationContext.Provider
      value={{
        isAnnotationMode,
        setAnnotationMode,
        activeAnnotation,
        submitAnnotation,
        cancelAnnotation,
        isSubmitting,
        lastEdit
      }}
    >
      {children}
    </AnnotationContext.Provider>
  )
}

export function useAnnotation() {
  const context = useContext(AnnotationContext)
  if (!context) {
    throw new Error('useAnnotation must be used within an AnnotationProvider')
  }
  return context
}
