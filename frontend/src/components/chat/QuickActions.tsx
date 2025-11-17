interface QuickActionsProps {
  onSelect: (query: string) => void
  suggestions: string[]
}

export function QuickActions({ onSelect, suggestions }: QuickActionsProps) {
  if (suggestions.length === 0) return null

  return (
    <div className="px-4 pb-2">
      <p className="text-xs text-gray-500 mb-2">Quick actions:</p>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((suggestion, i) => (
          <button
            key={i}
            onClick={() => onSelect(suggestion)}
            className="text-xs px-2 py-1 bg-white border border-gray-200 rounded hover:bg-gray-50 transition-colors"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  )
}
