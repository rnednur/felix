import React, { useEffect, useRef } from 'react'
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
  const mapLoaded = useRef(false)

  const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || ''

  useEffect(() => {
    if (!data || data.length === 0 || mapLoaded.current) {
      return
    }

    try {
      // Convert data to Kepler.gl format
      const fields = Object.keys(data[0] || {}).map(name => ({
        name,
        type: inferFieldType(data[0][name])
      }))

      const rows = data.map(row => Object.values(row))

      const keplerData = {
        fields,
        rows
      }

      console.log('Loading data into Kepler.gl:', {
        datasetId,
        rowCount: rows.length,
        fieldCount: fields.length,
        spatialColumns
      })

      // Dispatch action to add data to Kepler
      dispatch(
        addDataToMap({
          datasets: {
            info: {
              label: `Dataset ${datasetId}`,
              id: datasetId
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
      )

      mapLoaded.current = true
    } catch (error) {
      console.error('Error loading data into Kepler.gl:', error)
    }
  }, [data, datasetId, spatialColumns, config, dispatch])

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
 */
function inferFieldType(value: any): string {
  if (value === null || value === undefined) return 'string'

  const type = typeof value

  if (type === 'number') {
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
