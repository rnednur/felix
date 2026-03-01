import { useState, useCallback, useRef, useMemo, useEffect } from 'react'
// Use the mapbox subpath of react-map-gl v8 to get correct types
// (avoids conflict with @types/react-map-gl v6 which has old class-based API)
import Map, { Source, Layer, Popup, NavigationControl } from 'react-map-gl/mapbox'
import type { MapRef } from 'react-map-gl/mapbox'
import type { MapLayerMouseEvent } from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { List, X, Search, MapPin, BarChart2, Globe } from 'lucide-react'
import { MapStatsPanel } from './MapStatsPanel'
import { MapChartOverlay } from './MapChartOverlay'

// Foursquare-style color palette (12 colors)
const CATEGORY_COLORS = [
  '#6366f1', '#f59e0b', '#10b981', '#ef4444',
  '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6',
  '#f97316', '#06b6d4', '#84cc16', '#e11d48',
]

// Country centroids — used when dataset lat/lng values are synthetic/incorrect
const COUNTRY_CENTROIDS: Record<string, [number, number]> = {
  'Afghanistan': [33.93911, 67.709953], 'Albania': [41.1533, 20.1683], 'Algeria': [28.0339, 1.6596],
  'Angola': [-11.2027, 17.8739], 'Argentina': [-38.4161, -63.6167], 'Australia': [-25.2744, 133.7751],
  'Austria': [47.5162, 14.5501], 'Azerbaijan': [40.1431, 47.5769], 'Bangladesh': [23.6850, 90.3563],
  'Belgium': [50.5039, 4.4699], 'Bolivia': [-16.2902, -63.5887], 'Bosnia': [43.9159, 17.6791],
  'Brazil': [-14.2350, -51.9253], 'Bulgaria': [42.7339, 25.4858], 'Cambodia': [12.5657, 104.9910],
  'Cameroon': [7.3697, 12.3547], 'Canada': [56.1304, -106.3468], 'Chad': [15.4542, 18.7322],
  'Chile': [-35.6751, -71.5430], 'China': [35.8617, 104.1954], 'Colombia': [4.5709, -74.2973],
  'Congo': [-4.0383, 21.7587], 'Croatia': [45.1, 15.2], 'Cuba': [21.5218, -77.7812],
  'Czech Republic': [49.8175, 15.4730], 'Denmark': [56.2639, 9.5018], 'Ecuador': [-1.8312, -78.1834],
  'Egypt': [26.8206, 30.8025], 'Ethiopia': [9.1450, 40.4897], 'Finland': [61.9241, 25.7482],
  'France': [46.2276, 2.2137], 'Germany': [51.1657, 10.4515], 'Ghana': [7.9465, -1.0232],
  'Greece': [39.0742, 21.8243], 'Guatemala': [15.7835, -90.2308], 'Haiti': [18.9712, -72.2852],
  'Honduras': [15.1999, -86.2419], 'Hungary': [47.1625, 19.5033], 'India': [20.5937, 78.9629],
  'Indonesia': [-0.7893, 113.9213], 'Iran': [32.4279, 53.6880], 'Iraq': [33.2232, 43.6793],
  'Ireland': [53.1424, -7.6921], 'Israel': [31.0461, 34.8516], 'Italy': [41.8719, 12.5674],
  'Japan': [36.2048, 138.2529], 'Jordan': [30.5852, 36.2384], 'Kazakhstan': [48.0196, 66.9237],
  'Kenya': [-0.0236, 37.9062], 'Libya': [26.3351, 17.2283], 'Madagascar': [-18.7669, 46.8691],
  'Malaysia': [4.2105, 101.9758], 'Mali': [17.5707, -3.9962], 'Mexico': [23.6345, -102.5528],
  'Morocco': [31.7917, -7.0926], 'Mozambique': [-18.6657, 35.5296], 'Myanmar': [21.9162, 95.9560],
  'Nepal': [28.3949, 84.1240], 'Netherlands': [52.1326, 5.2913], 'New Zealand': [-40.9006, 174.8860],
  'Nicaragua': [12.8654, -85.2072], 'Niger': [17.6078, 8.0817], 'Nigeria': [9.0820, 8.6753],
  'North Korea': [40.3399, 127.5101], 'Norway': [60.4720, 8.4689], 'Pakistan': [30.3753, 69.3451],
  'Palestine': [31.9522, 35.2332], 'Panama': [8.5380, -80.7821], 'Papua New Guinea': [-6.3150, 143.9555],
  'Paraguay': [-23.4425, -58.4438], 'Peru': [-9.1900, -75.0152], 'Philippines': [12.8797, 121.7740],
  'Poland': [51.9194, 19.1451], 'Portugal': [39.3999, -8.2245], 'Romania': [45.9432, 24.9668],
  'Russia': [61.5240, 105.3188], 'Rwanda': [-1.9403, 29.8739], 'Saudi Arabia': [23.8859, 45.0792],
  'Senegal': [14.4974, -14.4524], 'Serbia': [44.0165, 21.0059], 'Sierra Leone': [8.4606, -11.7799],
  'Somalia': [5.1521, 46.1996], 'South Africa': [-30.5595, 22.9375], 'South Korea': [35.9078, 127.7669],
  'South Sudan': [6.8770, 31.3070], 'Spain': [40.4637, -3.7492], 'Sri Lanka': [7.8731, 80.7718],
  'Sudan': [12.8628, 30.2176], 'Sweden': [60.1282, 18.6435], 'Switzerland': [46.8182, 8.2275],
  'Syria': [34.8021, 38.9968], 'Taiwan': [23.6978, 120.9605], 'Tanzania': [-6.3690, 34.8888],
  'Thailand': [15.8700, 100.9925], 'Turkey': [38.9637, 35.2433], 'Türkiye': [38.9637, 35.2433],
  'Uganda': [1.3733, 32.2903], 'Ukraine': [48.3794, 31.1656], 'United Arab Emirates': [23.4241, 53.8478],
  'United Kingdom': [55.3781, -3.4360], 'United States': [37.0902, -95.7129],
  'Uruguay': [-32.5228, -55.7658], 'Uzbekistan': [41.3775, 64.5853], 'Venezuela': [6.4238, -66.5897],
  'Vietnam': [14.0583, 108.2772], 'Yemen': [15.5527, 48.5164], 'Zambia': [-13.1339, 27.8493],
  'Zimbabwe': [-19.0154, 29.1549],
}

