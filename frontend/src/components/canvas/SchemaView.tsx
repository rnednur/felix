import { useQuery } from '@tanstack/react-query'
import { getDatasetSchema } from '@/services/api'

interface SchemaViewProps {
  datasetId: string
}

export function SchemaView({ datasetId }: SchemaViewProps) {
  const { data: schema, isLoading } = useQuery({
    queryKey: ['dataset-schema', datasetId],
    queryFn: () => getDatasetSchema(datasetId),
    enabled: !!datasetId,
  })

  if (isLoading) {
    return <div className="p-6 text-center">Loading schema...</div>
  }

  if (!schema) {
    return <div className="p-6 text-center text-gray-500">No schema available</div>
  }

  return (
    <div className="h-full overflow-auto p-6">
      <div className="space-y-6">
        {/* Overview Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-500">Total Columns</p>
            <p className="text-2xl font-semibold mt-1">{schema.columns.length}</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-500">Total Rows</p>
            <p className="text-2xl font-semibold mt-1">{schema.total_rows.toLocaleString()}</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-500">Computed</p>
            <p className="text-sm font-medium mt-1">
              {new Date(schema.computed_at).toLocaleString()}
            </p>
          </div>
        </div>

        {/* Columns Table */}
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-6 py-3 border-b border-gray-200">
            <h3 className="text-sm font-semibold text-gray-700">Column Details</h3>
          </div>

          <div className="divide-y divide-gray-200">
            {schema.columns.map((col: any, idx: number) => (
              <div key={idx} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h4 className="text-base font-semibold text-gray-900">{col.name}</h4>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                        {col.dtype}
                      </span>
                      {col.nullable && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                          nullable
                        </span>
                      )}
                      {col.tags.map((tag: string) => (
                        <span
                          key={tag}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Statistics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                  {/* Missing Data */}
                  <div>
                    <p className="text-xs text-gray-500">Missing</p>
                    <p className="text-sm font-medium mt-1">
                      {col.stats.null_count.toLocaleString()} ({col.stats.null_pct.toFixed(1)}%)
                    </p>
                  </div>

                  {/* Unique Values */}
                  <div>
                    <p className="text-xs text-gray-500">Unique Values</p>
                    <p className="text-sm font-medium mt-1">
                      {col.stats.distinct_count.toLocaleString()}
                    </p>
                  </div>

                  {/* Type-specific stats */}
                  {col.stats.min !== undefined && col.stats.max !== undefined && (
                    <>
                      <div>
                        <p className="text-xs text-gray-500">Min</p>
                        <p className="text-sm font-medium mt-1">
                          {typeof col.stats.min === 'number'
                            ? col.stats.min.toLocaleString(undefined, { maximumFractionDigits: 2 })
                            : col.stats.min}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Max</p>
                        <p className="text-sm font-medium mt-1">
                          {typeof col.stats.max === 'number'
                            ? col.stats.max.toLocaleString(undefined, { maximumFractionDigits: 2 })
                            : col.stats.max}
                        </p>
                      </div>
                    </>
                  )}

                  {col.stats.mean !== undefined && (
                    <>
                      <div>
                        <p className="text-xs text-gray-500">Mean</p>
                        <p className="text-sm font-medium mt-1">
                          {col.stats.mean.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Std Dev</p>
                        <p className="text-sm font-medium mt-1">
                          {col.stats.std?.toLocaleString(undefined, { maximumFractionDigits: 2 }) || 'N/A'}
                        </p>
                      </div>
                    </>
                  )}
                </div>

                {/* Top Values for categorical columns */}
                {col.stats.top_values && col.stats.top_values.length > 0 && (
                  <div className="mt-4">
                    <p className="text-xs text-gray-500 mb-2">Top Values</p>
                    <div className="flex flex-wrap gap-2">
                      {col.stats.top_values.slice(0, 5).map(([value, count]: [string, number], i: number) => (
                        <div
                          key={i}
                          className="inline-flex items-center gap-2 px-3 py-1 bg-gray-100 rounded-md text-xs"
                        >
                          <span className="font-medium text-gray-900">{value}</span>
                          <span className="text-gray-500">({count.toLocaleString()})</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Quantiles for numeric columns */}
                {col.stats.quantiles && (
                  <div className="mt-4">
                    <p className="text-xs text-gray-500 mb-2">Distribution (Quartiles)</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-100 rounded-lg p-2 text-center">
                        <p className="text-xs text-gray-500">25%</p>
                        <p className="text-sm font-medium">
                          {col.stats.quantiles['0.25']?.toLocaleString(undefined, {
                            maximumFractionDigits: 2,
                          })}
                        </p>
                      </div>
                      <div className="flex-1 bg-gray-100 rounded-lg p-2 text-center">
                        <p className="text-xs text-gray-500">50% (Median)</p>
                        <p className="text-sm font-medium">
                          {col.stats.quantiles['0.5']?.toLocaleString(undefined, {
                            maximumFractionDigits: 2,
                          })}
                        </p>
                      </div>
                      <div className="flex-1 bg-gray-100 rounded-lg p-2 text-center">
                        <p className="text-xs text-gray-500">75%</p>
                        <p className="text-sm font-medium">
                          {col.stats.quantiles['0.75']?.toLocaleString(undefined, {
                            maximumFractionDigits: 2,
                          })}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
