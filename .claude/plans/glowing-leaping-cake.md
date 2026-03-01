# Foursquare-Style Map Implementation Plan

## What "More Like Foursquare" Means

Foursquare's key map UX elements (translated to a data analytics app):
1. **Clustered points** with count badges — points near each other merge into circles
2. **Click popup/card** — clicking a point shows a full data card for that row
3. **Hover tooltip** — brief field preview on mouse-over
4. **Side list panel** — scrollable list of visible points beside the map (toggle on/off)
5. **Category coloring** — auto-detect a categorical column and color points by it
6. **Color legend** — shows which color = which category
7. **Search/filter** — text search to filter visible points by any field

---

## Current State

- **Library**: Kepler.gl v3.2.4 (heavy, enterprise-grade; ironically made by Foursquare)
- **Approach**: Kepler.gl manages all state via Redux; no custom popup/tooltip/list UI
- **Missing**: clustering UI, click cards, hover tooltips, side list, category coloring

## Approach

Build a **new** `FoursquareMapView.tsx` using `react-map-gl` + native Mapbox GL clustering, replacing the Kepler.gl component. This gives full UX control without Redux overhead.

- Mapbox's GeoJSON source supports `cluster: true` natively — no extra package needed
- `react-map-gl` is a direct peer dep of Kepler.gl so it's already in node_modules; install it directly
- Keep `MapView.tsx` (Kepler.gl) unchanged for now — swap at `MapItem.tsx` level

---

## Files to Create/Modify

1. **Install** `react-map-gl` as direct dep (peer dep of Kepler.gl, already in node_modules)
2. **Create** `frontend/src/components/map/FoursquareMapView.tsx` — the new map component
3. **Update** `frontend/src/components/canvas/MapItem.tsx` — swap MapView → FoursquareMapView

---

## Implementation

### Step 1 — Install package
```bash
npm install react-map-gl --legacy-peer-deps
```

---

### Step 2 — FoursquareMapView.tsx

**File:** `frontend/src/components/map/FoursquareMapView.tsx`

**Props (same interface as MapView):**
```typescript
interface FoursquareMapViewProps {
  datasetId: string
  data: any[]
  spatialColumns: { lat: string; lng: string }
  config?: any
  onSaveConfig?: (config: any) => void
}
```

**Architecture:**

```
FoursquareMapView
├── Map (react-map-gl)
│   ├── Source (GeoJSON, cluster:true)
│   │   ├── Layer: cluster circles  (colored by count)
│   │   ├── Layer: cluster count labels
│   │   └── Layer: individual points  (colored by category)
│   ├── Popup (click — shows data card)
│   └── Hover tooltip (lightweight)
├── Search/filter bar (top-left overlay)
├── Category legend (bottom-left overlay)
└── Side list panel (right side, toggleable)
```

**Key features to implement:**

**Clustering:**
```typescript
// GeoJSON source with cluster enabled
<Source
  id="points"
  type="geojson"
  data={geojsonData}
  cluster={true}
  clusterMaxZoom={14}
  clusterRadius={50}
>
  {/* Cluster circles */}
  <Layer id="clusters" type="circle" filter={['has', 'point_count']}
    paint={{
      'circle-color': ['step', ['get', 'point_count'], '#6366f1', 10, '#3b82f6', 100, '#0ea5e9'],
      'circle-radius': ['step', ['get', 'point_count'], 20, 10, 30, 100, 40],
      'circle-stroke-width': 2, 'circle-stroke-color': '#fff'
    }}
  />
  {/* Count labels */}
  <Layer id="cluster-count" type="symbol" filter={['has', 'point_count']}
    layout={{ 'text-field': '{point_count_abbreviated}', 'text-size': 13 }}
    paint={{ 'text-color': '#fff' }}
  />
  {/* Individual points — colored by category */}
  <Layer id="unclustered-point" type="circle" filter={['!', ['has', 'point_count']]}
    paint={{
      'circle-color': categoryColorExpression,  // Mapbox expression
      'circle-radius': 8,
      'circle-stroke-width': 2,
      'circle-stroke-color': '#fff'
    }}
  />
</Source>
```

**Category auto-detection:**
```typescript
// Find first string column (not lat/lng) with ≤20 unique values → use as category
function detectCategoryColumn(data, spatialColumns): string | null
// Build a palette of up to 12 colors for categories
// Build Mapbox match expression for circle-color
```

**Click handler:**
```typescript
// On click: if cluster → zoom in; if point → show popup with all field/value pairs
// Popup renders as a Foursquare-style card:
//   Title (first string field), then key-value list of all other fields
```

**Hover tooltip:**
```typescript
// onMouseMove: show a small 2-3 field tooltip at cursor position
// Uses a simple positioned div (not Mapbox Popup) for performance
```

**Side list panel:**
```typescript
// Toggle button in map overlay
// Shows scrollable list of visible points (filtered by search + viewport bounds)
// Each card: color dot, title field value, 2-3 other fields
// Click → fly to point and open popup
```

**Search filter:**
```typescript
// Input at top of map — filters geojsonData to rows where ANY field includes search text
// Clears on × button
```

**Legend:**
```typescript
// If categoryColumn detected: render color swatches + label for each category
// Positioned bottom-left of map
```

---

### Step 3 — MapItem.tsx update

Replace the `MapView` import and usage with `FoursquareMapView`:

```typescript
// Before:
import { MapView } from '@/components/map/MapView'
// <MapView datasetId={...} data={...} spatialColumns={...} config={...} />

// After:
import { FoursquareMapView } from '@/components/map/FoursquareMapView'
// <FoursquareMapView datasetId={...} data={...} spatialColumns={...} config={...} />
```

No other changes to MapItem — the props interface is identical.

---

## Verification

1. Open a dataset with spatial data → map renders with clustered points
2. Zoom in → clusters expand into individual colored dots
3. Click a cluster → map zooms in to expand it
4. Click an individual point → Foursquare-style card appears with all row data
5. Hover over a point → brief tooltip shows
6. Toggle side panel → list of visible points appears; click one → flies to it on map
7. Type in search bar → list + map points filter to matching rows
8. Category legend shows if a categorical column was detected
9. Dark mode: map overlay cards respect dark mode classes
10. No Mapbox token → shows same token error as before
