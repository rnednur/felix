import { cn } from "@/lib/utils"
import { BarChart3, Table2, Lightbulb, Gauge, FileText } from "lucide-react"

type BadgeVariant = "kpi" | "chart" | "table" | "insight" | "text"

interface CardBadgeProps {
  variant: BadgeVariant
  label?: string
  className?: string
}

const variantConfig: Record<BadgeVariant, { icon: typeof BarChart3; bg: string; text: string; defaultLabel: string }> = {
  kpi: {
    icon: Gauge,
    bg: "bg-violet-100",
    text: "text-violet-700",
    defaultLabel: "KPI"
  },
  chart: {
    icon: BarChart3,
    bg: "bg-indigo-100",
    text: "text-indigo-700",
    defaultLabel: "Chart"
  },
  table: {
    icon: Table2,
    bg: "bg-slate-100",
    text: "text-slate-700",
    defaultLabel: "Table"
  },
  insight: {
    icon: Lightbulb,
    bg: "bg-amber-100",
    text: "text-amber-700",
    defaultLabel: "Insight"
  },
  text: {
    icon: FileText,
    bg: "bg-emerald-100",
    text: "text-emerald-700",
    defaultLabel: "Text"
  }
}

export function CardBadge({ variant, label, className }: CardBadgeProps) {
  const config = variantConfig[variant]
  const Icon = config.icon

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider",
        config.bg,
        config.text,
        className
      )}
    >
      <Icon className="h-3 w-3" />
      {label || config.defaultLabel}
    </span>
  )
}
