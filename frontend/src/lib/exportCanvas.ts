/**
 * Canvas Export Utilities
 *
 * Provides functions to export dashboard canvas to PNG and PDF formats.
 * Includes special handling for Kepler.gl maps which use WebGL rendering.
 */
import html2canvas from 'html2canvas'
import { captureAllKeplerMaps, replaceMapWithStatic } from './keplerExport'

export interface ExportOptions {
  scale?: number
  backgroundColor?: string
  format?: 'png' | 'pdf'
  filename?: string
}

/**
 * Capture a DOM element as a canvas using html2canvas
 * Includes special handling for Kepler.gl maps which use WebGL rendering.
 */
export async function captureElement(
  element: HTMLElement,
  options: ExportOptions = {}
): Promise<HTMLCanvasElement> {
  const { scale = 2, backgroundColor = '#ffffff' } = options

  // Wait for any pending renders
  await new Promise(resolve => setTimeout(resolve, 100))

  // Step 1: Capture all Kepler.gl maps as static images
  // This is needed because html2canvas cannot capture WebGL content
  const mapSnapshots = await captureAllKeplerMaps('[data-export-canvas]')

  // Step 2: Temporarily replace map canvases with static images
  let restoreMaps: (() => void) | null = null
  if (mapSnapshots.size > 0) {
    restoreMaps = replaceMapWithStatic(mapSnapshots)
    // Give the DOM a moment to update
    await new Promise(resolve => setTimeout(resolve, 50))
  }

  try {
    // Step 3: Capture the element with html2canvas
    const canvas = await html2canvas(element, {
      scale,
      backgroundColor,
      useCORS: true,
      allowTaint: true,
      logging: false,
      // Ensure SVGs are captured properly
      onclone: (clonedDoc) => {
        // Force SVG elements to have explicit dimensions
        const svgs = clonedDoc.querySelectorAll('svg')
        svgs.forEach(svg => {
          const bbox = svg.getBBox?.()
          if (bbox) {
            svg.setAttribute('width', String(bbox.width || 400))
            svg.setAttribute('height', String(bbox.height || 300))
          }
        })
      }
    })

    return canvas
  } finally {
    // Step 4: Restore original Kepler maps
    if (restoreMaps) {
      restoreMaps()
    }
  }
}

/**
 * Export a DOM element to PNG and trigger download
 */
export async function exportToPNG(
  element: HTMLElement,
  options: ExportOptions = {}
): Promise<Blob> {
  const { filename = 'dashboard' } = options

  const canvas = await captureElement(element, options)

  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (blob) {
          // Trigger download
          const url = URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.download = `${filename}.png`
          link.href = url
          link.click()
          URL.revokeObjectURL(url)
          resolve(blob)
        } else {
          reject(new Error('Failed to create PNG blob'))
        }
      },
      'image/png',
      1.0
    )
  })
}

/**
 * Export a DOM element to PDF via backend service
 */
export async function exportToPDF(
  element: HTMLElement,
  options: ExportOptions = {}
): Promise<void> {
  const { filename = 'dashboard', scale = 2 } = options

  const canvas = await captureElement(element, { ...options, scale })

  // Convert canvas to base64 PNG
  const imageData = canvas.toDataURL('image/png', 1.0)

  // Get auth token
  const token = localStorage.getItem('access_token')

  // Send to backend for PDF generation
  const response = await fetch('/api/v1/export/pdf', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: JSON.stringify({
      image_data: imageData,
      filename,
      width: canvas.width,
      height: canvas.height,
    }),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Failed to generate PDF: ${errorText}`)
  }

  // Download the PDF
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.download = `${filename}.pdf`
  link.href = url
  link.click()
  URL.revokeObjectURL(url)
}

/**
 * Get the canvas element for export (finds the main canvas container)
 */
export function getCanvasElement(): HTMLElement | null {
  // Try to find the canvas workspace element
  return document.querySelector('[data-export-canvas]') as HTMLElement | null
}

/**
 * Export the current dashboard canvas
 */
export async function exportDashboard(
  format: 'png' | 'pdf',
  options: ExportOptions = {}
): Promise<void> {
  const element = getCanvasElement()

  if (!element) {
    throw new Error('Canvas element not found. Make sure to add data-export-canvas attribute.')
  }

  if (format === 'png') {
    await exportToPNG(element, options)
  } else {
    await exportToPDF(element, options)
  }
}
