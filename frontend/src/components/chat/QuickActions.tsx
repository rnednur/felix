import { cn } from '@/lib/utils'
import { Zap } from 'lucide-react'

interface QuickActionsProps {
  onSelect: (query: string) => void
  suggestions: string[]
}

export function QuickActions({ onSelect, suggestions }: QuickActionsProps) {
  if (suggestions.length === 0) return null

  return (
    <div className="flex-shrink-0 px-4 py-3 bg-background-subtle border-t border-border">
      <div className="flex items-center gap-2 mb-2">
        <Zap className="h-3 w-3 text-primary" />
        <span className="text-xs font-medium text-muted-foreground">Quick actions</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((suggestion, i) => (
          <button
            key={i}
            onClick={() => onSelect(suggestion)}
            className={cn(
              'text-xs px-3 py-1.5',
              'bg-card border border-border rounded-full',
              'text-foreground',
              'hover:bg-muted hover:border-border-strong',
              'transition-all duration-150',
              'shadow-xs hover:shadow-sm'
            )}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  )
}
