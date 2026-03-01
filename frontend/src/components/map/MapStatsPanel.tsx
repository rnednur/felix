import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { X, BarChart2 } from 'lucide-react'
import { describeDataset } from '@/services/api'

interface MapStatsPanelProps {
  datasetId: string
  data: any[]
  spatialColumns: { lat?: string; lng?: string; wkt?: string }
  onClose: () => void
}

interface NumericStats {
  min: number | null
  max: number | null
  mean: number | null
  median: number | null
  std: number | null
}

interface TopValue {
  value: string
  count: number
  pct: number
}

interface ColumnAnalysis {
  name: string
  type: string
  missing_count: number
  missing_pct: number
  unique_count: number
  cardinality: 'low' | 'medium' | 'high'
  numeric_stats?: NumericStats
  top_values?: TopValue[]
}

interface Bucket {
  binStart: number
  binEnd: number
  count: number
  heightPct: number
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function computeHistogram(values: number[], bins = 15): Bucket[] {
  if (!values || values.length === 0) return []
  const min = Math.min(...values)
  const max = Math.max(...values)
  if (min === max) {
    return [{ binStart: min, binEnd: max, count: values.length, heightPct: 100 }]
  }
  const binWidth = (max - min) / bins
  const counts = Array(bins).fill(0)
  for (const v of values) {
    const idx = Math.min(Math.floor((v - min) / binWidth), bins - 1)
    counts[idx]++
  }
  const maxCount = Math.max(...counts)
  return counts.map((count, i) => ({
    binStart: min + i * binWidth,
    binEnd: min + (i + 1) * binWidth,
    count,
    heightPct: maxCount > 0 ? (count / maxCount) * 100 : 0,
  }))
}

function formatNumber(n: number | null | undefined): string {
  if (n == null) return '—'
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  if (Number.isInteger(n)) return n.toLocaleString()
  return n.toFixed(2)
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function MiniHistogram({ buckets }: { buckets: Bucket[] }) {
  if (!buckets || buckets.length === 0) return null
  return (
    <div className="flex items-end gap-px h-8" style={{ minHeight: 32 }}>
      {buckets.map((b, i) => (
        <div
          key={i}
          className="flex-1 rounded-sm group/bar relative"
          style={{
            height: `${Math.max(b.heightPct, 2)}%`,
            backgroundColor: b.heightPct > 90 ? '#6366f1' : 'rgba(99, 102, 241, 0.55)',
            transition: 'background-color 0.1s',
          }}
          title={`${formatNumber(b.binStart)} – ${formatNumber(b.binEnd)}: ${b.count.toLocaleString()}`}
        />
      ))}
    </div>
  )
}

function CategoryBar({ label, pct, count }: { label: string; pct: number; count: number }) {
  return (
    <div className="flex items-center gap-2 text-[10px]" title={`${label}: ${count.toLocaleString()} (${pct.toFixed(1)}%)`}>
      <span className="text-muted-foreground truncate" style={{ minWidth: 0, flex: '0 0 80px', maxWidth: 80 }}>
        {label}
      </span>
      <div className="flex-1 bg-muted/40 rounded-full h-1.5 overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: 'rgba(99, 102, 241, 0.65)' }}
        />
      </div>
      <span className="text-muted-foreground flex-shrink-0">{pct.toFixed(0)}%</span>
    </div>
  )
}

function SkeletonCard() {
  return (
    <div className="border-b border-border/50 py-3 px-4 animate-pulse">
      <div className="flex items-center justify-between mb-2">
        <div className="h-3 bg-muted rounded w-24" />
        <div className="h-3 bg-muted rounded w-10" />
      </div>
      <div className="h-8 bg-muted/60 rounded mb-1" />
      <div className="flex justify-between">
        <div className="h-2 bg-muted/40 rounded w-8" />
        <div className="h-2 bg-muted/40 rounded w-12" />
        <div className="h-2 bg-muted/40 rounded w-8" />
      </div>
    </div>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

export function MapStatsPanel({ datasetId, data, spatialColumns, onClose }: MapStatsPanelProps) {
  const { data: describe, isLoading } = useQuery({
    queryKey: ['map-describe', datasetId],
    queryFn: () => describeDataset(datasetId),
    enabled: !!datasetId,
    staleTime: 5 * 60 * 1000,
  })

  const spatialSet = useMemo(() => {
    const cols = [spatialColumns.lat, spatialColumns.lng, spatialColumns.wkt].filter(Boolean) as string[]
    return new Set([...cols, ...cols.map(c => c.toLowerCase())])
  }, [spatialColumns])

  const columns: ColumnAnalysis[] = useMemo(() => {
    if (!describe?.analysis?.columns_analysis) return []
    return describe.analysis.columns_analysis
      .filter((col: ColumnAnalysis) => !spatialSet.has(col.name) && !spatialSet.has(col.name.toLowerCase()))
      .slice(0, 12)
  }, [describe, spatialSet])

  // Pre-compute histograms from in-memory data prop for all numeric columns
  const histograms = useMemo(() => {
    const result: Record<string, Bucket[]> = {}
    for (const col of columns) {
      if (col.numeric_stats) {
        const values = data
          .map(row => parseFloat(row[col.name]))
          .filter(v => !isNaN(v))
        result[col.name] = computeHistogram(values, 15)
      }
    }
    return result
  }, [columns, data])

  const overview = describe?.analysis?.overview
  const rowCount: number | undefined = overview?.total_rows
  const colCount: number | undefined = overview?.total_columns

  return (
    <div className="absolute right-0 top-0 h-full w-80 bg-card border-l border-border z-10 flex flex-col shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border flex-shrink-0">
        <div className="flex items-center gap-2">
          <BarChart2 className="h-4 w-4 text-primary" />
          <span className="font-semibold text-foreground text-sm">Dataset Stats</span>
        </div>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Summary row */}
      {!isLoading && rowCount != null && (
        <div className="px-4 py-2.5 border-b border-border/50 bg-muted/20 flex-shrink-0">
          <span className="text-xs text-muted-foreground">
            <span className="font-semibold text-foreground">{rowCount.toLocaleString()}</span> rows
            {colCount != null && (
              <> · <span className="font-semibold text-foreground">{colCount}</span> columns</>
            )}
          </span>
        </div>
      )}
      {isLoading && (
        <div className="px-4 py-2.5 border-b border-border/50 bg-muted/20 flex-shrink-0">
          <div className="h-3 bg-muted rounded w-32 animate-pulse" />
        </div>
      )}

      {/* Column list */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        ) : columns.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-muted-foreground text-sm">
            No column data available
          </div>
        ) : (
          columns.map(col => (
            <div key={col.name} className="border-b border-border/50 py-3 px-4">
              {/* Column header */}
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-medium text-foreground truncate mr-2">{col.name}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-mono flex-shrink-0">
                  {col.type}
                </span>
              </div>

              {/* Numeric: mini histogram + stats row */}
              {col.numeric_stats && histograms[col.name] && (
                <>
                  <MiniHistogram buckets={histograms[col.name]} />
                  <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
                    <span>{formatNumber(col.numeric_stats.min)}</span>
                    <span>avg {formatNumber(col.numeric_stats.mean)}</span>
                    <span>{formatNumber(col.numeric_stats.max)}</span>
                  </div>
                </>
              )}

              {/* Categorical: top values bars */}
              {col.top_values && col.top_values.length > 0 && (
                <div className="space-y-1 mt-1">
                  {col.top_values.slice(0, 5).map(tv => (
                    <CategoryBar key={tv.value} label={tv.value} pct={tv.pct} count={tv.count} />
                  ))}
                </div>
              )}

              {/* Missing data indicator */}
              {col.missing_pct > 0 && (
                <div className="mt-1.5 text-[10px] text-muted-foreground/70">
                  {col.missing_pct.toFixed(1)}% missing
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