// Detect which column contains country names by sampling values against the centroid lookup
function findCountryColumn(data: any[], exclude: Set<string>): string | null {
  if (!data || data.length === 0) return null
  const cols = Object.keys(data[0]).filter(c => !exclude.has(c))
  for (const col of cols) {
    const sample = data.slice(0, 30).map(r => String(r[col] ?? ''))
    const hits = sample.filter(v => COUNTRY_CENTROIDS[v] !== undefined).length
    if (hits >= Math.min(3, Math.floor(sample.length * 0.3))) return col
  }
  return null
}

// ─── WKT Parser ──────────────────────────────────────────────────────────────

const WKT_KEYWORDS = ['POINT', 'POLYGON', 'LINESTRING', 'MULTIPOLYGON', 'MULTILINESTRING', 'MULTIPOINT', 'GEOMETRYCOLLECTION']

/** Parse space-separated coordinate pairs from a flat string, e.g. "x1 y1, x2 y2" */
function parseCoordsFromString(s: string): number[][] {
  const result: number[][] = []
  const pairRe = /([-\d.e+]+)\s+([-\d.e+]+)/g
  let m: RegExpExecArray | null
  while ((m = pairRe.exec(s)) !== null) {
    result.push([parseFloat(m[1]), parseFloat(m[2])])
  }
  return result
}

/** Parse ring groups from inside a polygon/multilinestring: "(x y, ...), (x y, ...)" */
function parseRings(s: string): number[][][] {
  const rings: number[][][] = []
  const ringRe = /\(([^()]+)\)/g
  let m: RegExpExecArray | null
  while ((m = ringRe.exec(s)) !== null) {
    rings.push(parseCoordsFromString(m[1]))
  }
  return rings
}

/** Parse the coordinate array for MULTIPOLYGON using a depth-2 state machine */
function parseMultiPolygonCoords(s: string): number[][][][] {
  const body = s.replace(/^MULTIPOLYGON\s*/i, '').trim()
  const polygons: number[][][][] = []
  let depth = 0
  let polyStart = -1
  for (let i = 0; i < body.length; i++) {
    if (body[i] === '(') {
      depth++
      if (depth === 2) polyStart = i
    } else if (body[i] === ')') {
      if (depth === 2 && polyStart >= 0) {
        polygons.push(parseRings(body.slice(polyStart, i + 1)))
        polyStart = -1
      }
      depth--
    }
  }
  return polygons
}

/** Extract all [lng, lat] coordinate pairs from a GeoJSON geometry (for bbox calculations) */
function extractCoordsFromGeometry(geometry: any): number[][] {
  if (!geometry) return []
  switch (geometry.type) {
    case 'Point': return [geometry.coordinates]
    case 'MultiPoint': return geometry.coordinates
    case 'LineString': return geometry.coordinates
    case 'MultiLineString': return (geometry.coordinates as number[][][]).flat()
    case 'Polygon': return (geometry.coordinates as number[][][]).flat()
    case 'MultiPolygon': return (geometry.coordinates as number[][][][]).flat(2)
    default: return []
  }
}

/** Parse a WKT string into a GeoJSON geometry object, or null on failure */
function parseWKT(wkt: string): any | null {
  if (!wkt || typeof wkt !== 'string') return null
  const str = wkt.trim()
  const upper = str.toUpperCase()
  try {
    if (upper.startsWith('POINT')) {
      const m = str.match(/\(\s*([-\d.e+]+)\s+([-\d.e+]+)/)
      if (!m) return null
      return { type: 'Point', coordinates: [parseFloat(m[1]), parseFloat(m[2])] }
    }
    if (upper.startsWith('MULTIPOLYGON')) {
      return { type: 'MultiPolygon', coordinates: parseMultiPolygonCoords(str) }
    }
    if (upper.startsWith('POLYGON')) {
      const body = str.replace(/^POLYGON\s*/i, '').trim()
      return { type: 'Polygon', coordinates: parseRings(body) }
    }
    if (upper.startsWith('MULTILINESTRING')) {
      const body = str.replace(/^MULTILINESTRING\s*/i, '').trim()
      return { type: 'MultiLineString', coordinates: parseRings(body) }
    }
    if (upper.startsWith('LINESTRING')) {
      const inner = str.match(/\(([^)]+)\)/)?.[1]
      if (!inner) return null
      return { type: 'LineString', coordinates: parseCoordsFromString(inner) }
    }
    if (upper.startsWith('MULTIPOINT')) {
      const body = str.replace(/^MULTIPOINT\s*/i, '').trim()
      return { type: 'MultiPoint', coordinates: parseCoordsFromString(body.replace(/[()]/g, ' ')) }
    }
  } catch {
    return null
  }
  return null
}

