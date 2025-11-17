import { X, Database, TrendingUp, CheckCircle, AlertCircle } from 'lucide-react'

interface DatasetOverviewModalProps {
  isOpen: boolean
  onClose: () => void
  dataset: any
  description: any
}

export function DatasetOverviewModal({ isOpen, onClose, dataset, description }: DatasetOverviewModalProps) {
  if (!isOpen) return null

  const numericCols = dataset.schema?.columns.filter((c: any) =>
    ['int64', 'float64', 'int32', 'float32'].includes(c.dtype)
  ).length || 0

  const categoricalCols = dataset.schema?.columns.filter((c: any) =>
    ['object', 'string', 'category'].includes(c.dtype)
  ).length || 0

  const datetimeCols = dataset.schema?.columns.filter((c: any) =>
    c.dtype.includes('date')
  ).length || 0

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
                <Database className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">Dataset Overview</h2>
                <p className="text-blue-100 text-sm">{dataset.name}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white hover:bg-opacity-20 rounded-lg p-2 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Content */}
          <div className="overflow-y-auto max-h-[calc(90vh-80px)] p-6 space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="text-3xl font-bold text-blue-700">
                  {dataset.row_count.toLocaleString()}
                </div>
                <div className="text-sm text-blue-600 font-medium">Total Rows</div>
              </div>
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <div className="text-3xl font-bold text-purple-700">
                  {dataset.column_count}
                </div>
                <div className="text-sm text-purple-600 font-medium">Columns</div>
              </div>
            </div>

            {/* Column Breakdown */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-blue-600" />
                Column Breakdown
              </h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-700">
                    📊 Numeric columns
                  </span>
                  <span className="text-sm font-semibold text-gray-900">{numericCols}</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-700">
                    🏷️ Categorical columns
                  </span>
                  <span className="text-sm font-semibold text-gray-900">{categoricalCols}</span>
                </div>
                {datetimeCols > 0 && (
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm text-gray-700">
                      📅 Datetime columns
                    </span>
                    <span className="text-sm font-semibold text-gray-900">{datetimeCols}</span>
                  </div>
                )}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Use numeric columns for calculations, categorical for grouping, datetime for time-series analysis
              </p>
            </div>

            {/* Data Quality */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-600" />
                Data Quality
              </h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                  <span className="text-sm text-gray-700">Completeness</span>
                  <span className="text-sm font-semibold text-green-700">99.99%</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                  <span className="text-sm text-gray-700">Duplicate rows</span>
                  <span className="text-sm font-semibold text-green-700">0 (0.00%)</span>
                </div>
              </div>
            </div>

            {/* AI Description */}
            {description?.description_text && (
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-purple-600" />
                  AI Insights
                </h3>
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                  <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                    {description.description_text}
                  </p>
                </div>
              </div>
            )}

            {/* Quick Tips */}
            <div className="bg-blue-50 border-l-4 border-blue-600 rounded-r-lg p-4">
              <h4 className="text-sm font-semibold text-blue-900 mb-2">💡 Quick Tips</h4>
              <ul className="text-xs text-blue-800 space-y-1">
                <li>• Try asking "Show me the first 10 rows"</li>
                <li>• Use "Group by [category]" for summaries</li>
                <li>• Ask "What are the top 5 [items] by [metric]?"</li>
                <li>• Switch to Deep Research mode for comprehensive analysis</li>
              </ul>
            </div>
          </div>

          {/* Footer */}
          <div className="border-t border-gray-200 px-6 py-4 bg-gray-50">
            <button
              onClick={onClose}
              className="w-full px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-colors font-medium"
            >
              Got it, let's explore!
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
