import { useState } from 'react'
import { useResearchHistory, useResearchById, useDeleteResearch, type ResearchJobSummary } from '@/hooks/useResearchHistory'
import { Button } from '@/components/ui/button'
import { FileText, Trash2, Search, Clock, CheckCircle2, Eye, X } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface ResearchHistoryModalProps {
  isOpen: boolean
  onClose: () => void
  datasetId: string
  onLoadResearch: (report: any) => void
}

export function ResearchHistoryModal({ isOpen, onClose, datasetId, onLoadResearch }: ResearchHistoryModalProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedResearchId, setSelectedResearchId] = useState<string | null>(null)

  const { data: historyData, isLoading } = useResearchHistory(datasetId)
  const { data: selectedResearch } = useResearchById(selectedResearchId)
  const deleteResearch = useDeleteResearch()

  const filteredJobs = historyData?.jobs.filter(job =>
    job.main_question.toLowerCase().includes(searchQuery.toLowerCase())
  ) || []

  const handleLoadResearch = (researchId: string) => {
    setSelectedResearchId(researchId)
  }

  const handleViewReport = () => {
    if (selectedResearch?.result) {
      onLoadResearch(selectedResearch.result)
      onClose()
    }
  }

  const handleDelete = (researchId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm('Delete this research job?')) {
      deleteResearch.mutate(researchId)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Research History
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {/* Search */}
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search research questions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Loading state */}
          {isLoading && (
            <div className="text-center py-8 text-gray-500">
              Loading research history...
            </div>
          )}

          {/* Empty state */}
          {!isLoading && filteredJobs.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>No research jobs found</p>
              <p className="text-sm mt-1">Run a deep research analysis to get started</p>
            </div>
          )}

          {/* Research list */}
          <div className="space-y-3">
            {filteredJobs.map((job) => (
              <div
                key={job.research_id}
                className={`border rounded-lg p-4 hover:bg-gray-50 transition cursor-pointer ${
                  selectedResearchId === job.research_id ? 'border-blue-500 bg-blue-50' : ''
                }`}
                onClick={() => handleLoadResearch(job.research_id)}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900 mb-1 truncate">
                      {job.main_question}
                    </h3>
                    <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                      {job.direct_answer}
                    </p>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDistanceToNow(new Date(job.saved_at), { addSuffix: true })}
                      </span>
                      <span className="flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        {job.key_findings_count} findings
                      </span>
                      {job.has_verbose_analysis && (
                        <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium">
                          Verbose
                        </span>
                      )}
                      <span className="text-gray-400">
                        {job.execution_time.toFixed(1)}s
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleLoadResearch(job.research_id)
                      }}
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => handleDelete(job.research_id, e)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-gray-200 p-6">
          <div className="text-sm text-gray-600">
            {filteredJobs.length} research job{filteredJobs.length !== 1 ? 's' : ''}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
            {selectedResearchId && (
              <Button onClick={handleViewReport}>
                View Report
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
