import { useMemo, useState, useEffect } from 'react'
import { X, ChevronDown, ChevronUp, BarChart2, Maximize2, Sparkles, Cpu, Loader2 } from 'lucide-react'
import { VegaChart } from '@/components/visualization/VegaChart'
import { useVisualizationSuggestions } from '@/hooks/useVisualization'

interface MapChartOverlayProps {
  rows: any[]
  totalRows?: number
  spatialColumns?: { lat?: string; lng?: string; wkt?: string }
  queryId?: string   // When present, AI suggestions are available
  onClose: () => void
}

// ─── Column analysis ──────────────────────────────────────────────────────────

interface ColAnalysis {
  catCols: string[]   // Categorical: 2–25 unique string values
  numCols: string[]   // Numeric: number or parseable-as-number
  dateCols: string[]  // Date-like strings
}

function analyzeColumns(rows: any[], excludeCols: Set<string>): ColAnalysis {
  const catCols: string[] = []
  const numCols: string[] = []
  const dateCols: string[] = []

  if (!rows.length) return { catCols, numCols, dateCols }

  const cols = Object.keys(rows[0]).filter(c => !excludeCols.has(c))

  for (const col of cols) {
    const sample = rows.slice(0, 20).map(r => r[col]).filter(v => v != null)
    if (!sample.length) continue
    const first = sample[0]

    if (typeof first === 'number') {
      numCols.push(col)
    } else if (typeof first === 'string') {
      const trimmed = first.trim()
      if (trimmed !== '' && !isNaN(Number(trimmed))) {
        numCols.push(col)
        continue
      }
      if (/\d{4}/.test(trimmed) && !isNaN(Date.parse(trimmed))) {
        dateCols.push(col)
        continue
      }
      const uniq = new Set(rows.map(r => r[col]).filter(v => v != null))
      if (uniq.size >= 2 && uniq.size <= 25) {
        catCols.push(col)
      }
    }
  }

  return { catCols, numCols, dateCols }
}

// ─── Chart spec generator ─────────────────────────────────────────────────────

function generateSpec(rows: any[], excludeCols: Set<string>, height: number): any | null {
  if (!rows.length) return null

  const { catCols, numCols, dateCols } = analyzeColumns(rows, excludeCols)
  const data = rows.slice(0, 500)

  const base = {
    $schema: 'https://vega.github.io/schema/vega-lite/v6.json',
    data: { values: data },
    width: 'container' as const,
    height,
    autosize: { type: 'fit' as const, contains: 'padding' as const },
    padding: { left: 4, right: 4, top: 2, bottom: 2 },
  }

  // ── 1. Categorical + numeric → horizontal bar ─────────────────────────────
  if (catCols.length >= 1 && numCols.length >= 1) {
    const catCol = catCols[0]
    const numCol = numCols[0]
    const uniqCatCount = new Set(data.map(r => r[catCol])).size
    const alreadyAggregated = uniqCatCount === data.length && data.length <= 25

    return {
      ...base,
      mark: { type: 'bar', cornerRadiusEnd: 3 },
      encoding: {
        y: {
          field: catCol,
          type: 'nominal',
          sort: alreadyAggregated ? undefined : '-x',
          axis: { title: null, labelLimit: 120 },
        },
        x: alreadyAggregated
          ? { field: numCol, type: 'quantitative', axis: { title: numCol.replace(/_/g, ' '), tickCount: 4 } }
          : { aggregate: 'sum', field: numCol, type: 'quantitative', axis: { title: numCol.replace(/_/g, ' '), tickCount: 4 } },
        color: { field: catCol, type: 'nominal', legend: null, scale: { scheme: 'tableau10' } },
        tooltip: [
          { field: catCol, type: 'nominal' },
          alreadyAggregated
            ? { field: numCol, type: 'quantitative' }
            : { aggregate: 'sum', field: numCol, type: 'quantitative', title: numCol },
        ],
      },
    }
  }

  // ── 2. Categorical only → count per category ──────────────────────────────
  if (catCols.length >= 1) {
    const catCol = catCols[0]
    return {
      ...base,
      mark: { type: 'bar', cornerRadiusEnd: 3 },
      encoding: {
        y: { field: catCol, type: 'nominal', sort: '-x', axis: { title: null, labelLimit: 120 } },
        x: { aggregate: 'count', type: 'quantitative', axis: { title: 'Count', tickCount: 4 } },
        color: { field: catCol, type: 'nominal', legend: null, scale: { scheme: 'tableau10' } },
        tooltip: [
          { field: catCol, type: 'nominal' },
          { aggregate: 'count', type: 'quantitative', title: 'Count' },
        ],
      },
    }
  }

  // ── 3. Date + numeric → line chart ────────────────────────────────────────
  if (dateCols.length >= 1 && numCols.length >= 1) {
    const dateCol = dateCols[0]
    const numCol = numCols[0]
    return {
      ...base,
      mark: { type: 'line', point: { size: 30 } },
      encoding: {
        x: { field: dateCol, type: 'temporal', axis: { title: null } },
        y: { field: numCol, type: 'quantitative', axis: { title: numCol.replace(/_/g, ' '), tickCount: 4 } },
        tooltip: [
          { field: dateCol, type: 'temporal' },
          { field: numCol, type: 'quantitative' },
        ],
      },
    }
  }

  // ── 4. Numeric → histogram ────────────────────────────────────────────────
  if (numCols.length >= 1) {
    const numCol = numCols[0]
    return {
      ...base,
      mark: { type: 'bar', cornerRadiusTopLeft: 2, cornerRadiusTopRight: 2 },
      encoding: {
        x: { field: numCol, type: 'quantitative', bin: { maxbins: 15 }, axis: { title: numCol.replace(/_/g, ' ') } },
        y: { aggregate: 'count', type: 'quantitative', axis: { title: 'Count', tickCount: 4 } },
        tooltip: [
          { field: numCol, type: 'quantitative', bin: true },
          { aggregate: 'count', type: 'quantitative', title: 'Count' },
        ],
      },
    }
  }

  return null
}

