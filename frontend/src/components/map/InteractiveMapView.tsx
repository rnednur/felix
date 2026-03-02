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

// US State centroids — full names and 2-letter abbreviations
const US_STATE_CENTROIDS: Record<string, [number, number]> = {
  'Alabama': [32.806671, -86.791130], 'Alaska': [61.370716, -152.404419],
  'Arizona': [33.729759, -111.431221], 'Arkansas': [34.969704, -92.373123],
  'California': [36.116203, -119.681564], 'Colorado': [39.059811, -105.311104],
  'Connecticut': [41.597782, -72.755371], 'Delaware': [39.318523, -75.507141],
  'Florida': [27.766279, -81.686783], 'Georgia': [33.040619, -83.643074],
  'Hawaii': [21.094318, -157.498337], 'Idaho': [44.240459, -114.478828],
  'Illinois': [40.349457, -88.986137], 'Indiana': [39.849426, -86.258278],
  'Iowa': [42.011539, -93.210526], 'Kansas': [38.526600, -96.726486],
  'Kentucky': [37.668140, -84.670067], 'Louisiana': [31.169960, -91.867805],
  'Maine': [44.693947, -69.381927], 'Maryland': [39.063946, -76.802101],
  'Massachusetts': [42.230171, -71.530106], 'Michigan': [43.326618, -84.536095],
  'Minnesota': [45.694454, -93.900192], 'Mississippi': [32.741646, -89.678696],
  'Missouri': [38.456085, -92.288368], 'Montana': [46.921925, -110.454353],
  'Nebraska': [41.125370, -98.268082], 'Nevada': [38.313515, -117.055374],
  'New Hampshire': [43.452492, -71.563896], 'New Jersey': [40.298904, -74.521011],
  'New Mexico': [34.840515, -106.248482], 'New York': [42.165726, -74.948051],
  'North Carolina': [35.630066, -79.806419], 'North Dakota': [47.528912, -99.784012],
  'Ohio': [40.388783, -82.764915], 'Oklahoma': [35.565342, -96.928917],
  'Oregon': [44.572021, -122.070938], 'Pennsylvania': [40.590752, -77.209755],
  'Rhode Island': [41.680893, -71.511780], 'South Carolina': [33.856892, -80.945007],
  'South Dakota': [44.299782, -99.438828], 'Tennessee': [35.747845, -86.692345],
  'Texas': [31.054487, -97.563461], 'Utah': [40.150032, -111.862434],
  'Vermont': [44.045876, -72.710686], 'Virginia': [37.769337, -78.169968],
  'Washington': [47.400902, -121.490494], 'West Virginia': [38.491226, -80.954453],
  'Wisconsin': [44.268543, -89.616508], 'Wyoming': [42.755966, -107.302490],
  'District of Columbia': [38.897438, -77.026817],
}
// Abbreviation aliases
const US_STATE_ABBREVS: Record<string, string> = {
  'AL':'Alabama','AK':'Alaska','AZ':'Arizona','AR':'Arkansas','CA':'California',
  'CO':'Colorado','CT':'Connecticut','DE':'Delaware','FL':'Florida','GA':'Georgia',
  'HI':'Hawaii','ID':'Idaho','IL':'Illinois','IN':'Indiana','IA':'Iowa',
  'KS':'Kansas','KY':'Kentucky','LA':'Louisiana','ME':'Maine','MD':'Maryland',
  'MA':'Massachusetts','MI':'Michigan','MN':'Minnesota','MS':'Mississippi',
  'MO':'Missouri','MT':'Montana','NE':'Nebraska','NV':'Nevada','NH':'New Hampshire',
  'NJ':'New Jersey','NM':'New Mexico','NY':'New York','NC':'North Carolina',
  'ND':'North Dakota','OH':'Ohio','OK':'Oklahoma','OR':'Oregon','PA':'Pennsylvania',
  'RI':'Rhode Island','SC':'South Carolina','SD':'South Dakota','TN':'Tennessee',
  'TX':'Texas','UT':'Utah','VT':'Vermont','VA':'Virginia','WA':'Washington',
  'WV':'West Virginia','WI':'Wisconsin','WY':'Wyoming','DC':'District of Columbia',
}
function lookupStateCentroid(name: string): [number, number] | undefined {
  return US_STATE_CENTROIDS[name] ?? US_STATE_CENTROIDS[US_STATE_ABBREVS[name] ?? '']
}

