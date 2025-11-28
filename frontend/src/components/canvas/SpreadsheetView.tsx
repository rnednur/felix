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
      <table className="border border-gray-200 rounded-lg bg-white min-w-full">
        <thead className="bg-gray-50 border-b border-gray-200 sticky top-0 z-10">
          <tr>
            {data.columns.map((col) => (
              <th
                key={col}
                className="p-3 border-r border-gray-200 text-sm font-medium text-gray-700 text-left last:border-r-0 whitespace-nowrap"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.rows.map((row, i) => (
            <tr
              key={i}
              className="border-b border-gray-200 hover:bg-gray-50"
            >
              {data.columns.map((col) => (
                <td
                  key={col}
                  className="p-3 border-r border-gray-200 text-sm text-gray-900 last:border-r-0"
                >
                  {row[col]?.toString() || ''}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