// ─── Spatial column type ─────────────────────────────────────────────────────

export type SpatialColumns =
  | { lat: string; lng: string; wkt?: undefined }
  | { wkt: string; lat?: undefined; lng?: undefined }

interface InteractiveMapViewProps {
  datasetId: string
  data: any[]
  spatialColumns: SpatialColumns | { lat?: string; lng?: string; wkt?: string }
  config?: any
  onSaveConfig?: (config: any) => void
  chartRows?: any[]
}

interface PopupInfo {
  longitude: number
  latitude: number
  properties: Record<string, any>
}

interface HoverInfo {
  x: number
  y: number
  properties: Record<string, any>
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

const SPATIAL_EXCLUDE = new Set([
  'lat', 'lng', 'latitude', 'longitude', 'LAT', 'LNG', 'LATITUDE', 'LONGITUDE',
  'id', 'ID', 'uuid', 'UUID', 'created_at', 'updated_at',
])

function makeExcludeSet(spatialColumns: { lat?: string; lng?: string; wkt?: string }): Set<string> {
  const cols = [spatialColumns.lat, spatialColumns.lng, spatialColumns.wkt].filter(Boolean) as string[]
  return new Set([...SPATIAL_EXCLUDE, ...cols])
}

function detectCategoryColumn(
  data: any[],
  spatialColumns: { lat?: string; lng?: string; wkt?: string }
): string | null {
  if (!data || data.length === 0) return null
  const exclude = makeExcludeSet(spatialColumns)
  const columns = Object.keys(data[0]).filter(col => !exclude.has(col))

  for (const col of columns) {
    const values = data.map(r => r[col]).filter(v => v !== null && v !== undefined)
    const uniqueValues = new Set(values.map(String))
    if (typeof values[0] === 'string' && uniqueValues.size >= 2 && uniqueValues.size <= 20) {
      return col
    }
  }
  return null
}

function buildCategoryColorExpression(data: any[], col: string): any {
  const uniqueValues = [
    ...new Set(data.map(r => r[col]).filter(v => v != null).map(String))
  ]
  const expr: any[] = ['match', ['get', col]]
  uniqueValues.forEach((val, i) => {
    expr.push(val, CATEGORY_COLORS[i % CATEGORY_COLORS.length])
  })
  expr.push('#6366f1')
  return expr
}

function buildCategoryMap(data: any[], col: string): Record<string, string> {
  const uniqueValues = [
    ...new Set(data.map(r => r[col]).filter(v => v != null).map(String))
  ]
  const map: Record<string, string> = {}
  uniqueValues.forEach((val, i) => { map[val] = CATEGORY_COLORS[i % CATEGORY_COLORS.length] })
  return map
}

// Haversine distance between two lat/lng points in km
function haversineKm(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLng = (lng2 - lng1) * Math.PI / 180
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLng / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

// Deterministic per-row jitter so points don't pile up on the centroid
function indexJitter(index: number, axis: number, scale: number): number {
  return Math.sin(index * 7.3 + axis * 13.1) * scale
}

// ─── GeoJSON builders ─────────────────────────────────────────────────────────

function buildGeojsonFromWkt(data: any[], wktCol: string): any {
  const features = data.map(row => {
    const wktStr = String(row[wktCol] ?? '')
    const geometry = parseWKT(wktStr)
    if (!geometry) return null
    return {
      type: 'Feature' as const,
      geometry,
      properties: { ...row },
    }
  }).filter(Boolean)
  return { type: 'FeatureCollection', features }
}

function buildGeojsonFromLatLng(data: any[], spatialColumns: { lat: string; lng: string }): any {
  const exclude = makeExcludeSet(spatialColumns)
  const countryColumn = findCountryColumn(data, exclude)

  const features = data
    .map((row, index) => {
      const rawLat = parseFloat(row[spatialColumns.lat])
      const rawLng = parseFloat(row[spatialColumns.lng])
      const hasValidCoords =
        !isNaN(rawLat) && !isNaN(rawLng) &&
        rawLat >= -90 && rawLat <= 90 &&
        rawLng >= -180 && rawLng <= 180

      let finalLat: number
      let finalLng: number

      if (hasValidCoords) {
        if (countryColumn) {
          const country = String(row[countryColumn] ?? '')
          const centroid = COUNTRY_CENTROIDS[country]
          if (centroid) {
            const distKm = haversineKm(rawLat, rawLng, centroid[0], centroid[1])
            if (distKm > 3000) {
              finalLat = centroid[0] + indexJitter(index, 0, 1.5)
              finalLng = centroid[1] + indexJitter(index, 1, 3.0)
            } else {
              finalLat = rawLat
              finalLng = rawLng
            }
          } else {
            finalLat = rawLat
            finalLng = rawLng
          }
        } else {
          finalLat = rawLat
          finalLng = rawLng
        }
      } else if (countryColumn) {
        const country = String(row[countryColumn] ?? '')
        const centroid = COUNTRY_CENTROIDS[country]
        if (!centroid) return null
        finalLat = centroid[0] + indexJitter(index, 0, 1.5)
        finalLng = centroid[1] + indexJitter(index, 1, 3.0)
      } else {
        return null
      }

      return {
        type: 'Feature' as const,
        geometry: {
          type: 'Point' as const,
          coordinates: [finalLng, finalLat],
        },
        properties: { ...row },
      }
    })
    .filter(Boolean)

  return { type: 'FeatureCollection', features }
}

function buildGeojson(data: any[], spatialColumns: { lat?: string; lng?: string; wkt?: string }): any {
  if (spatialColumns.wkt) {
    return buildGeojsonFromWkt(data, spatialColumns.wkt)
  }
  if (spatialColumns.lat && spatialColumns.lng) {
    return buildGeojsonFromLatLng(data, { lat: spatialColumns.lat, lng: spatialColumns.lng })
  }
  return { type: 'FeatureCollection', features: [] }
}

function computeInitialViewState(data: any[], spatialColumns: { lat?: string; lng?: string; wkt?: string }) {
  const lats: number[] = []
  const lngs: number[] = []

  if (spatialColumns.wkt) {
    const wktCol = spatialColumns.wkt
    data.forEach(row => {
      const geometry = parseWKT(String(row[wktCol] ?? ''))
      if (!geometry) return
      extractCoordsFromGeometry(geometry).forEach(([lng, lat]) => {
        if (!isNaN(lat) && !isNaN(lng)) {
          lats.push(lat)
          lngs.push(lng)
        }
      })
    })
  } else if (spatialColumns.lat && spatialColumns.lng) {
    const exclude = makeExcludeSet(spatialColumns)
    const countryColumn = findCountryColumn(data, exclude)
    data.forEach((row, index) => {
      let lat = parseFloat(row[spatialColumns.lat!])
      let lng = parseFloat(row[spatialColumns.lng!])
      const hasValidCoords = !isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180

      if (hasValidCoords) {
        if (countryColumn) {
          const country = String(row[countryColumn] ?? '')
          const centroid = COUNTRY_CENTROIDS[country]
          if (centroid && haversineKm(lat, lng, centroid[0], centroid[1]) > 3000) {
            lat = centroid[0] + indexJitter(index, 0, 1.5)
            lng = centroid[1] + indexJitter(index, 1, 3.0)
          }
        }
        lats.push(lat)
        lngs.push(lng)
      } else if (countryColumn) {
        const country = String(row[countryColumn] ?? '')
        const centroid = COUNTRY_CENTROIDS[country]
        if (centroid) {
          lats.push(centroid[0] + indexJitter(index, 0, 1.5))
          lngs.push(centroid[1] + indexJitter(index, 1, 3.0))
        }
      }
    })
  }

  if (lats.length === 0) return { latitude: 0, longitude: 0, zoom: 1 }

  const centerLat = (Math.min(...lats) + Math.max(...lats)) / 2
  const centerLng = (Math.min(...lngs) + Math.max(...lngs)) / 2
  const span = Math.max(Math.max(...lats) - Math.min(...lats), Math.max(...lngs) - Math.min(...lngs))
  const zoom = span < 0.01 ? 14 : span < 0.1 ? 12 : span < 1 ? 9 : span < 10 ? 6 : span < 50 ? 4 : 2

  return { latitude: centerLat, longitude: centerLng, zoom }
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'number') {
    return Number.isInteger(value) ? value.toLocaleString() : (value as number).toFixed(2)
  }
  return String(value)
}

function getTitleField(
  properties: Record<string, any>,
  spatialColumns: { lat?: string; lng?: string; wkt?: string }
): string {
  const exclude = makeExcludeSet(spatialColumns)
  const stringEntry = Object.entries(properties).find(
    ([k, v]) => !exclude.has(k) && typeof v === 'string' && (v as string).length > 0
  )
  if (stringEntry) return String(stringEntry[1])
  const anyEntry = Object.entries(properties).find(([k]) => !exclude.has(k))
  return anyEntry ? formatValue(anyEntry[1]) : 'Feature'
}

function getPreviewFields(
  properties: Record<string, any>,
  spatialColumns: { lat?: string; lng?: string; wkt?: string },
  limit = 3
): Array<{ key: string; value: string }> {
  const exclude = makeExcludeSet(spatialColumns)
  return Object.entries(properties)
    .filter(([k]) => !exclude.has(k))
    .slice(0, limit)
    .map(([k, v]) => ({ key: k, value: formatValue(v) }))
}

// ─── Component ────────────────────────────────────────────────────────────────

const LAT_PATTERNS = ['lat', 'latitude']
const LNG_PATTERNS = ['lng', 'lon', 'longitude', 'long']

function detectSpatialColumnsFromData(data: any[]): { lat?: string; lng?: string; wkt?: string } | null {
  if (!data.length) return null
  const cols = Object.keys(data[0])

  // First: check for lat/lng columns
  const latCol = cols.find(c => LAT_PATTERNS.includes(c.toLowerCase()))
  const lngCol = cols.find(c => LNG_PATTERNS.some(p => c.toLowerCase() === p))
  if (latCol && lngCol) return { lat: latCol, lng: lngCol }

  // Second: check for WKT geometry columns by sampling values
  for (const col of cols) {
    const sampleValues = data.slice(0, 5).map(r => String(r[col] ?? '')).filter(Boolean)
    const isWkt = sampleValues.some(v => WKT_KEYWORDS.some(kw => v.trim().toUpperCase().startsWith(kw)))
    if (isWkt) return { wkt: col }
  }

  return null
}

export function InteractiveMapView({
  datasetId,
  data,
  spatialColumns: spatialColumnsProp,
  chartRows,
}: InteractiveMapViewProps) {
  const mapRef = useRef<MapRef>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const MAPBOX_TOKEN: string = (import.meta as any).env?.VITE_MAPBOX_TOKEN ?? ''

  // If the prop-specified columns don't actually exist in the data (e.g. dataset uses
  // a WKT "Geolocation" column but the NL query extracted lat/lng as computed columns),
  // auto-detect from the real column names present in the data.
  const spatialColumns = useMemo(() => {
    if (!data.length) return spatialColumnsProp as { lat?: string; lng?: string; wkt?: string }
    const first = data[0]

    // WKT prop: check the wkt column actually exists in data
    if (spatialColumnsProp?.wkt) {
      if (spatialColumnsProp.wkt in first) return spatialColumnsProp as { wkt: string }
    }

    // Lat/lng prop: check both columns exist in data
    if (spatialColumnsProp?.lat && spatialColumnsProp?.lng) {
      const propLatExists = spatialColumnsProp.lat in first
      const propLngExists = spatialColumnsProp.lng in first
      if (propLatExists && propLngExists) return spatialColumnsProp as { lat: string; lng: string }
    }

    // Fall back to auto-detection from actual column names/values
    return detectSpatialColumnsFromData(data) ?? spatialColumnsProp as { lat?: string; lng?: string; wkt?: string }
  }, [data, spatialColumnsProp])

  // Whether we're in WKT mode (affects clustering and layer setup)
  const isWktMode = !!spatialColumns?.wkt

  const [popupInfo, setPopupInfo] = useState<PopupInfo | null>(null)
  const [hoverInfo, setHoverInfo] = useState<HoverInfo | null>(null)
  const [showListPanel, setShowListPanel] = useState(false)
  const [showStatsPanel, setShowStatsPanel] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [chartOverlayClosed, setChartOverlayClosed] = useState(false)

  // Reset chart overlay visibility when a new query result arrives
  useEffect(() => {
    if (chartRows && chartRows.length > 0) {
      setChartOverlayClosed(false)
    }
  }, [chartRows])

  // Skip fitBounds on initial mount — only fly when data changes from a query result
  const isInitialized = useRef(false)

  useEffect(() => {
    if (!isInitialized.current) {
      isInitialized.current = true
      return
    }

    let lats: number[] = []
    let lngs: number[] = []

    if (spatialColumns?.wkt) {
      const wktCol = spatialColumns.wkt
      data.forEach(row => {
        const geometry = parseWKT(String(row[wktCol] ?? ''))
        if (!geometry) return
        extractCoordsFromGeometry(geometry).forEach(([lng, lat]) => {
          if (!isNaN(lat) && !isNaN(lng)) { lats.push(lat); lngs.push(lng) }
        })
      })
    } else if (spatialColumns?.lat && spatialColumns?.lng) {
      const exclude = makeExcludeSet(spatialColumns)
      const cc = findCountryColumn(data, exclude)
      lats = []
      lngs = []
      data.forEach((r, idx) => {
        let lat = parseFloat(r[spatialColumns.lat!])
        let lng = parseFloat(r[spatialColumns.lng!])
        const ok = !isNaN(lat) && !isNaN(lng) && lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180
        if (ok && cc) {
          const centroid = COUNTRY_CENTROIDS[String(r[cc] ?? '')]
          if (centroid && haversineKm(lat, lng, centroid[0], centroid[1]) > 3000) {
            lat = centroid[0] + indexJitter(idx, 0, 1.5)
            lng = centroid[1] + indexJitter(idx, 1, 3.0)
          }
        } else if (!ok && cc) {
          const centroid = COUNTRY_CENTROIDS[String(r[cc] ?? '')]
          if (centroid) { lat = centroid[0]; lng = centroid[1] } else return
        } else if (!ok) {
          return
        }
        lats.push(lat)
        lngs.push(lng)
      })
    }

    if (lats.length === 0) return

    const minLat = Math.min(...lats)
    const maxLat = Math.max(...lats)
    const minLng = Math.min(...lngs)
    const maxLng = Math.max(...lngs)

    // Small delay so the Mapbox source has time to ingest the new data
    const timer = setTimeout(() => {
      mapRef.current?.getMap()?.fitBounds(
        [[minLng, minLat], [maxLng, maxLat]],
        { padding: 60, maxZoom: 12, duration: 800 }
      )
    }, 150)
    return () => clearTimeout(timer)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data])

  const categoryColumn = useMemo(
    () => detectCategoryColumn(data, spatialColumns ?? {}),
    [data, spatialColumns]
  )

  const categoryColorMap = useMemo(
    () => (categoryColumn ? buildCategoryMap(data, categoryColumn) : {}),
    [data, categoryColumn]
  )

  const categoryColorExpression = useMemo(
    () => categoryColumn ? buildCategoryColorExpression(data, categoryColumn) : '#6366f1',
    [data, categoryColumn]
  )

  const initialViewState = useMemo(
    () => computeInitialViewState(data, spatialColumns ?? {}),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [data.length, spatialColumns?.lat, spatialColumns?.lng, spatialColumns?.wkt]
  )

  const filteredData = useMemo(() => {
    if (!searchQuery.trim()) return data
    const q = searchQuery.toLowerCase()
    return data.filter(row =>
      Object.values(row).some(v => String(v ?? '').toLowerCase().includes(q))
    )
  }, [data, searchQuery])

  const geojson = useMemo(
    () => buildGeojson(filteredData, spatialColumns ?? {}),
    [filteredData, spatialColumns]
  )

  // ─── Map interactions ───────────────────────────────────────────────────────

  // Layers that respond to clicks/hover
  const interactiveLayerIds = isWktMode
    ? ['wkt-polygon-fill', 'wkt-line', 'wkt-point']
    : ['clusters', 'unclustered-point']

  const handleClick = useCallback((event: MapLayerMouseEvent) => {
    const features = (event as any).features as Array<{ layer?: { id?: string }; properties?: any; geometry?: any }> | undefined
    if (!features || features.length === 0) { setPopupInfo(null); return }

    const feature = features[0]

    if (feature.layer?.id === 'clusters') {
      const clusterId = feature.properties?.cluster_id
      if (clusterId == null) return
      const map = mapRef.current?.getMap()
      if (!map) return
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const source = map.getSource('points') as any
      source.getClusterExpansionZoom(clusterId, (err: Error | null, zoom: number) => {
        if (err) return
        const coords = feature.geometry?.coordinates as [number, number]
        map.easeTo({ center: coords, zoom: zoom + 0.5, duration: 500 })
      })
      setPopupInfo(null)
    } else if (
      feature.layer?.id === 'unclustered-point' ||
      feature.layer?.id === 'wkt-point'
    ) {
      const coords = feature.geometry?.coordinates as [number, number]
      setPopupInfo({ longitude: coords[0], latitude: coords[1], properties: feature.properties ?? {} })
    } else if (
      feature.layer?.id === 'wkt-polygon-fill' ||
      feature.layer?.id === 'wkt-line'
    ) {
      // Use the click position for the popup
      setPopupInfo({
        longitude: event.lngLat.lng,
        latitude: event.lngLat.lat,
        properties: feature.properties ?? {},
      })
    }
  }, [])

  const handleMouseMove = useCallback((event: MapLayerMouseEvent) => {
    const features = (event as any).features as Array<{ layer?: { id?: string }; properties?: any }> | undefined
    const interactiveLayers = new Set(['unclustered-point', 'wkt-point', 'wkt-polygon-fill', 'wkt-line'])
    const pts = features?.filter(f => f.layer?.id && interactiveLayers.has(f.layer.id))
    if (pts && pts.length > 0) {
      setHoverInfo({ x: event.point.x, y: event.point.y, properties: pts[0].properties ?? {} })
    } else {
      setHoverInfo(null)
    }
  }, [])

  const handleMouseLeave = useCallback(() => { setHoverInfo(null) }, [])

  const flyToPoint = useCallback((row: any) => {
    if (!spatialColumns?.lat || !spatialColumns?.lng) return
    const lat = parseFloat(row[spatialColumns.lat])
    const lng = parseFloat(row[spatialColumns.lng])
    if (isNaN(lat) || isNaN(lng)) return
    mapRef.current?.getMap()?.easeTo({ center: [lng, lat], zoom: 14, duration: 600 })
    setPopupInfo({ longitude: lng, latitude: lat, properties: { ...row } })
    setShowListPanel(false)
  }, [spatialColumns])

  // ─── Empty states ───────────────────────────────────────────────────────────

  if (!MAPBOX_TOKEN) {
    return (
      <div className="h-full flex items-center justify-center bg-muted/20">
        <div className="text-center p-6 max-w-md">
          <h3 className="text-lg font-semibold text-foreground mb-2">Mapbox Token Required</h3>
          <p className="text-muted-foreground mb-4">
            Add a Mapbox access token to your environment variables to use map visualization.
          </p>
          <code className="block bg-muted p-3 rounded-lg text-sm text-left font-mono">
            VITE_MAPBOX_TOKEN=your_token_here
          </code>
        </div>
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-muted/20">
        <p className="text-muted-foreground">No data to display on map</p>
      </div>
    )
  }

  const pointCount = geojson.features.length
  const titleField = popupInfo ? getTitleField(popupInfo.properties, spatialColumns ?? {}) : ''

  // ─── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="relative h-full w-full overflow-hidden">
      <Map
        ref={mapRef}
        initialViewState={initialViewState}
        mapboxAccessToken={MAPBOX_TOKEN}
        mapStyle="mapbox://styles/mapbox/light-v11"
        style={{ width: '100%', height: '100%' }}
        interactiveLayerIds={interactiveLayerIds}
        onClick={handleClick as any}
        onMouseMove={handleMouseMove as any}
        onMouseLeave={handleMouseLeave}
        cursor={hoverInfo ? 'pointer' : 'grab'}
      >
        <NavigationControl position="bottom-right" />

        {isWktMode ? (
          /* ── WKT geometry source (no clustering) ── */
          <Source
            id="wkt-features"
            type="geojson"
            data={geojson}
          >
            {/* Polygon fill */}
            <Layer
              id="wkt-polygon-fill"
              type="fill"
              filter={['match', ['geometry-type'], ['Polygon', 'MultiPolygon'], true, false] as any}
              paint={{
                'fill-color': categoryColorExpression,
                'fill-opacity': 0.45,
              }}
            />
            {/* Polygon stroke */}
            <Layer
              id="wkt-polygon-outline"
              type="line"
              filter={['match', ['geometry-type'], ['Polygon', 'MultiPolygon'], true, false] as any}
              paint={{
                'line-color': categoryColorExpression,
                'line-width': 1.5,
                'line-opacity': 0.9,
              }}
            />
            {/* Lines */}
            <Layer
              id="wkt-line"
              type="line"
              filter={['match', ['geometry-type'], ['LineString', 'MultiLineString'], true, false] as any}
              paint={{
                'line-color': categoryColorExpression,
                'line-width': 2.5,
                'line-opacity': 0.9,
              }}
            />
            {/* Points */}
            <Layer
              id="wkt-point"
              type="circle"
              filter={['match', ['geometry-type'], ['Point', 'MultiPoint'], true, false] as any}
              paint={{
                'circle-color': categoryColorExpression,
                'circle-radius': ['interpolate', ['linear'], ['zoom'], 8, 5, 14, 10] as any,
                'circle-stroke-width': 2,
                'circle-stroke-color': '#fff',
                'circle-opacity': 0.9,
              }}
            />
          </Source>
        ) : (
          /* ── Lat/lng point source (with clustering) ── */
          <Source
            id="points"
            type="geojson"
            data={geojson}
            cluster={true}
            clusterMaxZoom={14}
            clusterRadius={50}
          >
            {/* Cluster bubbles */}
            <Layer
              id="clusters"
              type="circle"
              filter={['has', 'point_count']}
              paint={{
                'circle-color': [
                  'step', ['get', 'point_count'],
                  '#6366f1', 10, '#3b82f6', 100, '#0ea5e9',
                ] as any,
                'circle-radius': [
                  'step', ['get', 'point_count'],
                  20, 10, 30, 100, 40,
                ] as any,
                'circle-stroke-width': 3,
                'circle-stroke-color': '#fff',
                'circle-opacity': 0.9,
              }}
            />

            {/* Cluster count labels */}
            <Layer
              id="cluster-count"
              type="symbol"
              filter={['has', 'point_count']}
              layout={{
                'text-field': '{point_count_abbreviated}',
                'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
                'text-size': 13,
              }}
              paint={{ 'text-color': '#fff' }}
            />

            {/* Individual points — colored by detected category */}
            <Layer
              id="unclustered-point"
              type="circle"
              filter={['!', ['has', 'point_count']]}
              paint={{
                'circle-color': categoryColorExpression,
                'circle-radius': ['interpolate', ['linear'], ['zoom'], 8, 5, 14, 10] as any,
                'circle-stroke-width': 2,
                'circle-stroke-color': '#fff',
                'circle-opacity': 0.9,
              }}
            />
          </Source>
        )}

        {/* Click popup — Foursquare-style data card */}
        {popupInfo && (
          <Popup
            longitude={popupInfo.longitude}
            latitude={popupInfo.latitude}
            onClose={() => setPopupInfo(null)}
            closeButton={true}
            closeOnClick={false}
            anchor="bottom"
          >
            <div className="min-w-[220px] max-w-[280px] max-h-64 overflow-y-auto">
              <div className="flex items-center gap-2 mb-3 pb-2 border-b border-gray-100">
                <div
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{
                    backgroundColor: categoryColumn && popupInfo.properties[categoryColumn]
                      ? (categoryColorMap[String(popupInfo.properties[categoryColumn])] ?? '#6366f1')
                      : '#6366f1'
                  }}
                />
                <span className="font-semibold text-gray-900 text-sm leading-tight truncate">
                  {titleField}
                </span>
              </div>
              <div className="space-y-1.5">
                {Object.entries(popupInfo.properties)
                  .filter(([k]) => !makeExcludeSet(spatialColumns ?? {}).has(k))
                  .map(([k, v]) => (
                    <div key={k} className="flex justify-between gap-2 text-xs">
                      <span className="text-gray-500 font-medium capitalize flex-shrink-0">
                        {k.replace(/_/g, ' ')}
                      </span>
                      <span className="text-gray-900 font-medium text-right truncate max-w-[150px]">
                        {formatValue(v)}
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          </Popup>
        )}
      </Map>

      {/* ── Search bar overlay (top-left) ── */}
      <div className="absolute top-3 left-3 z-10">
        <div className="relative flex items-center">
          <Search className="absolute left-3 h-4 w-4 text-muted-foreground pointer-events-none" />
          <input
            type="text"
            placeholder="Search locations…"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="pl-9 pr-8 py-2 rounded-xl border border-border bg-card/90 backdrop-blur-sm text-sm shadow-md
                       text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 w-52"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
        {searchQuery && (
          <div className="mt-1 text-xs text-muted-foreground bg-card/80 backdrop-blur rounded-lg px-2 py-1 shadow">
            {pointCount} result{pointCount !== 1 ? 's' : ''}
          </div>
        )}
      </div>

      {/* ── Panel toggles (top-right) ── */}
      <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5">
        <button
          onClick={() => { setShowListPanel(false); setShowStatsPanel(p => !p) }}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium shadow-md border
                      transition-colors backdrop-blur-sm
                      ${showStatsPanel
                        ? 'bg-primary text-primary-foreground border-primary'
                        : 'bg-card/90 text-foreground border-border hover:bg-accent'
                      }`}
          title="Toggle stats panel"
        >
          <BarChart2 className="h-4 w-4" />
          <span className="hidden sm:inline">Stats</span>
        </button>
        <button
          onClick={() => { setShowStatsPanel(false); setShowListPanel(p => !p) }}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium shadow-md border
                      transition-colors backdrop-blur-sm
                      ${showListPanel
                        ? 'bg-primary text-primary-foreground border-primary'
                        : 'bg-card/90 text-foreground border-border hover:bg-accent'
                      }`}
          title="Toggle list view"
        >
          <List className="h-4 w-4" />
          <span className="hidden sm:inline">List</span>
        </button>
        {isWktMode && (
          <div className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium shadow-md border
                          bg-card/90 text-muted-foreground border-border"
            title="WKT geometry mode"
          >
            <Globe className="h-4 w-4" />
            <span className="hidden sm:inline">Geometry</span>
          </div>
        )}
      </div>

      {/* ── Hover tooltip ── */}
      {hoverInfo && (
        <div
          className="absolute z-20 pointer-events-none"
          style={{ left: hoverInfo.x + 12, top: hoverInfo.y - 8 }}
        >
          <div className="bg-card/95 backdrop-blur border border-border rounded-lg shadow-lg px-3 py-2 text-xs max-w-[200px]">
            <div className="font-semibold text-foreground truncate">
              {getTitleField(hoverInfo.properties, spatialColumns ?? {})}
            </div>
            {getPreviewFields(hoverInfo.properties, spatialColumns ?? {}, 2).map(({ key, value }) => (
              <div key={key} className="flex gap-1 text-muted-foreground mt-0.5">
                <span className="capitalize">{key.replace(/_/g, ' ')}:</span>
                <span className="font-medium text-foreground truncate">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Category legend (bottom-left) ── */}
      {categoryColumn && Object.keys(categoryColorMap).length > 0 && (
        <div className="absolute bottom-20 left-3 z-10">
          <div className="bg-card/85 backdrop-blur border border-border rounded-xl shadow-md px-3 py-2">
            <div className="text-xs font-semibold text-muted-foreground mb-1.5 capitalize">
              {categoryColumn.replace(/_/g, ' ')}
            </div>
            <div className="space-y-1">
              {Object.entries(categoryColorMap).slice(0, 12).map(([label, color]) => (
                <div key={label} className="flex items-center gap-2 text-xs">
                  <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                  <span className="text-foreground truncate max-w-[120px]">{label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── Stats panel ── */}
      {showStatsPanel && datasetId && (
        <MapStatsPanel
          datasetId={datasetId}
          data={data}
          spatialColumns={spatialColumns ?? {}}
          onClose={() => setShowStatsPanel(false)}
        />
      )}

      {/* ── Query result chart overlay ── */}
      {chartRows && chartRows.length > 0 && !chartOverlayClosed && (
        <MapChartOverlay
          rows={chartRows}
          totalRows={chartRows.length}
          spatialColumns={spatialColumns ?? {}}
          onClose={() => setChartOverlayClosed(true)}
        />
      )}

      {/* ── Side list panel ── */}
      {showListPanel && (
        <div className="absolute right-0 top-0 h-full w-72 bg-card border-l border-border z-10 flex flex-col shadow-xl">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border flex-shrink-0">
            <div className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-primary" />
              <span className="font-semibold text-foreground text-sm">
                {pointCount.toLocaleString()} feature{pointCount !== 1 ? 's' : ''}
              </span>
            </div>
            <button onClick={() => setShowListPanel(false)} className="text-muted-foreground hover:text-foreground">
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto">
            {filteredData.slice(0, 500).map((row, index) => {
              const hasLatLng = !!(spatialColumns?.lat && spatialColumns?.lng)
              const lat = hasLatLng ? parseFloat(row[spatialColumns!.lat!]) : NaN
              const lng = hasLatLng ? parseFloat(row[spatialColumns!.lng!]) : NaN
              const isValid = hasLatLng && !isNaN(lat) && !isNaN(lng)
              const catValue = categoryColumn ? String(row[categoryColumn] ?? '') : ''
              const dotColor = categoryColumn && catValue
                ? (categoryColorMap[catValue] ?? '#6366f1')
                : '#6366f1'

              return (
                <button
                  key={index}
                  onClick={() => isValid && flyToPoint(row)}
                  disabled={!isValid}
                  className="w-full text-left px-4 py-3 border-b border-border/50 hover:bg-accent transition-colors
                             disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <div className="flex items-start gap-2.5">
                    <div
                      className="w-2.5 h-2.5 rounded-full flex-shrink-0 mt-1"
                      style={{ backgroundColor: dotColor }}
                    />
                    <div className="min-w-0 flex-1">
                      <div className="font-medium text-sm text-foreground truncate">
                        {getTitleField(row, spatialColumns ?? {})}
                      </div>
                      {getPreviewFields(row, spatialColumns ?? {}, 2).map(({ key, value }) => (
                        <div key={key} className="text-xs text-muted-foreground truncate">
                          {key.replace(/_/g, ' ')}: {value}
                        </div>
                      ))}
                    </div>
                  </div>
                </button>
              )
            })}

            {filteredData.length > 500 && (
              <div className="px-4 py-3 text-xs text-muted-foreground text-center">
                Showing first 500 of {filteredData.length.toLocaleString()} features
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