// ─── Resize a spec to a given height ──────────────────────────────────────────
function resizeSpec(spec: any, height: number): any {
  if (!spec) return spec
  return {
    ...spec,
    height,
    width: 'container',
    autosize: { type: 'fit', contains: 'padding' },
  }
}

// ─── Component ────────────────────────────────────────────────────────────────

export function MapChartOverlay({
  rows,
  totalRows,
  spatialColumns,
  queryId,
  onClose,
}: MapChartOverlayProps) {
  const [minimized, setMinimized] = useState(false)
  const [expanded, setExpanded] = useState(false)
  // Default to AI mode when a queryId is available
  const [useAI, setUseAI] = useState(!!queryId)

  // Sync mode with queryId availability (e.g. when a new query fires)
  useEffect(() => {
    setUseAI(!!queryId)
  }, [queryId])

  const excludeCols = useMemo(() => {
    const base = new Set([
      'id', 'ID', 'uuid', 'UUID', 'created_at', 'updated_at',
      'lat', 'lng', 'latitude', 'longitude', 'LAT', 'LNG', 'LATITUDE', 'LONGITUDE',
    ])
    if (spatialColumns?.lat) base.add(spatialColumns.lat)
    if (spatialColumns?.lng) base.add(spatialColumns.lng)
    if (spatialColumns?.wkt) base.add(spatialColumns.wkt)
    return base
  }, [spatialColumns])

  // Heuristic specs
  const heuristicSpec = useMemo(() => generateSpec(rows, excludeCols, 155), [rows, excludeCols])
  const heuristicExpandedSpec = useMemo(() => generateSpec(rows, excludeCols, 340), [rows, excludeCols])

  // AI-suggested specs
  const { data: aiSuggestions, isLoading: aiLoading } = useVisualizationSuggestions(
    useAI && queryId ? queryId : ''
  )
  const aiSpec = useMemo(() => {
    const first = aiSuggestions?.suggestions?.[0]?.spec
    return first ? resizeSpec(first, 155) : null
  }, [aiSuggestions])
  const aiExpandedSpec = useMemo(() => {
    const first = aiSuggestions?.suggestions?.[0]?.spec
    return first ? resizeSpec(first, 340) : null
  }, [aiSuggestions])

  // Active specs — fall back to heuristic if AI hasn't loaded yet
  const activeSpec = useAI ? (aiSpec ?? heuristicSpec) : heuristicSpec
  const activeExpandedSpec = useAI ? (aiExpandedSpec ?? heuristicExpandedSpec) : heuristicExpandedSpec

  // Escape key closes expanded modal
  useEffect(() => {
    if (!expanded) return
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') setExpanded(false) }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [expanded])

  if (!activeSpec) return null

  const count = totalRows ?? rows.length

  return (
    <>
      {/* ── Compact overlay ── */}
      <div className="absolute top-16 right-3 z-10 w-64 pointer-events-auto">
        <div className="rounded-2xl shadow-xl border border-border bg-card/95 backdrop-blur-md overflow-hidden">
          {/* Header */}
          <div
            className="flex items-center justify-between px-3 py-2 border-b border-border/50 cursor-pointer select-none hover:bg-muted/40 transition-colors"
            onClick={e => { e.stopPropagation(); setMinimized(p => !p) }}
            title={minimized ? 'Expand' : 'Collapse'}
          >
            <div className="flex items-center gap-1.5 min-w-0">
              <BarChart2 className="h-3.5 w-3.5 text-primary flex-shrink-0" />
              <span className="text-xs font-semibold text-foreground truncate">
                {count.toLocaleString()} result{count !== 1 ? 's' : ''}
              </span>
              {useAI && aiLoading && (
                <Loader2 className="h-3 w-3 text-muted-foreground animate-spin flex-shrink-0" />
              )}
            </div>
            <div className="flex items-center gap-0.5 flex-shrink-0">
              {/* AI / Auto toggle — only shown when queryId is available */}
              {queryId && (
                <button
                  onClick={e => { e.stopPropagation(); setUseAI(p => !p) }}
                  title={useAI ? 'Switch to heuristic chart' : 'Switch to AI chart'}
                  className={`flex items-center gap-0.5 px-1.5 py-0.5 rounded-md text-[10px] font-medium transition-colors mr-0.5
                    ${useAI
                      ? 'bg-primary/10 text-primary hover:bg-primary/20'
                      : 'bg-muted text-muted-foreground hover:bg-muted/80'}`}
                >
                  {useAI
                    ? <><Sparkles className="h-2.5 w-2.5" /> AI</>
                    : <><Cpu className="h-2.5 w-2.5" /> Auto</>}
                </button>
              )}
              <span className="p-1 text-muted-foreground">
                {minimized ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronUp className="h-3.5 w-3.5" />}
              </span>
              <button
                onClick={e => { e.stopPropagation(); onClose() }}
                className="p-1 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                title="Close"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          {/* Chart body */}
          {!minimized && (
            <div
              className="h-44 px-1 py-1 overflow-hidden cursor-zoom-in group relative"
              onDoubleClick={e => { e.stopPropagation(); setExpanded(true) }}
            >
              <VegaChart spec={activeSpec} />
              <div className="absolute bottom-1.5 right-1.5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                <div className="bg-card/80 backdrop-blur rounded-md px-1.5 py-0.5 flex items-center gap-1 text-[10px] text-muted-foreground border border-border/50">
                  <Maximize2 className="h-2.5 w-2.5" />
                  double-click to expand
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Expanded modal ── */}
      {expanded && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center pointer-events-auto"
          onClick={() => setExpanded(false)}
        >
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
          <div
            className="relative rounded-2xl shadow-2xl border border-border bg-card w-[680px] max-w-[92vw]"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <div className="flex items-center gap-2">
                <BarChart2 className="h-4 w-4 text-primary" />
                <span className="text-sm font-semibold text-foreground">
                  {count.toLocaleString()} result{count !== 1 ? 's' : ''}
                </span>
                {useAI && aiLoading && <Loader2 className="h-3.5 w-3.5 text-muted-foreground animate-spin" />}
              </div>
              <div className="flex items-center gap-2">
                {queryId && (
                  <button
                    onClick={() => setUseAI(p => !p)}
                    className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium transition-colors
                      ${useAI
                        ? 'bg-primary/10 text-primary hover:bg-primary/20'
                        : 'bg-muted text-muted-foreground hover:bg-muted/80'}`}
                  >
                    {useAI
                      ? <><Sparkles className="h-3 w-3" /> AI chart</>
                      : <><Cpu className="h-3 w-3" /> Auto chart</>}
                  </button>
                )}
                <button
                  onClick={() => setExpanded(false)}
                  className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
                  title="Close (Esc)"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
            <div className="h-[380px] px-2 py-2">
              <VegaChart spec={activeExpandedSpec} />
            </div>
          </div>
        </div>
      )}
    </>
  )
}
