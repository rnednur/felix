import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { X, Play, AlertTriangle, Code2, Clock } from 'lucide-react'
import { PythonAnalysisResult } from '@/services/api'

interface CodePreviewModalProps {
  isOpen: boolean
  onClose: () => void
  analysisResult: PythonAnalysisResult
  onExecute: () => void
  isExecuting?: boolean
}

export function CodePreviewModal({
  isOpen,
  onClose,
  analysisResult,
  onExecute,
  isExecuting = false
}: CodePreviewModalProps) {
  const [showFullCode, setShowFullCode] = useState(false)

  if (!isOpen) return null

  const { generated_code, mode, steps, estimated_runtime, requires_review, safety_warnings } = analysisResult

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Execution Status Bar */}
        {isExecuting && (
          <div className="bg-blue-50 border-b border-blue-200 px-4 py-2 flex items-center gap-2">
            <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-blue-800 font-medium">Executing code... This may take up to 2 minutes</span>
          </div>
        )}

        {/* Header */}
        <div className="border-b border-gray-200 p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Code2 className="h-5 w-5 text-blue-600" />
            <div>
              <h2 className="text-lg font-semibold">Generated Python Code</h2>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                  {mode.toUpperCase()} Mode
                </span>
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {estimated_runtime}
                </span>
              </div>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Safety Warnings */}
        {requires_review && safety_warnings && safety_warnings.length > 0 && (
          <div className="bg-yellow-50 border-b border-yellow-200 p-4">
            <div className="flex gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-yellow-800">Safety Review Required</p>
                <ul className="mt-2 text-sm text-yellow-700 space-y-1">
                  {safety_warnings.map((warning, i) => (
                    <li key={i}>• {warning}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Workflow Steps */}
        {steps && steps.length > 1 && (
          <div className="border-b border-gray-200 p-4 bg-gray-50">
            <p className="text-sm font-medium text-gray-700 mb-2">Workflow Steps:</p>
            <div className="space-y-1">
              {steps.map((step, i) => (
                <div key={i} className="text-sm text-gray-600 flex items-start gap-2">
                  <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs font-medium">
                    {step.step}
                  </span>
                  <span>{step.description}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Code Content */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="bg-gray-900 rounded-lg overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2 bg-gray-800">
              <span className="text-xs text-gray-400">Python</span>
              <button
                onClick={() => setShowFullCode(!showFullCode)}
                className="text-xs text-blue-400 hover:text-blue-300"
              >
                {showFullCode ? 'Show Less' : 'Show Full Code'}
              </button>
            </div>
            <pre className={`p-4 text-sm text-gray-100 overflow-x-auto ${!showFullCode ? 'max-h-96' : ''}`}>
              <code>{generated_code}</code>
            </pre>
          </div>

          {/* Code Explanation */}
          <div className="mt-4 text-sm text-gray-600 space-y-2">
            <p className="font-medium">This code will:</p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              {mode === 'ml' && (
                <>
                  <li>Load your dataset from Parquet</li>
                  <li>Prepare features and split data for training</li>
                  <li>Train a machine learning model</li>
                  <li>Calculate performance metrics</li>
                  <li>Return results with predictions</li>
                </>
              )}
              {mode === 'stats' && (
                <>
                  <li>Load your dataset</li>
                  <li>Perform statistical analysis</li>
                  <li>Calculate significance tests</li>
                  <li>Generate visualizations if applicable</li>
                </>
              )}
              {mode === 'python' && (
                <>
                  <li>Load and process your dataset</li>
                  <li>Execute the requested analysis</li>
                  <li>Return formatted results</li>
                </>
              )}
              {mode === 'workflow' && (
                <>
                  <li>Execute multiple analysis steps in sequence</li>
                  <li>Pass data between steps as needed</li>
                  <li>Return combined results</li>
                </>
              )}
            </ul>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="border-t border-gray-200 p-4 flex items-center justify-between bg-gray-50">
          <div className="text-sm text-gray-600">
            {requires_review ? (
              <span className="text-yellow-700">⚠️ Please review code before executing</span>
            ) : (
              <span className="text-green-700">✓ Code passed safety checks</span>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose} disabled={isExecuting}>
              Cancel
            </Button>
            <Button onClick={onExecute} disabled={isExecuting} className="min-w-[140px]">
              {isExecuting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                  Executing...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Execute Code
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