// Major world city centroids (~150 cities across all continents)
const CITY_CENTROIDS: Record<string, [number, number]> = {
  // North America
  'New York': [40.7128, -74.0060], 'Los Angeles': [34.0522, -118.2437],
  'Chicago': [41.8781, -87.6298], 'Houston': [29.7604, -95.3698],
  'Phoenix': [33.4484, -112.0740], 'Philadelphia': [39.9526, -75.1652],
  'San Antonio': [29.4241, -98.4936], 'San Diego': [32.7157, -117.1611],
  'Dallas': [32.7767, -96.7970], 'San Jose': [37.3382, -121.8863],
  'Austin': [30.2672, -97.7431], 'Jacksonville': [30.3322, -81.6557],
  'San Francisco': [37.7749, -122.4194], 'Seattle': [47.6062, -122.3321],
  'Denver': [39.7392, -104.9903], 'Washington': [38.9072, -77.0369],
  'Nashville': [36.1627, -86.7816], 'Boston': [42.3601, -71.0589],
  'Portland': [45.5051, -122.6750], 'Atlanta': [33.7490, -84.3880],
  'Miami': [25.7617, -80.1918], 'Minneapolis': [44.9778, -93.2650],
  'Toronto': [43.6532, -79.3832], 'Montreal': [45.5017, -73.5673],
  'Vancouver': [49.2827, -123.1207], 'Calgary': [51.0447, -114.0719],
  'Mexico City': [19.4326, -99.1332], 'Guadalajara': [20.6597, -103.3496],
  'Monterrey': [25.6866, -100.3161],
  // South America
  'São Paulo': [-23.5505, -46.6333], 'Rio de Janeiro': [-22.9068, -43.1729],
  'Buenos Aires': [-34.6037, -58.3816], 'Lima': [-12.0464, -77.0428],
  'Bogotá': [4.7110, -74.0721], 'Santiago': [-33.4489, -70.6693],
  'Caracas': [10.4806, -66.9036], 'Quito': [-0.1807, -78.4678],
  'La Paz': [-16.5000, -68.1500],
  // Europe
  'London': [51.5074, -0.1278], 'Paris': [48.8566, 2.3522],
  'Berlin': [52.5200, 13.4050], 'Madrid': [40.4168, -3.7038],
  'Rome': [41.9028, 12.4964], 'Vienna': [48.2082, 16.3738],
  'Amsterdam': [52.3676, 4.9041], 'Brussels': [50.8503, 4.3517],
  'Stockholm': [59.3293, 18.0686], 'Oslo': [59.9139, 10.7522],
  'Copenhagen': [55.6761, 12.5683], 'Helsinki': [60.1699, 24.9384],
  'Warsaw': [52.2297, 21.0122], 'Prague': [50.0755, 14.4378],
  'Budapest': [47.4979, 19.0402], 'Bucharest': [44.4268, 26.1025],
  'Athens': [37.9838, 23.7275], 'Lisbon': [38.7169, -9.1399],
  'Zurich': [47.3769, 8.5417], 'Dublin': [53.3498, -6.2603],
  'Munich': [48.1351, 11.5820], 'Milan': [45.4654, 9.1859],
  'Barcelona': [41.3851, 2.1734], 'Kyiv': [50.4501, 30.5234],
  'Moscow': [55.7558, 37.6176], 'Saint Petersburg': [59.9343, 30.3351],
  'Istanbul': [41.0082, 28.9784], 'Minsk': [53.9045, 27.5615],
  // Africa
  'Cairo': [30.0444, 31.2357], 'Lagos': [6.5244, 3.3792],
  'Kinshasa': [-4.4419, 15.2663], 'Johannesburg': [-26.2041, 28.0473],
  'Cape Town': [-33.9249, 18.4241], 'Nairobi': [-1.2921, 36.8219],
  'Addis Ababa': [9.0320, 38.7421], 'Dar es Salaam': [-6.7924, 39.2083],
  'Casablanca': [33.5731, -7.5898], 'Accra': [5.6037, -0.1870],
  'Dakar': [14.7167, -17.4677], 'Tunis': [36.8190, 10.1658],
  'Algiers': [36.7372, 3.0869], 'Khartoum': [15.5007, 32.5599],
  // Asia
  'Tokyo': [35.6762, 139.6503], 'Shanghai': [31.2304, 121.4737],
  'Beijing': [39.9042, 116.4074], 'Delhi': [28.7041, 77.1025],
  'Mumbai': [19.0760, 72.8777], 'Dhaka': [23.8103, 90.4125],
  'Karachi': [24.8607, 67.0011], 'Bangkok': [13.7563, 100.5018],
  'Jakarta': [-6.2088, 106.8456], 'Manila': [14.5995, 120.9842],
  'Seoul': [37.5665, 126.9780], 'Osaka': [34.6937, 135.5023],
  'Taipei': [25.0330, 121.5654], 'Kuala Lumpur': [3.1390, 101.6869],
  'Singapore': [1.3521, 103.8198], 'Ho Chi Minh City': [10.8231, 106.6297],
  'Hanoi': [21.0278, 105.8342], 'Phnom Penh': [11.5564, 104.9282],
  'Yangon': [16.8661, 96.1951], 'Kolkata': [22.5726, 88.3639],
  'Chennai': [13.0827, 80.2707], 'Bangalore': [12.9716, 77.5946],
  'Lahore': [31.5204, 74.3587], 'Colombo': [6.9271, 79.8612],
  'Tehran': [35.6892, 51.3890], 'Baghdad': [33.3152, 44.3661],
  'Riyadh': [24.7136, 46.6753], 'Jeddah': [21.2854, 39.2376],
  'Amman': [31.9454, 35.9284], 'Beirut': [33.8938, 35.5018],
  'Tel Aviv': [32.0853, 34.7818], 'Dubai': [25.2048, 55.2708],
  'Abu Dhabi': [24.4539, 54.3773], 'Doha': [25.2854, 51.5310],
  'Kabul': [34.5553, 69.2075], 'Islamabad': [33.7294, 73.0931],
  'Kathmandu': [27.7172, 85.3240], 'Ulaanbaatar': [47.8864, 106.9057],
  'Tashkent': [41.2995, 69.2401], 'Almaty': [43.2220, 76.8512],
  // Oceania
  'Sydney': [-33.8688, 151.2093], 'Melbourne': [-37.8136, 144.9631],
  'Brisbane': [-27.4698, 153.0251], 'Perth': [-31.9505, 115.8605],
  'Auckland': [-36.8485, 174.7633], 'Wellington': [-41.2866, 174.7756],
}

