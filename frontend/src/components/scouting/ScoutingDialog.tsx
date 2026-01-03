import { useState } from 'react'
import { X, Sparkles, Plus, Trash2 } from 'lucide-react'
import axios from 'axios'

interface ScoutingDialogProps {
  datasetId: string
  datasetName: string
  onClose: () => void
  onSuccess: (result: any) => void
}

export function ScoutingDialog({ datasetId, datasetName, onClose, onSuccess }: ScoutingDialogProps) {
  const [loading, setLoading] = useState(false)
  const [businessContext, setBusinessContext] = useState('')
  const [customRules, setCustomRules] = useState<string[]>([''])
  const [specificQuestions, setSpecificQuestions] = useState<string[]>([''])
  const [sampleSize, setSampleSize] = useState(1000)

  const addRule = () => {
    setCustomRules([...customRules, ''])
  }

  const updateRule = (index: number, value: string) => {
    const updated = [...customRules]
    updated[index] = value
    setCustomRules(updated)
  }

  const removeRule = (index: number) => {
    setCustomRules(customRules.filter((_, i) => i !== index))
  }

  const addQuestion = () => {
    setSpecificQuestions([...specificQuestions, ''])
  }

  const updateQuestion = (index: number, value: string) => {
    const updated = [...specificQuestions]
    updated[index] = value
    setSpecificQuestions(updated)
  }

  const removeQuestion = (index: number) => {
    setSpecificQuestions(specificQuestions.filter((_, i) => i !== index))
  }

  const handleSubmit = async () => {
    setLoading(true)
    try {
      const response = await axios.post(`/datasets/${datasetId}/scout/interactive`, {
        sample_size: sampleSize,
        business_context: businessContext.trim(),
        custom_rules: customRules.filter(r => r.trim()),
        specific_questions: specificQuestions.filter(q => q.trim())
      })

      onSuccess(response.data)
      onClose()
    } catch (error) {
      console.error('Scouting failed:', error)
      alert('Failed to run scouting agent. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-600" />
            <h2 className="text-lg font-semibold">Data Scouting Agent</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
            disabled={loading}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Dataset Info */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <p className="text-sm text-blue-900">
              <strong>Dataset:</strong> {datasetName}
            </p>
            <p className="text-sm text-blue-700 mt-1">
              The scouting agent will analyze your data and provide intelligent observations,
              quality checks, and recommendations.
            </p>
          </div>

          {/* Business Context */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Business Context
              <span className="text-gray-500 font-normal ml-2">(Optional)</span>
            </label>
            <textarea
              value={businessContext}
              onChange={(e) => setBusinessContext(e.target.value)}
              placeholder="e.g., This dataset contains customer orders from our e-commerce platform. Orders should have valid email addresses and US zip codes..."
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              rows={3}
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">
              Help the agent understand your data's business context
            </p>
          </div>

          {/* Custom Validation Rules */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Validation Rules
              <span className="text-gray-500 font-normal ml-2">(Optional)</span>
            </label>
            <div className="space-y-2">
              {customRules.map((rule, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={rule}
                    onChange={(e) => updateRule(index, e.target.value)}
                    placeholder={`e.g., Email addresses must be valid, Prices must be > 0`}
                    className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    disabled={loading}
                  />
                  {customRules.length > 1 && (
                    <button
                      onClick={() => removeRule(index)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded"
                      disabled={loading}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
            <button
              onClick={addRule}
              className="mt-2 text-sm text-purple-600 hover:text-purple-700 flex items-center gap-1"
              disabled={loading}
            >
              <Plus className="h-4 w-4" />
              Add Rule
            </button>
          </div>

          {/* Specific Questions */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Specific Questions
              <span className="text-gray-500 font-normal ml-2">(Optional)</span>
            </label>
            <div className="space-y-2">
              {specificQuestions.map((question, index) => (
                <div key={index} className="flex gap-2">
                  <input
                    type="text"
                    value={question}
                    onChange={(e) => updateQuestion(index, e.target.value)}
                    placeholder={`e.g., Are there any duplicate customer IDs?`}
                    className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    disabled={loading}
                  />
                  {specificQuestions.length > 1 && (
                    <button
                      onClick={() => removeQuestion(index)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded"
                      disabled={loading}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
            <button
              onClick={addQuestion}
              className="mt-2 text-sm text-purple-600 hover:text-purple-700 flex items-center gap-1"
              disabled={loading}
            >
              <Plus className="h-4 w-4" />
              Add Question
            </button>
          </div>

          {/* Sample Size */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sample Size
            </label>
            <input
              type="number"
              value={sampleSize}
              onChange={(e) => setSampleSize(parseInt(e.target.value) || 1000)}
              min={100}
              max={10000}
              step={100}
              className="w-32 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              disabled={loading}
            />
            <p className="text-xs text-gray-500 mt-1">
              Number of rows to analyze (100-10,000)
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-gray-50 px-6 py-4 border-t flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
            disabled={loading}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Run Scouting Agent
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
