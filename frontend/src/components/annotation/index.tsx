// Annotation system exports
export { AnnotationProvider, useAnnotation } from '@/contexts/AnnotationContext'
export { AnnotationPopover } from './AnnotationPopover'
export { AnnotationHighlight } from './AnnotationHighlight'
export { AnnotationToggle } from './AnnotationToggle'
export { CreateZone } from './CreateZone'

// Types
export type {
  FelixElementMeta,
  ActiveAnnotation,
  AnnotationPayload,
  AnnotationResponse,
  DashboardEdit,
  AnnotationContextType,
  DashboardContext,
  KPIContext,
  ChartContext,
  ContextCreateRequest
} from '@/types/annotation'

// Import components for use in AnnotationOverlay
import { AnnotationHighlight } from './AnnotationHighlight'
import { AnnotationPopover } from './AnnotationPopover'

/**
 * Composite component that includes all annotation UI overlays.
 * Render this inside AnnotationProvider at the end of your dashboard.
 */
export function AnnotationOverlay() {
  return (
    <>
      <AnnotationHighlight />
      <AnnotationPopover />
    </>
  )
}
