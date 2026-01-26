import { KPICardContent } from '@/types/canvas'
import { useTheme } from '@/contexts/ThemeContext'
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
  itemId?: string
}

export function KPICard({ content, itemId }: KPICardProps) {
  const { persona } = useTheme()
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

  // Trend colors - semantic (green=good, red=bad) but adjusted for dark themes
  const getTrendStyles = () => {
    if (!trendDirection) return { color: persona.textMuted, bg: persona.isDark ? '#374151' : '#f1f5f9' }

    switch (trendDirection) {
      case 'up':
        return {
          color: persona.isDark ? '#34d399' : '#059669',
          bg: persona.isDark ? 'rgba(16, 185, 129, 0.15)' : '#ecfdf5'
        }
      case 'down':
        return {
          color: persona.isDark ? '#fb7185' : '#dc2626',
          bg: persona.isDark ? 'rgba(244, 63, 94, 0.15)' : '#fef2f2'
        }
      case 'flat':
        return {
          color: persona.textMuted,
          bg: persona.isDark ? '#374151' : '#f1f5f9'
        }
      default:
        return { color: persona.textMuted, bg: persona.isDark ? '#374151' : '#f1f5f9' }
    }
  }

  const MetricIcon = getMetricIcon()
  const trendStyles = getTrendStyles()

  // Icon background - subtle tint of primary color
  const iconBgColor = persona.isDark
    ? `${persona.primary}25`
    : `${persona.primary}15`

  // Serialize config for annotation system - include all KPI properties
  const felixConfig = itemId ? JSON.stringify({
    name,
    value: content.value,
    formattedValue,
    aggregation: content.aggregation,
    trend,
    trendDirection,
    comparisonLabel,
    column: content.column
  }) : undefined

  return (
    <div
      className="h-full flex flex-col rounded-xl p-5 transition-all duration-200"
      data-felix-id={itemId}
      data-felix-type="kpi"
      data-felix-config={felixConfig}
      style={{
        backgroundColor: persona.cardBackground,
        borderWidth: '1px',
        borderStyle: 'solid',
        borderColor: persona.cardBorder,
        boxShadow: persona.isDark
          ? '0 2px 8px -2px rgba(0,0,0,0.3), 0 4px 12px -4px rgba(0,0,0,0.2)'
          : '0 2px 8px -2px rgba(0,0,0,0.05), 0 4px 12px -4px rgba(0,0,0,0.05)'
      }}
    >
      {/* Header with icon */}
      <div className="flex items-start justify-between mb-3">
        <span
          className="text-sm font-medium tracking-wide"
          style={{ color: persona.textSecondary }}
        >
          {name}
        </span>
        <div
          className="p-2 rounded-lg"
          style={{
            backgroundColor: iconBgColor,
            color: persona.primary
          }}
        >
          <MetricIcon className="h-4 w-4" />
        </div>
      </div>

      {/* Value */}
      <div className="flex-1 flex items-center">
        <span
          className="text-4xl font-bold tracking-tight"
          style={{ color: persona.kpiValueColor }}
        >
          {formattedValue}
        </span>
      </div>

      {/* Trend */}
      {trend !== undefined && trend !== null && (
        <div className="mt-4 flex items-center gap-2">
          <span
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold"
            style={{
              color: trendStyles.color,
              backgroundColor: trendStyles.bg
            }}
          >
            {getTrendIcon()}
            <span>
              {trend > 0 ? '+' : ''}
              {trend.toFixed(1)}%
            </span>
          </span>
          {comparisonLabel && (
            <span
              className="text-xs"
              style={{ color: persona.textMuted }}
            >
              {comparisonLabel}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
