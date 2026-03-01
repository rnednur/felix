import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Sparkles, X, Loader2, ArrowRight } from 'lucide-react'
import { executeNLQuery, type QueryResult } from '@/services/api'

interface MapAIBarProps {
  datasetId: string
  onQueryResult: (result: QueryResult | null) => void
  currentResult: QueryResult | null
  totalRows?: number
  spatialColumns?: { lat: string; lng: string }
}

export function MapAIBar({ datasetId, onQueryResult, currentResult, totalRows, spatialColumns }: MapAIBarProps) {
  const [query, setQuery] = useState('')
  const [lastQuery, setLastQuery] = useState('')

  const nlQuery = useMutation({
    mutationFn: (q: string) => {
      // Always include lat/lng columns in the result so map can plot the points.
      // Only add the hint if we know the actual lat/lng column names.
      const spatialHint = spatialColumns?.lat && spatialColumns?.lng
        ? ` Always include the ${spatialColumns.lat} (latitude) and ${spatialColumns.lng} (longitude) columns in the SELECT clause so results can be plotted on a map.`
        : ''
      return executeNLQuery(q + spatialHint, { datasetId })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = query.trim()
    if (!trimmed || nlQuery.isPending) return
    setLastQuery(trimmed)
    nlQuery.mutate(trimmed, {
      onSuccess: (result) => {
        onQueryResult(result)
        setQuery('')
      },
    })
  }

  const handleClear = () => {
    onQueryResult(null)
    setLastQuery('')
    nlQuery.reset()
  }

  const hasResult = currentResult !== null
  const isError = nlQuery.isError
  const errorMsg = (() => {
    if (!nlQuery.error) return 'Query failed'
    const err = nlQuery.error as any
    return err?.response?.data?.detail ?? (nlQuery.error instanceof Error ? nlQuery.error.message : 'Query failed')
  })()

  const resultCount = currentResult?.rows?.length ?? 0
  const isZeroRows = hasResult && resultCount === 0

  return (
    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 w-full max-w-xl px-4 pointer-events-none">
      <div
        className={`pointer-events-auto rounded-2xl shadow-xl border bg-card/95 backdrop-blur-md transition-colors
                    ${isError ? 'border-destructive/50' : 'border-border'}`}
      >
        {/* Result chip */}
        {hasResult && (
          <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border/50 text-sm">
            <span className={`font-semibold flex-shrink-0 ${isZeroRows ? 'text-amber-600 dark:text-amber-400' : 'text-foreground'}`}>
              {isZeroRows
                ? 'No results'
                : `${resultCount.toLocaleString()}${totalRows ? ` of ${totalRows.toLocaleString()}` : ''} rows`}
            </span>
            <span className="text-muted-foreground flex-shrink-0">·</span>
            <span className="text-muted-foreground italic truncate min-w-0">
              &ldquo;{lastQuery}&rdquo;
            </span>
            <button
              onClick={handleClear}
              className="ml-auto flex-shrink-0 p-1 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Clear map filter"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Input row */}
        <form onSubmit={handleSubmit} className="flex items-center gap-3 px-4 py-3">
          <Sparkles className="h-4 w-4 text-primary flex-shrink-0" />
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder={
              hasResult
                ? 'Ask another question…'
                : 'Ask about this map… e.g. Show only earthquakes in Asia'
            }
            disabled={nlQuery.isPending}
            className="flex-1 bg-transparent text-sm placeholder:text-muted-foreground focus:outline-none text-foreground disabled:opacity-50 min-w-0"
          />
          <button
            type="submit"
            disabled={!query.trim() || nlQuery.isPending}
            className="flex-shrink-0 rounded-xl bg-primary text-primary-foreground px-3 py-1.5 text-sm font-medium
                       hover:bg-primary/90 disabled:opacity-40 transition-colors flex items-center justify-center"
            aria-label="Run AI map query"
          >
            {nlQuery.isPending
              ? <Loader2 className="h-4 w-4 animate-spin" />
              : <ArrowRight className="h-4 w-4" />
            }
          </button>
        </form>
      </div>

      {/* Error pill */}
      {isError && (
        <div className="mt-2 px-3 py-1.5 bg-destructive/10 border border-destructive/20 rounded-xl text-destructive text-xs">
          {errorMsg}
        </div>
      )}
    </div>
  )
}
