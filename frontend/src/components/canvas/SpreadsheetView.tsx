import { useState } from 'react'
import { cn } from '@/lib/utils'
import { ChevronUp, ChevronDown, Search, Download, Filter } from 'lucide-react'

interface SpreadsheetViewProps {
  data: {
    columns: string[]
    rows: any[]
  }
  title?: string
  subtitle?: string
}

export function SpreadsheetView({ data, title, subtitle }: SpreadsheetViewProps) {
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')
  const [searchQuery, setSearchQuery] = useState('')

  if (!data || !data.rows || data.rows.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mx-auto mb-3">
            <Filter className="h-5 w-5 text-muted-foreground" />
          </div>
          <p className="text-sm text-muted-foreground">No data to display</p>
        </div>
      </div>
    )
  }

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(column)
      setSortDirection('asc')
    }
  }

  // Sort and filter data
  let displayRows = [...data.rows]

  if (searchQuery) {
    const query = searchQuery.toLowerCase()
    displayRows = displayRows.filter(row =>
      data.columns.some(col =>
        String(row[col] ?? '').toLowerCase().includes(query)
      )
    )
  }

  if (sortColumn) {
    displayRows.sort((a, b) => {
      const aVal = a[sortColumn]
      const bVal = b[sortColumn]

      if (aVal === null || aVal === undefined) return 1
      if (bVal === null || bVal === undefined) return -1

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDirection === 'asc' ? aVal - bVal : bVal - aVal
      }

      const aStr = String(aVal).toLowerCase()
      const bStr = String(bVal).toLowerCase()
      return sortDirection === 'asc'
        ? aStr.localeCompare(bStr)
        : bStr.localeCompare(aStr)
    })
  }

  const formatCellValue = (value: any): string => {
    if (value === null || value === undefined) return '—'
    if (typeof value === 'number') {
      if (Number.isInteger(value)) return value.toLocaleString()
      return value.toLocaleString(undefined, { maximumFractionDigits: 2 })
    }
    if (typeof value === 'boolean') return value ? 'Yes' : 'No'
    return String(value)
  }

  const getCellAlignment = (value: any): string => {
    if (typeof value === 'number') return 'text-right'
    return 'text-left'
  }

  return (
    <div className="h-full flex flex-col bg-card rounded-lg border border-border overflow-hidden">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-border bg-background-subtle">
        <div>
          {title && (
            <h3 className="font-medium text-sm text-foreground">{title}</h3>
          )}
          {subtitle && (
            <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>
          )}
          {!title && (
            <p className="text-xs text-muted-foreground">
              Showing {displayRows.length.toLocaleString()} of {data.rows.length.toLocaleString()} rows
            </p>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={cn(
                'pl-8 pr-3 py-1.5 w-48',
                'text-xs bg-card border border-border rounded-md',
                'placeholder:text-muted-foreground',
                'focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary',
                'transition-all duration-150'
              )}
            />
          </div>

          {/* Export button */}
          <button
            className={cn(
              'p-1.5 rounded-md',
              'text-muted-foreground hover:text-foreground',
              'hover:bg-muted',
              'transition-colors duration-150'
            )}
            title="Export data"
          >
            <Download className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full">
          <thead className="sticky top-0 z-10">
            <tr className="bg-muted border-b border-border">
              {data.columns.map((col) => (
                <th
                  key={col}
                  onClick={() => handleSort(col)}
                  className={cn(
                    'px-4 py-2.5',
                    'text-xs font-semibold text-muted-foreground uppercase tracking-wider',
                    'text-left whitespace-nowrap',
                    'border-r border-border last:border-r-0',
                    'cursor-pointer select-none',
                    'hover:bg-muted/80 transition-colors duration-150',
                    'group'
                  )}
                >
                  <div className="flex items-center gap-1.5">
                    <span className="truncate max-w-[150px]" title={col}>
                      {col}
                    </span>
                    <div className="flex flex-col opacity-0 group-hover:opacity-100 transition-opacity">
                      {sortColumn === col ? (
                        sortDirection === 'asc' ? (
                          <ChevronUp className="h-3 w-3 text-primary" />
                        ) : (
                          <ChevronDown className="h-3 w-3 text-primary" />
                        )
                      ) : (
                        <ChevronUp className="h-3 w-3 text-muted-foreground" />
                      )}
                    </div>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {displayRows.map((row, i) => (
              <tr
                key={i}
                className={cn(
                  'transition-colors duration-100',
                  i % 2 === 0 ? 'bg-card' : 'bg-background-subtle/50',
                  'hover:bg-primary-muted/30'
                )}
              >
                {data.columns.map((col) => (
                  <td
                    key={col}
                    className={cn(
                      'px-4 py-2.5',
                      'text-sm text-foreground',
                      'border-r border-border last:border-r-0',
                      'whitespace-nowrap',
                      getCellAlignment(row[col])
                    )}
                  >
                    <span
                      className={cn(
                        'block truncate max-w-[200px]',
                        row[col] === null || row[col] === undefined
                          ? 'text-muted-foreground italic'
                          : ''
                      )}
                      title={String(row[col] ?? '')}
                    >
                      {formatCellValue(row[col])}
                    </span>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="flex-shrink-0 px-4 py-2 border-t border-border bg-background-subtle">
        <p className="text-xs text-muted-foreground">
          {searchQuery ? (
            <>
              Found <span className="font-medium text-foreground">{displayRows.length.toLocaleString()}</span> matching rows
            </>
          ) : (
            <>
              <span className="font-medium text-foreground">{data.columns.length}</span> columns
              {' · '}
              <span className="font-medium text-foreground">{data.rows.length.toLocaleString()}</span> rows
            </>
          )}
        </p>
      </div>
    </div>
  )
}
