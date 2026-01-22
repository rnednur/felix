import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import axios from '@/services/api'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Sparkles, RefreshCw, AlertTriangle, CheckCircle2, Info, ChevronDown, ChevronUp, HelpCircle } from 'lucide-react'

interface DataScoutPanelProps {
  datasetId: string
  datasetName: string
  onQuestionClick?: (question: string) => void
}

interface ScoutResult {
  success: boolean
  dataset_id: string
  sample_size: number
  total_rows: number
  observations: string[]
  scouting_questions: string[]
  column_profiles: any[]
  discrepancies: any[]
  timestamp: string
  cached?: boolean  // True if loaded from cache
}

export function DataScoutPanel({ datasetId, datasetName, onQuestionClick }: DataScoutPanelProps) {
  const [expanded, setExpanded] = useState(true)
  const [showDetails, setShowDetails] = useState(false)
  const [showSemanticDetails, setShowSemanticDetails] = useState(false)

  // Fetch scouting results (uses backend cache)
  const { data: scoutData, isLoading, refetch } = useQuery<ScoutResult>({
    queryKey: ['data-scout', datasetId],
    queryFn: async () => {
      const response = await axios.post(`/datasets/${datasetId}/scout`, {
        sample_size: 1000,
        force_refresh: false  // Use cache if available
      })
      return response.data
    },
    staleTime: Infinity,  // Never refetch automatically - backend handles caching
    refetchOnWindowFocus: false,
    refetchOnMount: false,
    refetchOnReconnect: false
  })

  // Force refresh scouting (bypass cache)
  const refreshMutation = useMutation({
    mutationFn: async () => {
      const response = await axios.post(`/datasets/${datasetId}/scout`, {
        sample_size: 1000,
        force_refresh: true  // Bypass cache
      })
      return response.data
    },
    onSuccess: (data) => {
      // Update the query cache with new data
      refetch()
    }
  })

  // Regenerate observations with LLM
  const regenerateMutation = useMutation({
    mutationFn: async () => {
      const response = await axios.post(`/datasets/${datasetId}/scout/regenerate-observations`, {
        use_llm: true
      })
      return response.data
    },
    onSuccess: () => {
      refetch()
    }
  })

  const isRefreshing = refreshMutation.isPending

  // Group discrepancies by severity
  const highPriorityIssues = scoutData?.discrepancies?.filter(d => d.severity === 'high') || []
  const mediumPriorityIssues = scoutData?.discrepancies?.filter(d => d.severity === 'medium') || []
  const infoItems = scoutData?.discrepancies?.filter(d => d.severity === 'info') || []

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      case 'medium':
        return <Info className="h-4 w-4 text-yellow-500" />
      case 'info':
        return <CheckCircle2 className="h-4 w-4 text-blue-500" />
      default:
        return <Info className="h-4 w-4 text-gray-500" />
    }
  }

  const getSeverityBadge = (severity: string) => {
    const colors = {
      high: 'bg-red-100 text-red-800 border-red-200',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      info: 'bg-blue-100 text-blue-800 border-blue-200',
      low: 'bg-gray-100 text-gray-800 border-gray-200'
    }
    return colors[severity as keyof typeof colors] || colors.low
  }

  if (isLoading) {
    return (
      <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-white">
        <CardContent className="p-6">
          <div className="flex items-center justify-center space-x-2 text-purple-600">
            <Sparkles className="h-5 w-5 animate-spin" />
            <span className="text-sm font-medium">Scouting your data...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!scoutData || !scoutData.success) {
    return null
  }

  return (
    <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-white shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-5 w-5 text-purple-600" />
            <CardTitle className="text-lg font-semibold text-gray-900">
              Data Scout Report
            </CardTitle>
            {scoutData.discrepancies.length > 0 && (
              <Badge variant="outline" className="ml-2 bg-yellow-50 text-yellow-700 border-yellow-200">
                {scoutData.discrepancies.length} findings
              </Badge>
            )}
          </div>
          <div className="flex items-center space-x-2">
            {scoutData?.cached && (
              <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                Cached
              </Badge>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => refreshMutation.mutate()}
              disabled={isLoading || isRefreshing}
              className="text-purple-600 hover:text-purple-700 hover:bg-purple-100"
              title="Refresh scouting data"
            >
              <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
              className="text-gray-600 hover:text-gray-900"
            >
              {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Quick diagnostic of <strong>{datasetName}</strong> • Analyzed {scoutData.sample_size.toLocaleString()} of {scoutData.total_rows.toLocaleString()} rows
        </p>
      </CardHeader>

      {expanded && (
        <CardContent className="pt-0 space-y-4">
          {/* First Look Observations */}
          <div className="bg-white rounded-lg p-4 border border-purple-100">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-semibold text-gray-900 flex items-center space-x-2">
                <CheckCircle2 className="h-4 w-4 text-purple-600" />
                <span>First Look Observations</span>
              </h4>
              <Badge variant="outline" className="text-xs bg-purple-50 text-purple-700 border-purple-200">
                AI-Enhanced
              </Badge>
            </div>

            <ul className="space-y-2 text-sm text-gray-700">
              {scoutData.observations.slice(0, 6).map((obs, idx) => (
                <li key={idx} className="flex items-start space-x-2">
                  <span className="text-purple-400 mt-0.5">•</span>
                  <span dangerouslySetInnerHTML={{ __html: obs.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                </li>
              ))}
            </ul>

            {/* Show semantic insights count if available */}
            {scoutData.column_profiles && (
              <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between">
                <p className="text-xs text-gray-500">
                  {scoutData.column_profiles.filter(p => p.patterns?.semantic?.confidence_score > 0.7).length} columns analyzed with semantic AI •{' '}
                  {scoutData.column_profiles.filter(p => !p.patterns?.semantic || p.patterns?.semantic?.confidence_score <= 0.7).length} using rule-based detection
                </p>
                {scoutData.column_profiles.filter(p => p.patterns?.semantic?.confidence_score > 0.7).length > 0 && (
                  <button
                    onClick={() => setShowSemanticDetails(!showSemanticDetails)}
                    className="text-xs text-purple-600 hover:text-purple-800 font-medium"
                  >
                    {showSemanticDetails ? 'Hide' : 'View'} semantic details
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Semantic Details Section */}
          {showSemanticDetails && scoutData.column_profiles && (
            <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg p-4 border border-purple-200">
              <h4 className="text-sm font-semibold text-gray-900 mb-3 flex items-center space-x-2">
                <Sparkles className="h-4 w-4 text-purple-600" />
                <span>Semantic Analysis Details</span>
              </h4>
              <div className="space-y-3">
                {scoutData.column_profiles
                  .filter(p => p.patterns?.semantic?.confidence_score > 0.7)
                  .map((profile, idx) => {
                    const semantic = profile.patterns.semantic
                    return (
                      <div key={idx} className="bg-white rounded-lg p-3 border border-purple-100">
                        <div className="flex items-start justify-between mb-2">
                          <h5 className="font-semibold text-gray-900 text-sm">{profile.column_name}</h5>
                          <Badge variant="outline" className="text-xs">
                            {(semantic.confidence_score * 100).toFixed(0)}% confident
                          </Badge>
                        </div>
                        <div className="space-y-1 text-xs text-gray-700">
                          <p><strong>Type:</strong> {semantic.semantic_type}</p>
                          {semantic.business_context && (
                            <p><strong>Context:</strong> {semantic.business_context}</p>
                          )}
                          {semantic.format_pattern && (
                            <p><strong>Format:</strong> <code className="bg-gray-100 px-1 rounded">{semantic.format_pattern}</code></p>
                          )}
                          {semantic.quality_issues && semantic.quality_issues.length > 0 && (
                            <div className="mt-2 pt-2 border-t border-gray-100">
                              <p className="font-medium text-yellow-700">Quality Issues:</p>
                              <ul className="list-disc list-inside ml-2 mt-1">
                                {semantic.quality_issues.map((issue: string, i: number) => (
                                  <li key={i} className="text-yellow-600">{issue}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {semantic.suggested_validations && semantic.suggested_validations.length > 0 && (
                            <div className="mt-2 pt-2 border-t border-gray-100">
                              <p className="font-medium text-green-700">Suggested Validations:</p>
                              <ul className="list-disc list-inside ml-2 mt-1">
                                {semantic.suggested_validations.map((validation: string, i: number) => (
                                  <li key={i} className="text-green-600">{validation}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })}
              </div>
            </div>
          )}

          {/* High Priority Issues */}
          {highPriorityIssues.length > 0 && (
            <div className="bg-red-50 rounded-lg p-4 border border-red-200">
              <h4 className="text-sm font-semibold text-red-900 mb-3 flex items-center space-x-2">
                <AlertTriangle className="h-4 w-4" />
                <span>High Priority Issues</span>
              </h4>
              <ul className="space-y-2 text-sm">
                {highPriorityIssues.map((issue, idx) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="text-red-500 mt-0.5">⚠️</span>
                    <div>
                      <p className="text-red-800"><strong>{issue.column}</strong>: {issue.description}</p>
                      {issue.suggestion && (
                        <p className="text-red-600 text-xs mt-1 italic">💡 {issue.suggestion}</p>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Scouting Questions */}
          {scoutData.scouting_questions.length > 0 && (
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <h4 className="text-sm font-semibold text-blue-900 mb-3 flex items-center space-x-2">
                <HelpCircle className="h-4 w-4" />
                <span>Scouting Questions</span>
              </h4>
              <p className="text-xs text-blue-700 mb-3">
                These questions can help clarify data quality and metadata issues:
              </p>
              <ul className="space-y-2 text-sm">
                {scoutData.scouting_questions.map((question, idx) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <span className="text-blue-500 mt-0.5">?</span>
                    <span
                      className="text-blue-800"
                      dangerouslySetInnerHTML={{ __html: question.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }}
                    />
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Show Details Toggle */}
          {(mediumPriorityIssues.length > 0 || infoItems.length > 0) && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowDetails(!showDetails)}
              className="w-full text-gray-700 border-gray-300"
            >
              {showDetails ? 'Hide' : 'Show'} Additional Details
              {showDetails ? <ChevronUp className="ml-2 h-4 w-4" /> : <ChevronDown className="ml-2 h-4 w-4" />}
            </Button>
          )}

          {/* Additional Details */}
          {showDetails && (
            <>
              {mediumPriorityIssues.length > 0 && (
                <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                  <h4 className="text-sm font-semibold text-yellow-900 mb-3 flex items-center space-x-2">
                    <Info className="h-4 w-4" />
                    <span>Medium Priority Issues</span>
                  </h4>
                  <ul className="space-y-2 text-sm">
                    {mediumPriorityIssues.map((issue, idx) => (
                      <li key={idx} className="flex items-start space-x-2">
                        <span className="text-yellow-500 mt-0.5">⚡</span>
                        <div>
                          <p className="text-yellow-800"><strong>{issue.column}</strong>: {issue.description}</p>
                          {issue.suggestion && (
                            <p className="text-yellow-600 text-xs mt-1 italic">💡 {issue.suggestion}</p>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {infoItems.length > 0 && (
                <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                  <h4 className="text-sm font-semibold text-blue-900 mb-3 flex items-center space-x-2">
                    <CheckCircle2 className="h-4 w-4" />
                    <span>Informational</span>
                  </h4>
                  <ul className="space-y-2 text-sm">
                    {infoItems.map((item, idx) => (
                      <li key={idx} className="flex items-start space-x-2">
                        <span className="text-blue-500 mt-0.5">ℹ️</span>
                        <div>
                          <p className="text-blue-800"><strong>{item.column}</strong>: {item.description}</p>
                          {item.suggestion && (
                            <p className="text-blue-600 text-xs mt-1 italic">💡 {item.suggestion}</p>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          {/* Footer with timestamp */}
          <div className="text-xs text-gray-500 text-center pt-2 border-t border-gray-200">
            Generated {new Date(scoutData.timestamp).toLocaleString()}
          </div>
        </CardContent>
      )}
    </Card>
  )
}
