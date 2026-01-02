import React, { useEffect, useRef, useCallback } from 'react'
import { useDispatch } from 'react-redux'
import KeplerGl from '@kepler.gl/components'
import { addDataToMap } from '@kepler.gl/actions'
import AutoSizer from 'react-virtualized-auto-sizer'

interface MapViewProps {
  datasetId: string
  data: any[]
  spatialColumns: {
    lat: string
    lng: string
  }
  config?: any
  onSaveConfig?: (config: any) => void
}

export function MapView({
  datasetId,
  data,
  spatialColumns,
  config,
  onSaveConfig
}: MapViewProps) {
  const dispatch = useDispatch()
  const dataLoadedRef = useRef(false)
  const previousDataLengthRef = useRef(0)

  const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || ''

  const loadDataToMap = useCallback(() => {
    try {
      if (!data || data.length === 0) {
        console.log('MapView: No data to load')
        return
      }

      // Convert data to Kepler.gl format with proper field types
      const columnNames = Object.keys(data[0] || {})
      const fields = columnNames.map(name => {
        const value = data[0][name]
        return {
          name,
          type: inferFieldType(value),
          format: ''
        }
      })

      // Convert rows to arrays in the same order as fields
      const rows = data.map(row =>
        columnNames.map(col => {
          const value = row[col]
          // Handle null/undefined values
          if (value === null || value === undefined) return null
          return value
        })
      )

      const keplerData = {
        fields,
        rows
      }

      console.log('Loading data into Kepler.gl:', {
        datasetId,
        rowCount: rows.length,
        fieldCount: fields.length,
        spatialColumns,
        sampleRow: data[0],
        keplerFields: fields,
        sampleKeplerRow: rows[0]
      })

      // Dispatch action to add data to Kepler
      // Use a unique dataset ID based on data length to force refresh
      const uniqueDatasetId = `${datasetId}-${data.length}`

      const addDataAction = addDataToMap({
        datasets: {
          info: {
            label: `Dataset ${datasetId} (${data.length} rows)`,
            id: uniqueDatasetId
          },
          data: keplerData
        },
        options: {
          centerMap: true,
          readOnly: false,
          keepExistingConfig: false
        },
        config: config || undefined
      })

      // Dispatch with the correct map instance ID
      dispatch({
        ...addDataAction,
        meta: {
          ...addDataAction.meta,
          mapId: 'map'  // Must match the KeplerGl id prop
        }
      })

      dataLoadedRef.current = true
      previousDataLengthRef.current = data.length
      console.log('MapView: Data dispatch complete')
    } catch (error) {
      console.error('Error loading data into Kepler.gl:', error)
      console.error('Error details:', error)
    }
  }, [data, datasetId, spatialColumns, config, dispatch])

  useEffect(() => {
    // Reset loaded flag when dataset changes or data length changes significantly
    const dataLength = data?.length || 0
    if (previousDataLengthRef.current !== dataLength) {
      console.log('MapView: Data length changed, will reload', {
        previous: previousDataLengthRef.current,
        current: dataLength
      })
      dataLoadedRef.current = false
    }
  }, [data])

  useEffect(() => {
    // Reset when dataset changes
    dataLoadedRef.current = false
  }, [datasetId])

  useEffect(() => {
    // Only load data once per data change
    if (dataLoadedRef.current) {
      console.log('MapView: Data already loaded, skipping')
      return
    }

    if (!data || data.length === 0) {
      console.log('MapView: No data to load', { dataLength: data?.length })
      return
    }

    // Wait for Kepler to fully mount
    const timer = setTimeout(() => {
      loadDataToMap()
    }, 500)

    return () => clearTimeout(timer)
  }, [data, loadDataToMap])

  if (!MAPBOX_TOKEN) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center p-6 max-w-md">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Mapbox Token Required
          </h3>
          <p className="text-gray-600 mb-4">
            To use the map visualization, please add a Mapbox access token to your environment variables.
          </p>
          <div className="bg-gray-100 p-4 rounded-lg text-left">
            <p className="text-sm font-mono text-gray-700">
              VITE_MAPBOX_TOKEN=your_token_here
            </p>
          </div>
          <p className="text-sm text-gray-500 mt-4">
            Get a free token at{' '}
            <a
              href="https://account.mapbox.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline"
            >
              mapbox.com
            </a>
          </p>
        </div>
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center p-6">
          <p className="text-gray-600">No data to display on map</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full w-full relative">
      <AutoSizer>
        {({ height, width }) => (
          <KeplerGl
            id="map"
            mapboxApiAccessToken={MAPBOX_TOKEN}
            width={width}
            height={height}
            appName="AI Spreadsheets - Talk2Map"
            version="v1"
            theme="light"
          />
        )}
      </AutoSizer>
    </div>
  )
}

/**
 * Infer Kepler.gl field type from value
 * Valid types: integer, real, boolean, date, timestamp, string, geometry, geojson
 */
function inferFieldType(value: any): string {
  if (value === null || value === undefined) return 'string'

  const type = typeof value

  if (type === 'number') {
    // Kepler.gl expects 'integer' or 'real', not 'number'
    return Number.isInteger(value) ? 'integer' : 'real'
  }

  if (type === 'boolean') return 'boolean'

  if (value instanceof Date) return 'timestamp'

  // Check if string is a date
  if (type === 'string') {
    const dateRegex = /^\d{4}-\d{2}-\d{2}/
    if (dateRegex.test(value)) {
      return 'timestamp'
    }
  }

  return 'string'
}