// ─── GeoJSON boundary cache ───────────────────────────────────────────────────

let _countriesGeoJSON: any = null
let _usStatesGeoJSON: any = null

async function fetchCountriesGeoJSON(): Promise<any> {
  if (_countriesGeoJSON) return _countriesGeoJSON
  const r = await fetch('https://cdn.jsdelivr.net/gh/holtzy/D3-graph-gallery@master/DATA/world.geojson')
  if (!r.ok) throw new Error(`Countries GeoJSON fetch failed: ${r.status}`)
  _countriesGeoJSON = await r.json()
  return _countriesGeoJSON
}

async function fetchUSStatesGeoJSON(): Promise<any> {
  if (_usStatesGeoJSON) return _usStatesGeoJSON
  const r = await fetch('https://cdn.jsdelivr.net/gh/PublicaMundi/MappingAPI@master/data/geojson/us-states.json')
  if (!r.ok) throw new Error(`US States GeoJSON fetch failed: ${r.status}`)
  _usStatesGeoJSON = await r.json()
  return _usStatesGeoJSON
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
  | { lat: string; lng: string; wkt?: undefined; country?: undefined; state?: undefined; city?: undefined }
  | { wkt: string; lat?: undefined; lng?: undefined; country?: undefined; state?: undefined; city?: undefined }
  | { country: string; lat?: undefined; lng?: undefined; wkt?: undefined; state?: undefined; city?: undefined }
  | { state: string; lat?: undefined; lng?: undefined; wkt?: undefined; country?: undefined; city?: undefined }
  | { city: string; lat?: undefined; lng?: undefined; wkt?: undefined; country?: undefined; state?: undefined }

interface InteractiveMapViewProps {
  datasetId: string
  data: any[]
  spatialColumns: SpatialColumns | { lat?: string; lng?: string; wkt?: string; country?: string; state?: string; city?: string }
  config?: any
  onSaveConfig?: (config: any) => void
  chartRows?: any[]
  chartQueryId?: string  // query_id for AI chart suggestions in the map overlay
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

function makeExcludeSet(spatialColumns: { lat?: string; lng?: string; wkt?: string; country?: string; state?: string; city?: string }): Set<string> {
  const cols = [spatialColumns.lat, spatialColumns.lng, spatialColumns.wkt, spatialColumns.country, spatialColumns.state, spatialColumns.city].filter(Boolean) as string[]
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

function buildGeojsonFromCity(data: any[], cityCol: string): any {
  const features = data.map((row, i) => {
    const city = String(row[cityCol] ?? '').trim()
    const centroid = CITY_CENTROIDS[city]
    if (!centroid) return null
    return {
      type: 'Feature' as const,
      geometry: {
        type: 'Point' as const,
        coordinates: [centroid[1] + indexJitter(i, 1, 0.05), centroid[0] + indexJitter(i, 0, 0.05)],
      },
      properties: { ...row },
    }
  }).filter(Boolean)
  return { type: 'FeatureCollection', features }
}

function detectValueColumn(data: any[], excludeCols: Set<string>): string | null {
  if (!data.length) return null
  const first = data[0]
  return Object.keys(first).find(c => !excludeCols.has(c) && typeof first[c] === 'number') ?? null
}

function buildChoroplethGeojson(
  boundaryGeoJSON: any,
  data: any[],
  dataNameCol: string,
  geoNameProp: string,
  valueCol: string | null,
): { geojson: any; minVal: number; maxVal: number; valueColName: string } {
  // Build lookup: normalised lowercase name → summed value (or row count)
  const lookup: Record<string, number> = {}
  data.forEach(row => {
    const name = String(row[dataNameCol] ?? '').trim().toLowerCase()
    if (!name) return
    const val = valueCol != null ? (parseFloat(String(row[valueCol])) || 0) : 1
    lookup[name] = (lookup[name] ?? 0) + val
  })

  const vals = Object.values(lookup).filter(v => v > 0)
  const minVal = vals.length ? Math.min(...vals) : 0
  const maxVal = vals.length ? Math.max(...vals) : 1

  const features = boundaryGeoJSON.features.map((f: any) => {
    const geoName = String(f.properties?.[geoNameProp] ?? '').trim().toLowerCase()
    const value = lookup[geoName] ?? null
    return {
      ...f,
      properties: { ...f.properties, __value: value ?? 0, __hasData: value !== null },
    }
  })

  return {
    geojson: { ...boundaryGeoJSON, features },
    minVal,
    maxVal,
    valueColName: valueCol ?? 'Count',
  }
}

function computeInitialViewState(data: any[], spatialColumns: { lat?: string; lng?: string; wkt?: string; country?: string; state?: string; city?: string }) {
  const sp = spatialColumns as any

  // Geographic mode: use fixed world/US view for choropleth, compute bbox for cities
  if (sp?.country) return { latitude: 20, longitude: 0, zoom: 2 }
  if (sp?.state) return { latitude: 38, longitude: -96, zoom: 3 }
  if (sp?.city) {
    const lats: number[] = []
    const lngs: number[] = []
    data.forEach(row => {
      const centroid = CITY_CENTROIDS[String(row[sp.city] ?? '').trim()]
      if (centroid) { lats.push(centroid[0]); lngs.push(centroid[1]) }
    })
    if (lats.length === 0) return { latitude: 20, longitude: 0, zoom: 2 }
    const centerLat = (Math.min(...lats) + Math.max(...lats)) / 2
    const centerLng = (Math.min(...lngs) + Math.max(...lngs)) / 2
    const span = Math.max(Math.max(...lats) - Math.min(...lats), Math.max(...lngs) - Math.min(...lngs))
    const zoom = span < 0.5 ? 10 : span < 5 ? 6 : span < 50 ? 3 : 2
    return { latitude: centerLat, longitude: centerLng, zoom }
  }

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

function detectSpatialColumnsFromData(data: any[]): { lat?: string; lng?: string; wkt?: string; country?: string; state?: string; city?: string } | null {
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

  // Third: country column (name hint + value sampling)
  const countryPatterns = ['country', 'nation', 'country_name', 'country name']
  const countryCol = cols.find(c => countryPatterns.includes(c.toLowerCase()))
  if (countryCol) {
    const hits = data.slice(0, 20).filter(r => COUNTRY_CENTROIDS[String(r[countryCol] ?? '')]).length
    if (hits >= 1) return { country: countryCol }
  }

  // Fourth: US state column (name hint + value sampling)
  const statePatterns = ['state', 'state_name', 'province', 'state name']
  const stateCol = cols.find(c => statePatterns.includes(c.toLowerCase()))
  if (stateCol) {
    const hits = data.slice(0, 20).filter(r => lookupStateCentroid(String(r[stateCol] ?? ''))).length
    if (hits >= 1) return { state: stateCol }
  }

  // Fifth: city column (name hint + value sampling)
  const cityPatterns = ['city', 'city_name', 'municipality', 'town', 'city name']
  const cityCol = cols.find(c => cityPatterns.includes(c.toLowerCase()))
  if (cityCol) {
    const hits = data.slice(0, 20).filter(r => CITY_CENTROIDS[String(r[cityCol] ?? '')]).length
    if (hits >= 1) return { city: cityCol }
  }

  return null
}

export function InteractiveMapView({
  datasetId,
  data,
  spatialColumns: spatialColumnsProp,
  chartRows,
  chartQueryId,
}: InteractiveMapViewProps) {
  const mapRef = useRef<MapRef>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const MAPBOX_TOKEN: string = (import.meta as any).env?.VITE_MAPBOX_TOKEN ?? ''

  // If the prop-specified columns don't actually exist in the data (e.g. dataset uses
  // a WKT "Geolocation" column but the NL query extracted lat/lng as computed columns),
  // auto-detect from the real column names present in the data.
  const spatialColumns = useMemo(() => {
    const sp = spatialColumnsProp as any
    if (!data.length) return sp

    const first = data[0]

    // WKT prop: check the wkt column actually exists in data
    if (sp?.wkt && sp.wkt in first) return sp as { wkt: string }

    // Lat/lng prop: check both columns exist in data
    if (sp?.lat && sp?.lng && sp.lat in first && sp.lng in first) return sp as { lat: string; lng: string }

    // Geographic column props: check column exists in data
    if (sp?.country && sp.country in first) return sp as { country: string }
    if (sp?.state && sp.state in first) return sp as { state: string }
    if (sp?.city && sp.city in first) return sp as { city: string }

    // Fall back to auto-detection from actual column names/values
    return detectSpatialColumnsFromData(data) ?? sp
  }, [data, spatialColumnsProp])

  // Whether we're in WKT mode (affects clustering and layer setup)
  const isWktMode = !!spatialColumns?.wkt

  // Geographic (country / state / city) mode helpers
  const sc = spatialColumns as any
  const isCountryMode    = !!sc?.country
  const isStateMode      = !!sc?.state
  const isCityMode       = !!sc?.city
  const isChoroplethMode = isCountryMode || isStateMode

  const [popupInfo, setPopupInfo] = useState<PopupInfo | null>(null)
  const [hoverInfo, setHoverInfo] = useState<HoverInfo | null>(null)
  const [showListPanel, setShowListPanel] = useState(false)
  const [showStatsPanel, setShowStatsPanel] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [chartOverlayClosed, setChartOverlayClosed] = useState(false)
  const [choroplethData, setChoroplethData] = useState<{
    geojson: any; minVal: number; maxVal: number; valueColName: string
  } | null>(null)
  const [geoLoadError, setGeoLoadError] = useState<string | null>(null)

  // Reset chart overlay visibility when a new query result arrives
  useEffect(() => {
    if (chartRows && chartRows.length > 0) {
      setChartOverlayClosed(false)
    }
  }, [chartRows])

  // Fetch + join boundary GeoJSON for choropleth mode (country or state)
  useEffect(() => {
    if (!isChoroplethMode || !data.length) {
      setChoroplethData(null)
      return
    }
    setGeoLoadError(null)
    setChoroplethData(null)
    const nameCol: string = sc.country ?? sc.state
    const excludeCols = makeExcludeSet(spatialColumns ?? {})
    const valueCol = detectValueColumn(data, excludeCols)
    const loader = isCountryMode ? fetchCountriesGeoJSON : fetchUSStatesGeoJSON
    loader()
      .then(boundary => {
        const result = buildChoroplethGeojson(boundary, data, nameCol, 'name', valueCol)
        setChoroplethData(result)
      })
      .catch(err => {
        console.error('Failed to load boundary GeoJSON', err)
        setGeoLoadError('Failed to load map boundaries')
      })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, isChoroplethMode, isCountryMode, sc?.country, sc?.state])

  // Skip fitBounds on initial mount — only fly when data changes from a query result
  const isInitialized = useRef(false)

  useEffect(() => {
    if (!isInitialized.current) {
      isInitialized.current = true
      return
    }

    // City mode: fit to visible city centroids
    if (isCityMode && sc?.city) {
      const lats: number[] = []
      const lngs: number[] = []
      data.forEach(row => {
        const centroid = CITY_CENTROIDS[String(row[sc.city] ?? '').trim()]
        if (centroid) { lats.push(centroid[0]); lngs.push(centroid[1]) }
      })
      if (lats.length > 0) {
        setTimeout(() => {
          mapRef.current?.getMap()?.fitBounds(
            [[Math.min(...lngs), Math.min(...lats)], [Math.max(...lngs), Math.max(...lats)]],
            { padding: 60, maxZoom: 10, duration: 800 }
          )
        }, 150)
      }
      return
    }

    // Choropleth mode: no fitBounds needed (fixed world/US view)
    if (isChoroplethMode) return

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

  const cityGeojson = useMemo(
    () => (isCityMode && sc?.city ? buildGeojsonFromCity(filteredData, sc.city) : null),
    [filteredData, isCityMode, sc?.city]
  )

  // ─── Map interactions ───────────────────────────────────────────────────────

  // Layers that respond to clicks/hover
  const interactiveLayerIds = isChoroplethMode
    ? ['geo-fill']
    : isWktMode
    ? ['wkt-polygon-fill', 'wkt-line', 'wkt-point']
    : ['clusters', 'unclustered-point']

  const handleClick = useCallback((event: MapLayerMouseEvent) => {
    const features = (event as any).features as Array<{ layer?: { id?: string }; properties?: any; geometry?: any }> | undefined
    if (!features || features.length === 0) { setPopupInfo(null); return }

    const feature = features[0]

    if (feature.layer?.id === 'geo-fill') {
      // Strip internal choropleth properties before showing popup
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { __value: _v, __hasData, ...props } = feature.properties ?? {}
      if (__hasData) {
        setPopupInfo({ longitude: event.lngLat.lng, latitude: event.lngLat.lat, properties: props })
      } else {
        setPopupInfo(null)
      }
      return
    }

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
    const interactiveLayers = new Set(['unclustered-point', 'wkt-point', 'wkt-polygon-fill', 'wkt-line', 'geo-fill'])
    const pts = features?.filter(f => f.layer?.id && interactiveLayers.has(f.layer.id))
    if (pts && pts.length > 0) {
      // Strip choropleth internals from hover tooltip
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { __value: _v2, __hasData, ...visibleProps } = pts[0].properties ?? {}
      if (pts[0].layer?.id === 'geo-fill' && !__hasData) { setHoverInfo(null); return }
      setHoverInfo({ x: event.point.x, y: event.point.y, properties: visibleProps })
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

  const pointCount = isChoroplethMode
    ? filteredData.length
    : isCityMode
    ? (cityGeojson?.features?.length ?? 0)
    : geojson.features.length
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

        {isChoroplethMode && choroplethData ? (
          /* ── Choropleth: country or US state polygons ── */
          <Source id="geo-boundaries" type="geojson" data={choroplethData.geojson}>
            <Layer
              id="geo-fill"
              type="fill"
              paint={{
                'fill-color': [
                  'case', ['==', ['get', '__hasData'], true] as any,
                  ['interpolate', ['linear'], ['get', '__value'],
                    choroplethData.minVal === choroplethData.maxVal ? choroplethData.minVal - 1 : choroplethData.minVal, '#dbeafe',
                    choroplethData.minVal === choroplethData.maxVal ? choroplethData.maxVal + 1 : choroplethData.maxVal, '#1d4ed8',
                  ] as any,
                  '#e5e7eb',
                ] as any,
                'fill-opacity': 0.75,
              }}
            />
            <Layer
              id="geo-outline"
              type="line"
              paint={{ 'line-color': '#9ca3af', 'line-width': 0.5, 'line-opacity': 0.8 }}
            />
          </Source>
        ) : isCityMode && cityGeojson ? (
          /* ── City centroid points (clustered) ── */
          <Source
            id="points"
            type="geojson"
            data={cityGeojson}
            cluster={true}
            clusterMaxZoom={14}
            clusterRadius={50}
          >
            <Layer
              id="clusters"
              type="circle"
              filter={['has', 'point_count']}
              paint={{
                'circle-color': [
                  'step', ['get', 'point_count'],
                  '#6366f1', 10, '#3b82f6', 100, '#0ea5e9',
                ] as any,
                'circle-radius': ['step', ['get', 'point_count'], 20, 10, 30, 100, 40] as any,
                'circle-stroke-width': 3,
                'circle-stroke-color': '#fff',
                'circle-opacity': 0.9,
              }}
            />
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
        ) : isWktMode ? (
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
        {isChoroplethMode && (
          <div className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium shadow-md border
                          bg-card/90 text-muted-foreground border-border"
            title={isCountryMode ? 'Country choropleth' : 'US State choropleth'}
          >
            <Globe className="h-4 w-4" />
            <span className="hidden sm:inline">{isCountryMode ? 'Countries' : 'States'}</span>
          </div>
        )}
        {isCityMode && (
          <div className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium shadow-md border
                          bg-card/90 text-muted-foreground border-border"
            title="City centroids mode"
          >
            <Globe className="h-4 w-4" />
            <span className="hidden sm:inline">Cities</span>
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

      {/* ── Choropleth legend (bottom-left) ── */}
      {isChoroplethMode && choroplethData && (
        <div className="absolute bottom-20 left-3 z-10">
          <div className="bg-card/85 backdrop-blur border border-border rounded-xl shadow-md px-3 py-2">
            <div className="text-xs font-semibold text-muted-foreground mb-1.5 capitalize">
              {choroplethData.valueColName.replace(/_/g, ' ')}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">{formatValue(choroplethData.minVal)}</span>
              <div className="w-20 h-3 rounded" style={{ background: 'linear-gradient(to right, #dbeafe, #1d4ed8)' }} />
              <span className="text-xs text-muted-foreground">{formatValue(choroplethData.maxVal)}</span>
            </div>
            <div className="flex items-center gap-1.5 mt-1.5">
              <div className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ backgroundColor: '#e5e7eb', border: '1px solid #d1d5db' }} />
              <span className="text-xs text-muted-foreground">No data</span>
            </div>
          </div>
        </div>
      )}

      {/* ── Category legend (bottom-left) ── */}
      {!isChoroplethMode && categoryColumn && Object.keys(categoryColorMap).length > 0 && (
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

      {/* ── Choropleth loading state ── */}
      {isChoroplethMode && !choroplethData && !geoLoadError && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
          <div className="bg-card/80 backdrop-blur px-4 py-2 rounded-xl text-sm text-muted-foreground shadow">
            Loading map boundaries…
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
          queryId={chartQueryId}
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
