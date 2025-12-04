import { InsightNoteContent } from '@/types/canvas'
import ReactMarkdown from 'react-markdown'
import { Lightbulb } from 'lucide-react'

interface InsightNoteItemProps {
  content: InsightNoteContent
}

export function InsightNoteItem({ content }: InsightNoteItemProps) {
  const { content: markdownContent, aiGenerated, tags } = content

  // Check if this is a query header
  const isQueryHeader = tags?.includes('query-header')

  return (
    <div className={`h-full flex flex-col overflow-hidden ${
      isQueryHeader
        ? 'bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-300 shadow-lg'
        : 'bg-yellow-50 border-l-4 border-yellow-400'
    }`}>
      {/* Header */}
      {!isQueryHeader && (
        <div className="bg-yellow-100 px-4 py-3 border-b border-yellow-200 flex items-center gap-2">
          <Lightbulb className="h-4 w-4 text-yellow-700" />
          <h3 className="text-sm font-semibold text-yellow-900">
            {aiGenerated ? 'AI Insight' : 'Note'}
          </h3>
          {tags && tags.length > 0 && (
            <div className="flex gap-1 ml-auto">
              {tags.map((tag, i) => (
                <span
                  key={i}
                  className="px-2 py-1 text-xs bg-yellow-200 text-yellow-800 rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Content */}
      <div className={`flex-1 overflow-auto ${isQueryHeader ? 'p-6' : 'p-4'}`}>
        <div className={`prose max-w-none ${
          isQueryHeader ? 'prose-lg prose-blue' : 'prose-sm prose-yellow'
        }`}>
          <ReactMarkdown>{markdownContent}</ReactMarkdown>
        </div>
      </div>
    </div>
  )
}
