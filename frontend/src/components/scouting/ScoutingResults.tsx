import { CheckCircle2, XCircle, AlertCircle, HelpCircle, X } from 'lucide-react'

interface ScoutingResultsProps {
  result: {
    observations: string[]
    answers?: string[]
    rule_validations?: string[]
    additional_questions?: string[]
    discrepancies?: Array<{
      column: string
      type: string
      severity: string
      description: string
      suggestion?: string
    }>
  }
  onClose: () => void
}

export function ScoutingResults({ result, onClose }: ScoutingResultsProps) {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'medium':
        return 'text-orange-600 bg-orange-50 border-orange-200'
      case 'low':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      default:
        return 'text-blue-600 bg-blue-50 border-blue-200'
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Scouting Results</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Key Observations */}
          {result.observations && result.observations.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                Key Observations
              </h3>
              <div className="space-y-2">
                {result.observations.map((obs, index) => (
                  <div
                    key={index}
                    className="p-3 bg-gray-50 rounded-lg text-sm text-gray-700"
                    dangerouslySetInnerHTML={{
                      __html: obs
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/⚠️/g, '<span class="mr-1">⚠️</span>')
                    }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Answers to Specific Questions */}
          {result.answers && result.answers.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <HelpCircle className="h-4 w-4 text-blue-600" />
                Answers to Your Questions
              </h3>
              <div className="space-y-2">
                {result.answers.map((answer, index) => (
                  <div
                    key={index}
                    className="p-3 bg-blue-50 rounded-lg text-sm text-gray-700"
                  >
                    {answer}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Rule Validations */}
          {result.rule_validations && result.rule_validations.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-purple-600" />
                Rule Validation Results
              </h3>
              <div className="space-y-2">
                {result.rule_validations.map((validation, index) => (
                  <div
                    key={index}
                    className="p-3 bg-purple-50 rounded-lg text-sm text-gray-700"
                  >
                    {validation}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Discrepancies */}
          {result.discrepancies && result.discrepancies.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <XCircle className="h-4 w-4 text-red-600" />
                Detected Issues
              </h3>
              <div className="space-y-2">
                {result.discrepancies.map((disc, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border ${getSeverityColor(disc.severity)}`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-medium">{disc.column}</p>
                        <p className="text-sm mt-1">{disc.description}</p>
                        {disc.suggestion && (
                          <p className="text-xs mt-2 opacity-75">
                            💡 {disc.suggestion}
                          </p>
                        )}
                      </div>
                      <span className="text-xs font-semibold px-2 py-1 rounded uppercase">
                        {disc.severity}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Additional Questions */}
          {result.additional_questions && result.additional_questions.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <HelpCircle className="h-4 w-4 text-gray-600" />
                Follow-up Questions
              </h3>
              <div className="space-y-2">
                {result.additional_questions.map((question, index) => (
                  <div
                    key={index}
                    className="p-3 bg-gray-50 rounded-lg text-sm text-gray-700 flex items-start gap-2"
                  >
                    <span className="text-gray-400 font-medium">{index + 1}.</span>
                    <span
                      dangerouslySetInnerHTML={{
                        __html: question.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                      }}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 px-6 py-4 border-t flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
