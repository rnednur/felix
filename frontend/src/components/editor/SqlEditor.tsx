import { useRef, useCallback, useEffect } from 'react'
import Editor, { OnMount } from '@monaco-editor/react'
import { Play, WrapText } from 'lucide-react'

export interface SqlEditorSchema {
  tableName: string
  columns: { name: string; type: string }[]
}

interface SqlEditorProps {
  value: string
  onChange?: (value: string) => void
  onRun?: (sql: string) => void
  readOnly?: boolean
  height?: string
  schema?: SqlEditorSchema
  /** Show run button and keyboard shortcut hint */
  showControls?: boolean
}

export function SqlEditor({
  value,
  onChange,
  onRun,
  readOnly = false,
  height = '200px',
  schema,
  showControls = false,
}: SqlEditorProps) {
  const editorRef = useRef<any>(null)
  const monacoRef = useRef<any>(null)
  const completionDisposableRef = useRef<any>(null)

  const handleRun = useCallback(() => {
    const currentValue = editorRef.current?.getValue() ?? value
    if (onRun && currentValue.trim()) {
      onRun(currentValue)
    }
  }, [onRun, value])

  // Register schema-aware completion provider whenever schema changes
  const registerCompletions = useCallback((monaco: any) => {
    // Dispose previous provider if any
    completionDisposableRef.current?.dispose()

    if (!schema) return

    const { tableName, columns } = schema

    completionDisposableRef.current = monaco.languages.registerCompletionItemProvider('sql', {
      provideCompletionItems: (model: any, position: any) => {
        const word = model.getWordUntilPosition(position)
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn,
        }

        const suggestions = [
          // Table name suggestion
          {
            label: tableName,
            kind: monaco.languages.CompletionItemKind.Class,
            insertText: tableName,
            detail: 'Table',
            range,
          },
          // Column suggestions
          ...columns.map(col => ({
            label: col.name,
            kind: monaco.languages.CompletionItemKind.Field,
            insertText: col.name,
            detail: col.type,
            documentation: `${tableName}.${col.name} (${col.type})`,
            range,
          })),
          // Common SQL keywords
          ...['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT',
            'JOIN', 'LEFT JOIN', 'INNER JOIN', 'ON', 'AND', 'OR', 'NOT', 'IN',
            'LIKE', 'IS NULL', 'IS NOT NULL', 'COUNT(*)', 'SUM', 'AVG', 'MIN', 'MAX',
            'DISTINCT', 'AS', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END'].map(kw => ({
            label: kw,
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: kw,
            range,
          })),
        ]

        return { suggestions }
      },
    })
  }, [schema])

  const handleEditorMount: OnMount = useCallback((editor, monaco) => {
    editorRef.current = editor
    monacoRef.current = monaco

    // Cmd+Enter / Ctrl+Enter to run
    editor.addCommand(
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter,
      () => {
        const currentValue = editor.getValue()
        if (onRun && currentValue.trim()) {
          onRun(currentValue)
        }
      }
    )

    registerCompletions(monaco)
  }, [onRun, registerCompletions])

  // Re-register completions when schema changes
  useEffect(() => {
    if (monacoRef.current) {
      registerCompletions(monacoRef.current)
    }
    return () => {
      completionDisposableRef.current?.dispose()
    }
  }, [registerCompletions])

  return (
    <div className="flex flex-col overflow-hidden rounded-lg border border-gray-700" style={{ height }}>
      {/* Editor */}
      <div className="flex-1 min-h-0">
        <Editor
          defaultLanguage="sql"
          value={value}
          onChange={(v) => onChange?.(v ?? '')}
          theme="vs-dark"
          onMount={handleEditorMount}
          options={{
            readOnly,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 13,
            lineHeight: 20,
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
            padding: { top: 8, bottom: 8 },
            wordWrap: 'on',
            renderLineHighlight: readOnly ? 'none' : 'line',
            cursorStyle: readOnly ? 'line-thin' : 'line',
            selectionHighlight: !readOnly,
            occurrencesHighlight: readOnly ? 'off' : 'singleFile',
            overviewRulerBorder: false,
            hideCursorInOverviewRuler: true,
            scrollbar: {
              verticalScrollbarSize: 6,
              horizontalScrollbarSize: 6,
            },
            lineNumbers: readOnly ? 'off' : 'on',
            glyphMargin: false,
            folding: false,
            renderValidationDecorations: 'off',
          }}
        />
      </div>

      {/* Controls bar (only in editable mode with showControls) */}
      {showControls && !readOnly && (
        <div className="flex items-center justify-between px-3 py-1.5 bg-gray-900 border-t border-gray-700">
          <span className="text-xs text-gray-500">
            {navigator.platform.includes('Mac') ? '⌘' : 'Ctrl'}+Enter to run
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => editorRef.current?.getAction('editor.action.formatDocument')?.run()}
              className="flex items-center gap-1 px-2 py-1 text-xs text-gray-400 hover:text-gray-200 hover:bg-gray-700 rounded transition-colors"
              title="Format SQL"
            >
              <WrapText className="h-3 w-3" />
              Format
            </button>
            {onRun && (
              <button
                onClick={handleRun}
                className="flex items-center gap-1 px-2.5 py-1 text-xs bg-emerald-600 hover:bg-emerald-500 text-white rounded transition-colors font-medium"
              >
                <Play className="h-3 w-3" />
                Run
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
