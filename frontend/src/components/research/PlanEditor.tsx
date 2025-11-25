import { useState } from 'react'
import { Button } from '@/components/ui/button'

interface SubQuestion {
  id: string
  question: string
  intent_type: string
  desired_output: string
  priority: number
  editable: boolean
}

interface ResearchPlan {
  main_question: string
  sub_questions: SubQuestion[]
  estimated_time: string
  research_stages: string[]
}

interface PlanEditorProps {
  plan: ResearchPlan
  onExecute: (editedPlan: { main_question: string; sub_questions: SubQuestion[] }) => void
  onCancel: () => void
}

export function PlanEditor({ plan, onExecute, onCancel }: PlanEditorProps) {
  const [subQuestions, setSubQuestions] = useState(plan.sub_questions)
  const [showAllStages, setShowAllStages] = useState(false)

  const updateQuestion = (id: string, newText: string) => {
    setSubQuestions(prev =>
      prev.map(sq => sq.id === id ? { ...sq, question: newText } : sq)
    )
  }

  const removeQuestion = (id: string) => {
    setSubQuestions(prev => prev.filter(sq => sq.id !== id))
  }

  const addQuestion = () => {
    const newQ: SubQuestion = {
      id: `sq_${Date.now()}`,
      question: '',
      intent_type: 'descriptive',
      desired_output: 'table',
      priority: 2,
      editable: true
    }
    setSubQuestions(prev => [...prev, newQ])
  }

  const getStageIcon = (index: number) => {
    const icons = ['📚', '≡', '📊']
    return icons[index] || '•'
  }

  return (
    <div className="bg-white rounded-lg shadow-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
      {/* Header */}
      <div className="px-6 py-5 border-b border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900">{plan.main_question}</h2>
        <p className="text-sm text-gray-600 mt-2">
          Review and edit the research plan before execution
        </p>
      </div>

      {/* Content - Scrollable */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="space-y-4">
          {plan.research_stages.map((stage, i) => (
            <div key={i}>
              {/* Stage Header */}
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-lg">
                  {getStageIcon(i)}
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{stage}</h3>
                </div>
              </div>

              {/* Show first stage (Research Websites) expanded by default */}
              {i === 0 && (
                <div className="ml-12 space-y-2">
                  {subQuestions.map((sq, idx) => (
                    <div key={sq.id} className="bg-gray-50 border border-gray-200 rounded-lg p-3 hover:border-gray-300 transition-colors">
                      <div className="flex items-start gap-3">
                        <span className="text-sm font-medium text-gray-500 mt-2">({idx + 1})</span>
                        <textarea
                          value={sq.question}
                          onChange={(e) => updateQuestion(sq.id, e.target.value)}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          placeholder="Enter research question..."
                          rows={2}
                        />
                        <button
                          onClick={() => removeQuestion(sq.id)}
                          className="text-red-500 hover:text-red-700 hover:bg-red-50 rounded p-1 transition-colors"
                          title="Remove question"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                      <div className="ml-8 mt-2 flex gap-3 text-xs text-gray-500">
                        <span>Type: <span className="font-medium">{sq.intent_type}</span></span>
                        <span>•</span>
                        <span>Output: <span className="font-medium">{sq.desired_output}</span></span>
                        <span>•</span>
                        <span>Priority: <span className="font-medium">{sq.priority}</span></span>
                      </div>
                    </div>
                  ))}

                  {/* Add Question Button */}
                  <button
                    onClick={addQuestion}
                    className="ml-8 text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1 py-2"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Add question
                  </button>
                </div>
              )}

              {/* Other stages - show expandable */}
              {i > 0 && !showAllStages && (
                <div className="ml-12 text-sm text-gray-500">
                  <button
                    onClick={() => setShowAllStages(true)}
                    className="hover:text-gray-700 flex items-center gap-1"
                  >
                    <span>Click to see all stages</span>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                </div>
              )}

              {/* Show other stages when expanded */}
              {i > 0 && showAllStages && (
                <div className="ml-12 text-sm text-gray-600 bg-gray-50 rounded-lg p-3">
                  <p>This stage will be executed automatically based on your research questions above.</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Footer - Fixed at bottom */}
      <div className="px-6 py-4 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Ready in {plan.estimated_time}</span>
        </div>

        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={onCancel}
            className="border-gray-300"
          >
            Cancel
          </Button>
          <Button
            onClick={() => onExecute({
              main_question: plan.main_question,
              sub_questions: subQuestions
            })}
            disabled={subQuestions.length === 0 || subQuestions.some(sq => !sq.question.trim())}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            Start research
          </Button>
        </div>
      </div>
    </div>
  )
}
