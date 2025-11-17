interface SpreadsheetViewProps {
  data: {
    columns: string[]
    rows: any[]
  }
}

export function SpreadsheetView({ data }: SpreadsheetViewProps) {
  if (!data || !data.rows || data.rows.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <p>No data to display</p>
      </div>
    )
  }

  return (
    <div className="h-full overflow-auto">
      <div className="border border-gray-200 rounded-lg bg-white overflow-hidden">
        {/* Header */}
        <div className="grid bg-gray-50 border-b border-gray-200 sticky top-0" style={{ gridTemplateColumns: `repeat(${data.columns.length}, minmax(150px, 1fr))` }}>
          {data.columns.map((col) => (
            <div
              key={col}
              className="p-3 border-r border-gray-200 text-sm font-medium text-gray-700 last:border-r-0"
            >
              {col}
            </div>
          ))}
        </div>

        {/* Rows */}
        {data.rows.map((row, i) => (
          <div
            key={i}
            className="grid border-b border-gray-200 hover:bg-gray-50"
            style={{ gridTemplateColumns: `repeat(${data.columns.length}, minmax(150px, 1fr))` }}
          >
            {data.columns.map((col) => (
              <div
                key={col}
                className="p-3 border-r border-gray-200 text-sm text-gray-900 last:border-r-0"
              >
                {row[col]?.toString() || ''}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
