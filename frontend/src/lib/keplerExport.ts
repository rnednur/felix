/**
 * Kepler.gl Map Export Utility
 *
 * Captures Kepler.gl maps as static images for dashboard export.
 * Kepler.gl uses WebGL rendering which html2canvas cannot capture directly,
 * so we need to use the canvas.toDataURL() method on the WebGL canvas.
 */

/**
 * Captures a Kepler.gl map as a PNG data URL
 * @param mapContainerId - The ID of the map container element
 * @returns Promise<string> - Base64 PNG data URL
 */
export async function captureKeplerMap(mapContainerId: string): Promise<string | null> {
  try {
    // Find the map container
    const container = document.querySelector(`[data-map-container="${mapContainerId}"]`)
    if (!container) {
      console.warn(`Map container not found: ${mapContainerId}`)
      return null
    }

    // Find the Kepler.gl canvas element (MapBox uses canvas for WebGL rendering)
    const canvas = container.querySelector('canvas.mapboxgl-canvas') as HTMLCanvasElement
    if (!canvas) {
      console.warn(`Kepler/MapBox canvas not found in container: ${mapContainerId}`)
      return null
    }

    // Wait a brief moment for the map to finish rendering
    await new Promise(resolve => setTimeout(resolve, 100))

    // Capture the canvas as a data URL
    // Note: This may fail if the canvas is "tainted" by cross-origin resources
    try {
      const dataUrl = canvas.toDataURL('image/png')
      return dataUrl
    } catch (error) {
      console.warn('Failed to capture map canvas (may be tainted):', error)
      // Fall back to creating a placeholder image
      return createPlaceholderImage(canvas.width, canvas.height, 'Map preview not available')
    }
  } catch (error) {
    console.error('Error capturing Kepler map:', error)
    return null
  }
}

/**
 * Captures all Kepler maps in a container
 * @param containerSelector - CSS selector for the container with maps
 * @returns Promise<Map<string, string>> - Map of container IDs to data URLs
 */
export async function captureAllKeplerMaps(containerSelector: string = '[data-export-canvas]'): Promise<Map<string, string>> {
  const snapshots = new Map<string, string>()

  const container = document.querySelector(containerSelector)
  if (!container) {
    console.warn('Export container not found')
    return snapshots
  }

  // Find all map containers
  const mapContainers = container.querySelectorAll('[data-map-container]')

  for (const mapContainer of mapContainers) {
    const mapId = mapContainer.getAttribute('data-map-container')
    if (mapId) {
      const snapshot = await captureKeplerMap(mapId)
      if (snapshot) {
        snapshots.set(mapId, snapshot)
      }
    }
  }

  return snapshots
}

/**
 * Temporarily replaces Kepler map canvases with static images for export
 * @param snapshots - Map of container IDs to data URLs from captureAllKeplerMaps
 * @returns Cleanup function to restore original maps
 */
export function replaceMapWithStatic(snapshots: Map<string, string>): () => void {
  const replacements: Array<{ container: Element; canvas: HTMLCanvasElement; img: HTMLImageElement }> = []

  for (const [mapId, dataUrl] of snapshots) {
    const container = document.querySelector(`[data-map-container="${mapId}"]`)
    if (!container) continue

    const canvas = container.querySelector('canvas.mapboxgl-canvas') as HTMLCanvasElement
    if (!canvas) continue

    // Create a static image element
    const img = document.createElement('img')
    img.src = dataUrl
    img.style.width = '100%'
    img.style.height = '100%'
    img.style.objectFit = 'cover'
    img.setAttribute('data-map-snapshot', mapId)

    // Hide the canvas and show the image
    canvas.style.display = 'none'
    canvas.parentElement?.appendChild(img)

    replacements.push({ container, canvas, img })
  }

  // Return cleanup function
  return () => {
    for (const { canvas, img } of replacements) {
      canvas.style.display = ''
      img.remove()
    }
  }
}

/**
 * Creates a placeholder image when map capture fails
 */
function createPlaceholderImage(width: number, height: number, text: string): string {
  const canvas = document.createElement('canvas')
  canvas.width = width || 400
  canvas.height = height || 300

  const ctx = canvas.getContext('2d')
  if (!ctx) return ''

  // Fill with light gray background
  ctx.fillStyle = '#f3f4f6'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  // Add map icon placeholder
  ctx.fillStyle = '#9ca3af'
  ctx.font = '16px system-ui, sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(text, canvas.width / 2, canvas.height / 2)

  return canvas.toDataURL('image/png')
}
