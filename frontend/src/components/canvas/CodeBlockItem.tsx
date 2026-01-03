import { CodeBlockContent } from '@/types/canvas'
import { Code } from 'lucide-react'

interface CodeBlockItemProps {
  content: CodeBlockContent
}

export function CodeBlockItem({ content }: CodeBlockItemProps) {
  const { language, code } = content

  return (
    <div className="h-full flex flex-col bg-white overflow-hidden">
      {/* Header */}
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-2">
        <Code className="h-4 w-4 text-gray-600" />
        <h3 className="text-sm font-semibold text-gray-700 uppercase">{language}</h3>
      </div>

      {/* Code */}
      <div className="flex-1 overflow-auto p-4 bg-gray-900">
        <pre className="text-sm text-gray-100 font-mono">
          <code>{code}</code>
        </pre>
      </div>
    </div>
  )
}
