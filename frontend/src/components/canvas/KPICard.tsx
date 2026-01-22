import { KPICardContent } from '@/types/canvas'
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Trophy,
  CheckCircle2,
  Target,
  DollarSign,
  Hash,
  BarChart3,
  Users,
  Clock,
  Percent
} from 'lucide-react'

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

  // Get contextual icon based on metric name
  const getMetricIcon = () => {
    const nameLower = name.toLowerCase()

    if (nameLower.includes('score') || nameLower.includes('average') || nameLower.includes('highest') || nameLower.includes('best')) {
      return Trophy
    }
    if (nameLower.includes('completion') || nameLower.includes('complete') || nameLower.includes('success')) {
      return CheckCircle2
    }
    if (nameLower.includes('attendance') || nameLower.includes('participation') || nameLower.includes('rate')) {
      return Target
    }
    if (nameLower.includes('revenue') || nameLower.includes('sales') || nameLower.includes('$') || nameLower.includes('cost') || nameLower.includes('price')) {
      return DollarSign
    }
    if (nameLower.includes('count') || nameLower.includes('total') || nameLower.includes('number')) {
      return Hash
    }
    if (nameLower.includes('user') || nameLower.includes('customer') || nameLower.includes('student') || nameLower.includes('employee')) {
      return Users
    }
    if (nameLower.includes('time') || nameLower.includes('duration') || nameLower.includes('hours')) {
      return Clock
    }
    if (nameLower.includes('%') || nameLower.includes('percent')) {
      return Percent
    }
    return BarChart3
  }

  // Get value color based on value type
  const getValueColor = () => {
    const value = formattedValue.toString()

    if (value.includes('%')) {
      return 'text-indigo-600'
    }
    if (value.includes('$') || value.includes('€') || value.includes('£')) {
      return 'text-emerald-600'
    }
    return 'text-violet-600'
  }

  // Get icon background color (subtle, matching value color)
  const getIconBgColor = () => {
    const value = formattedValue.toString()

    if (value.includes('%')) {
      return 'bg-indigo-100 text-indigo-600'
    }
    if (value.includes('$') || value.includes('€') || value.includes('£')) {
      return 'bg-emerald-100 text-emerald-600'
    }
    return 'bg-violet-100 text-violet-600'
  }

  const getTrendIcon = () => {
    if (!trendDirection) return null

    switch (trendDirection) {
      case 'up':
        return <TrendingUp className="h-3.5 w-3.5" />
      case 'down':
        return <TrendingDown className="h-3.5 w-3.5" />
      case 'flat':
        return <Minus className="h-3.5 w-3.5" />
      default:
        return null
    }
  }

  const getTrendColor = () => {
    if (!trendDirection) return 'text-muted-foreground'

    switch (trendDirection) {
      case 'up':
        return 'text-emerald-600'
      case 'down':
        return 'text-rose-600'
      case 'flat':
        return 'text-slate-500'
      default:
        return 'text-slate-500'
    }
  }

  const getTrendBgColor = () => {
    if (!trendDirection) return 'bg-slate-100'

    switch (trendDirection) {
      case 'up':
        return 'bg-emerald-50'
      case 'down':
        return 'bg-rose-50'
      case 'flat':
        return 'bg-slate-100'
      default:
        return 'bg-slate-100'
    }
  }

  const MetricIcon = getMetricIcon()

  return (
    <div className="h-full flex flex-col bg-card rounded-xl border border-border/50 p-5 shadow-[0_2px_8px_-2px_rgba(0,0,0,0.05),0_4px_12px_-4px_rgba(0,0,0,0.05)] hover:shadow-[0_4px_12px_-2px_rgba(0,0,0,0.08),0_8px_20px_-4px_rgba(0,0,0,0.06)] transition-all duration-200">
      {/* Header with icon */}
      <div className="flex items-start justify-between mb-3">
        <span className="text-sm font-medium text-muted-foreground tracking-wide">
          {name}
        </span>
        <div className={`p-2 rounded-lg ${getIconBgColor()}`}>
          <MetricIcon className="h-4 w-4" />
        </div>
      </div>

      {/* Value */}
      <div className="flex-1 flex items-center">
        <span className={`text-4xl font-bold tracking-tight ${getValueColor()}`}>
          {formattedValue}
        </span>
      </div>

      {/* Trend */}
      {trend !== undefined && trend !== null && (
        <div className="mt-4 flex items-center gap-2">
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${getTrendColor()} ${getTrendBgColor()}`}
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
