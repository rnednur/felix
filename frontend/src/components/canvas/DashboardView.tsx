import { VegaChart } from '@/components/visualization/VegaChart'

interface DashboardViewProps {
  queryResult?: {
    columns: string[]
    rows: any[]
    sql?: string
    execution_time_ms?: number
    total_rows?: number
  }
  charts: Array<{
    type: string
    spec: any
    title?: string
  }>
}

export function DashboardView({ queryResult, charts }: DashboardViewProps) {
  if (!queryResult) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <div className="text-center">
          <p className="text-lg font-medium">No query results yet</p>
          <p className="text-sm mt-2">Ask a question to see results and visualizations</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-auto">
      <div className="p-6 space-y-6">
        {/* Query Info */}
        {queryResult.sql && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-700">Generated SQL</h3>
              <span className="text-xs text-gray-500">
                {queryResult.execution_time_ms}ms • {queryResult.total_rows?.toLocaleString()} rows
              </span>
            </div>
            <pre className="text-xs text-gray-600 overflow-x-auto">{queryResult.sql}</pre>
          </div>
        )}

        {/* Results Table */}
        {queryResult.rows.length > 0 && (
          <div className="border border-gray-200 rounded-lg bg-white overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700">Query Results</h3>
            </div>
            <div className="overflow-x-auto max-h-80">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    {queryResult.columns.map((col) => (
                      <th
                        key={col}
                        className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase"
                      >
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {queryResult.rows.slice(0, 50).map((row, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      {queryResult.columns.map((col) => (
                        <td key={col} className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                          {row[col]?.toString() || ''}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {queryResult.rows.length > 50 && (
              <div className="bg-gray-50 px-4 py-2 border-t border-gray-200 text-xs text-gray-500">
                Showing first 50 of {queryResult.total_rows?.toLocaleString()} rows
              </div>
            )}
          </div>
        )}

        {/* Visualizations */}
        {charts.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Visualizations</h3>
            <div className={`grid gap-6 ${charts.length === 1 ? 'grid-cols-1' : 'grid-cols-2'}`}>
              {charts.map((chart, i) => (
                <div key={i} className="border border-gray-200 rounded-lg bg-white p-6">
                  <h4 className="font-semibold mb-4 capitalize">
                    {chart.title || `${chart.type} Chart`}
                  </h4>
                  <VegaChart spec={chart.spec} onExport={() => {}} />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
