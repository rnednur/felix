import { KPICardContent } from '@/types/canvas'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface KPICardProps {
  content: KPICardContent
}

export function KPICard({ content }: KPICardProps) {
  const {
    name,
    formattedValue,
    trend,
    trendDirection,
    comparisonLabel,
  } = content

  const getTrendIcon = () => {
    if (!trendDirection) return null

    switch (trendDirection) {
      case 'up':
        return <TrendingUp className="h-4 w-4" />
      case 'down':
        return <TrendingDown className="h-4 w-4" />
      case 'flat':
        return <Minus className="h-4 w-4" />
      default:
        return null
    }
  }

  const getTrendColor = () => {
    if (!trendDirection) return 'text-muted-foreground'

    switch (trendDirection) {
      case 'up':
        return 'text-success'
      case 'down':
        return 'text-destructive'
      case 'flat':
        return 'text-muted-foreground'
      default:
        return 'text-muted-foreground'
    }
  }

  const getTrendBgColor = () => {
    if (!trendDirection) return 'bg-muted/50'

    switch (trendDirection) {
      case 'up':
        return 'bg-success/10'
      case 'down':
        return 'bg-destructive/10'
      case 'flat':
        return 'bg-muted/50'
      default:
        return 'bg-muted/50'
    }
  }

  return (
    <div className="h-full flex flex-col bg-card rounded-lg border border-border p-4 hover:shadow-md transition-shadow">
      {/* Label */}
      <div className="mb-2">
        <span className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
          {name}
        </span>
      </div>

      {/* Value */}
      <div className="flex-1 flex items-center">
        <span className="text-3xl font-bold text-foreground tracking-tight">
          {formattedValue}
        </span>
      </div>

      {/* Trend */}
      {trend !== undefined && trend !== null && (
        <div className="mt-3 flex items-center gap-2">
          <span
            className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getTrendColor()} ${getTrendBgColor()}`}
          >
            {getTrendIcon()}
            <span>
              {trend > 0 ? '+' : ''}
              {trend.toFixed(1)}%
            </span>
          </span>
          {comparisonLabel && (
            <span className="text-xs text-muted-foreground">
              {comparisonLabel}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
