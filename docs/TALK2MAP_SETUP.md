# Talk2Map Integration - Setup Guide

## Overview

Talk2Map extends the AI Spreadsheets platform with powerful geospatial visualization capabilities using **Kepler.gl**. Upload CSV files with spatial data (latitude/longitude or addresses), visualize them on interactive maps, and ask natural language questions to filter and explore your data geographically.

## Features

- ✅ **Automatic Spatial Detection**: Detects lat/lng columns, addresses, or geographic data
- ✅ **Kepler.gl Visualization**: Interactive maps with multiple layer types (points, heatmaps, arcs, etc.)
- ✅ **Query Integration**: Natural language queries automatically update the map view
- ✅ **Rich Interactions**: Tooltips, filtering, zooming, and layer customization
- ✅ **Canvas Integration**: Save map snapshots to your canvas workspace

## Quick Start

### 1. Get a Mapbox Token

1. Go to [https://account.mapbox.com](https://account.mapbox.com)
2. Sign up for a free account
3. Navigate to **Access Tokens**
4. Copy your default public token (or create a new one)

### 2. Configure Environment

Add the token to `frontend/.env`:

```bash
VITE_MAPBOX_TOKEN=pk.eyJ1IjoieW91cnVzZXJuYW1lIiwiYSI6InlvdXJ0b2tlbiJ9...
```

### 3. Upload Spatial Data

Your CSV should have **latitude/longitude columns**. Common patterns detected:

#### Coordinate Columns
```csv
name,latitude,longitude,value
New York,40.7128,-74.0060,100
Los Angeles,34.0522,-118.2437,85
Chicago,41.8781,-87.6298,92
```

#### Alternative Names (all supported)
- **Latitude**: `lat`, `latitude`, `y`, `lat_`, `_lat`, `ycoord`
- **Longitude**: `lng`, `lon`, `longitude`, `x`, `lng_`, `_lng`, `long`, `xcoord`

#### Address Columns (geocoding - planned)
```csv
name,address,value
Store A,123 Main St New York NY,100
Store B,456 Oak Ave Los Angeles CA,85
```

### 4. View Your Data on the Map

1. Upload your CSV file
2. Navigate to the dataset detail page
3. If spatial columns are detected, you'll see a **Map** tab
4. Click the tab to visualize your data with Kepler.gl

### 5. Query and Filter

Ask questions in the chat sidebar:

- "Show locations in California"
- "Find points with value > 50"
- "What's the distribution in the northeast?"

The map automatically updates to highlight filtered results!

## Technical Architecture

### Backend Components

#### SpatialService (`backend/app/services/spatial_service.py`)
- **Detects** lat/lng, address, or geographic columns
- **Validates** coordinate ranges and data quality
- **Generates** Kepler.gl configuration with optimal zoom/center
- **Geocodes** addresses (future feature)

```python
from app.services.spatial_service import SpatialService

service = SpatialService()
spatial_info = service.detect_spatial_columns(df)
# Returns: { has_spatial, type, columns, bounding_box, default_config }
```

#### API Endpoint (`/datasets/{id}/spatial-info`)
```bash
GET /api/v1/datasets/{dataset_id}/spatial-info

Response:
{
  "has_spatial": true,
  "type": "coordinates",
  "columns": {
    "lat": "latitude",
    "lng": "longitude"
  },
  "bounding_box": {
    "min_lat": 40.0,
    "max_lat": 41.0,
    "min_lng": -74.5,
    "max_lng": -73.5
  },
  "default_config": { ... } // Kepler.gl config
}
```

### Frontend Components

#### Redux Store (`frontend/src/store/index.ts`)
Kepler.gl uses Redux for state management. The store combines:
- `keplerGl`: Kepler.gl reducer (manages map state, layers, filters)
- Future: Add your app's reducers here

#### MapView Component (`frontend/src/components/map/MapView.tsx`)
Main visualization component:
- Loads data into Kepler.gl
- Handles responsive sizing
- Shows Mapbox token warning if not configured
- Supports filtered data from queries

```typescript
<MapView
  datasetId={id}
  data={queryResult?.rows || preview?.rows}
  spatialColumns={{ lat: 'latitude', lng: 'longitude' }}
  config={mapConfig}
/>
```

#### DatasetDetail Integration (`frontend/src/pages/DatasetDetail.tsx`)
- Fetches spatial info on dataset load
- Conditionally renders Map tab if spatial data exists
- Passes filtered query results to MapView

### Database Schema

New fields in `datasets` table:

```sql
has_spatial_data BOOLEAN DEFAULT FALSE
spatial_config JSONB NULL
```

Future: Persist detected spatial metadata for faster loading.

## Supported Data Formats

### 1. Latitude/Longitude (Best)
```csv
id,name,lat,lng,category,value
1,Point A,40.7128,-74.0060,restaurant,95
2,Point B,34.0522,-118.2437,cafe,88
```

### 2. Address (Geocoding - Coming Soon)
```csv
id,name,address,value
1,Store A,"123 Main St, New York, NY 10001",100
2,Store B,"456 Oak Ave, Los Angeles, CA 90001",85
```

### 3. Geographic (City/State/Zip - Coming Soon)
```csv
id,name,city,state,zip,value
1,Location A,New York,NY,10001,100
2,Location B,Los Angeles,CA,90001,85
```

## Advanced Features

### Kepler.gl Capabilities

1. **Multiple Layer Types**
   - Points (default)
   - Heatmaps
   - Hexbin aggregation
   - Arcs (for origin-destination flows)
   - 3D buildings

2. **Interactive Filters**
   - Range sliders for numeric fields
   - Time series animation
   - Multi-select for categories

3. **Styling Options**
   - Color by field value
   - Size by field value
   - Custom color scales
   - Dark/light map styles

4. **Export Options**
   - Export as image (PNG)
   - Export configuration (JSON)
   - Export data (CSV)

### Future Enhancements

- [ ] **Geocoding Integration**: Auto-convert addresses to coordinates
- [ ] **Spatial Queries**: "Show points within 5 miles of X"
- [ ] **Drawing Tools**: Draw polygons to filter data
- [ ] **Canvas Integration**: Save map snapshots to workspace
- [ ] **Multi-dataset Layers**: Overlay multiple datasets
- [ ] **Heatmap Auto-generation**: Smart layer suggestions
- [ ] **Time Series**: Animate data over time

## Troubleshooting

### "Mapbox Token Required" Message

**Problem**: Map tab shows token error

**Solution**: Add `VITE_MAPBOX_TOKEN` to `frontend/.env` and restart dev server

```bash
# Stop the server (Ctrl+C)
cd frontend
# Add token to .env
echo "VITE_MAPBOX_TOKEN=your_token_here" >> .env
# Restart
npm run dev
```

### Map Tab Not Showing

**Problem**: No Map tab appears for dataset

**Possible Causes**:
1. Dataset doesn't have lat/lng columns
2. Column names don't match patterns (see supported names above)
3. Coordinates are invalid (out of range)

**Solution**:
- Check your CSV has columns like `latitude`/`longitude`
- Ensure values are numeric and in valid ranges:
  - Latitude: -90 to 90
  - Longitude: -180 to 180

### Map Loads But No Points Visible

**Problem**: Map renders but data points are missing

**Possible Causes**:
1. Data has null/invalid coordinates
2. Zoom level is wrong
3. Layer is hidden

**Solution**:
- Open Kepler.gl layer panel (left sidebar)
- Check if layer is visible (toggle eye icon)
- Adjust map zoom to see your data extent

### Performance Issues with Large Datasets

**Problem**: Map is slow with 100k+ points

**Solution**:
1. Use aggregation layers (hexbin, heatmap) instead of points
2. Enable GPU acceleration in browser settings
3. Limit preview to first 10k rows for exploration

## Example Datasets

Try these sample datasets to test Talk2Map:

### 1. NYC Restaurant Inspections
```csv
name,latitude,longitude,grade,score
Joe's Pizza,40.7308,-73.9973,A,95
Shake Shack,40.7414,-73.9887,A,98
```

### 2. Weather Stations
```csv
station_id,lat,lng,temperature,humidity
STATION_1,40.7128,-74.0060,72,65
STATION_2,34.0522,-118.2437,85,45
```

### 3. Store Locations
```csv
store_id,name,latitude,longitude,revenue,employees
1,Store A,40.7580,-73.9855,150000,25
2,Store B,34.0522,-118.2437,200000,30
```

## API Reference

### GET `/datasets/{id}/spatial-info`

**Description**: Detect spatial columns and generate Kepler.gl config

**Response**:
```json
{
  "has_spatial": true,
  "type": "coordinates",
  "columns": { "lat": "latitude", "lng": "longitude" },
  "bounding_box": {
    "min_lat": 40.0,
    "max_lat": 41.0,
    "min_lng": -74.5,
    "max_lng": -73.5
  },
  "default_config": {
    "version": "v1",
    "config": {
      "visState": { ... },
      "mapState": { ... },
      "mapStyle": { ... }
    }
  }
}
```

## Resources

- **Kepler.gl Docs**: [https://docs.kepler.gl](https://docs.kepler.gl)
- **Mapbox**: [https://mapbox.com](https://mapbox.com)
- **Sample Datasets**: [https://github.com/uber/kepler.gl-data](https://github.com/uber/kepler.gl-data)

## Support

For issues or questions:
1. Check this documentation
2. Review console logs in browser DevTools
3. Open an issue with:
   - Dataset sample (first 5 rows)
   - Error messages
   - Browser and OS version
