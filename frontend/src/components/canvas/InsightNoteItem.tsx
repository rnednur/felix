import { InsightNoteContent } from '@/types/canvas'
import ReactMarkdown from 'react-markdown'
import { Lightbulb, Sparkles } from 'lucide-react'
import { CardBadge } from '@/components/ui/card-badge'

interface InsightNoteItemProps {
  content: InsightNoteContent
  variant?: 'default' | 'dashboard'
  itemId?: string
}

export function InsightNoteItem({ content, variant = 'default', itemId }: InsightNoteItemProps) {
  const { content: markdownContent, aiGenerated, tags } = content

  // Check if this is a query header
  const isQueryHeader = tags?.includes('query-header')

  // Use dashboard variant for cleaner look
  const useDashboardStyle = variant === 'dashboard' || tags?.includes('key-insights')

  // Serialize config for annotation system - include content for LLM to modify
  const felixConfig = itemId ? JSON.stringify({
    content: markdownContent,  // Include actual content for LLM modifications
    aiGenerated,
    tags,
    isHeader: isQueryHeader,
    variant: useDashboardStyle ? 'dashboard' : 'default'
  }) : undefined

  if (isQueryHeader) {
    return (
      <div
        className="h-full flex flex-col overflow-hidden bg-gradient-to-r from-indigo-50 to-violet-50 border border-indigo-200 rounded-xl shadow-sm"
        data-felix-id={itemId}
        data-felix-type="insight"
        data-felix-config={felixConfig}
      >
        <div className="flex-1 overflow-auto p-6">
          <div className="prose prose-lg prose-indigo max-w-none">
            <ReactMarkdown>{markdownContent}</ReactMarkdown>
          </div>
        </div>
      </div>
    )
  }

  if (useDashboardStyle) {
    // Clean dashboard-style insights panel (like Bricks "Key Insights")
    return (
      <div
        className="h-full flex flex-col bg-card rounded-xl border border-border/50 overflow-hidden shadow-[0_2px_8px_-2px_rgba(0,0,0,0.05),0_4px_12px_-4px_rgba(0,0,0,0.05)]"
        data-felix-id={itemId}
        data-felix-type="insight"
        data-felix-config={felixConfig}
      >
        {/* Header */}
        <div className="px-5 py-4 flex items-center gap-3 border-b border-border/30">
          <CardBadge variant="insight" />
          <h3 className="text-base font-semibold text-foreground font-display">
            Key Insights
          </h3>
          {aiGenerated && (
            <span className="ml-auto inline-flex items-center gap-1 text-xs text-muted-foreground">
              <Sparkles className="h-3 w-3" />
              AI Generated
            </span>
          )}
        </div>

        {/* Content with clean bullet styling */}
        <div className="flex-1 overflow-auto p-5 bg-white">
          <div className="prose prose-sm max-w-none prose-ul:my-0 prose-li:my-1 prose-li:marker:text-indigo-400">
            <ReactMarkdown
              components={{
                ul: ({ children }) => (
                  <ul className="space-y-2 list-none pl-0">
                    {children}
                  </ul>
                ),
                li: ({ children }) => (
                  <li className="flex items-start gap-2 text-slate-700">
                    <span className="mt-2 h-1.5 w-1.5 rounded-full bg-indigo-400 flex-shrink-0" />
                    <span>{children}</span>
                  </li>
                ),
                p: ({ children }) => (
                  <p className="text-slate-700 leading-relaxed">{children}</p>
                ),
              }}
            >
              {markdownContent}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    )
  }

  // Default note style with accent border
  return (
    <div
      className="h-full flex flex-col overflow-hidden bg-card rounded-xl border-l-4 border-l-amber-400 border border-border/50 shadow-sm"
      data-felix-id={itemId}
      data-felix-type="insight"
      data-felix-config={felixConfig}
    >
      {/* Header */}
      <div className="bg-amber-50/50 px-4 py-3 border-b border-amber-100 flex items-center gap-2">
        <Lightbulb className="h-4 w-4 text-amber-600" />
        <h3 className="text-sm font-semibold text-amber-900">
          {aiGenerated ? 'AI Insight' : 'Note'}
        </h3>
        {tags && tags.length > 0 && (
          <div className="flex gap-1 ml-auto">
            {tags.filter(t => t !== 'key-insights').map((tag, i) => (
              <span
                key={i}
                className="px-2 py-0.5 text-[10px] bg-amber-100 text-amber-700 rounded font-medium uppercase tracking-wide"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4 bg-white">
        <div className="prose prose-sm max-w-none prose-amber">
          <ReactMarkdown>{markdownContent}</ReactMarkdown>
        </div>
      </div>
    </div>
  )
}
