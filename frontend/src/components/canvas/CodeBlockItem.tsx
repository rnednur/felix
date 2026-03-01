import { lazy, Suspense } from 'react'
import { CodeBlockContent } from '@/types/canvas'
import { Code } from 'lucide-react'

const SqlEditor = lazy(() => import('@/components/editor/SqlEditor').then(m => ({ default: m.SqlEditor })))

interface CodeBlockItemProps {
  content: CodeBlockContent
  itemId?: string
}

export function CodeBlockItem({ content, itemId }: CodeBlockItemProps) {
  const { language, code } = content

  // Serialize config for annotation system
  const felixConfig = itemId ? JSON.stringify({
    language,
    codeLength: code?.length
  }) : undefined

  return (
    <div
      className="h-full flex flex-col bg-white overflow-hidden"
      data-felix-id={itemId}
      data-felix-type="code"
      data-felix-config={felixConfig}
    >
      {/* Header */}
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center gap-2">
        <Code className="h-4 w-4 text-gray-600" />
        <h3 className="text-sm font-semibold text-gray-700 uppercase">{language}</h3>
      </div>

      {/* Code */}
      <div className="flex-1 min-h-0 overflow-hidden">
        {language === 'sql' ? (
          <Suspense fallback={
            <div className="h-full bg-gray-900 p-4">
              <pre className="text-sm text-gray-100 font-mono">{code}</pre>
            </div>
          }>
            <SqlEditor value={code || ''} readOnly height="100%" />
          </Suspense>
        ) : (
          <div className="overflow-auto h-full p-4 bg-gray-900">
            <pre className="text-sm text-gray-100 font-mono">
              <code>{code}</code>
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
