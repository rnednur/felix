import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../services/api'

export interface ResearchJobSummary {
  research_id: string
  dataset_id: string
  main_question: string
  direct_answer: string
  key_findings_count: number
  has_verbose_analysis: boolean
  saved_at: string
  execution_time: number
  stages_completed: string[]
  metadata: any
}

export interface ResearchRecord {
  research_id: string
  dataset_id: string
  saved_at: string
  metadata: any
  result: any
}

export function useResearchHistory(datasetId?: string) {
  return useQuery({
    queryKey: ['research-history', datasetId],
    queryFn: async () => {
      const params = datasetId ? `?dataset_id=${datasetId}` : ''
      const response = await api.get(`/deep-research/history${params}`)
      return response.data as { success: boolean; count: number; jobs: ResearchJobSummary[] }
    }
  })
}

export function useResearchById(researchId: string | null) {
  return useQuery({
    queryKey: ['research', researchId],
    queryFn: async () => {
      if (!researchId) return null
      const response = await api.get(`/deep-research/history/${researchId}`)
      return response.data as ResearchRecord
    },
    enabled: !!researchId
  })
}

export function useDeleteResearch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (researchId: string) => {
      const response = await api.delete(`/deep-research/history/${researchId}`)
      return response.data
    },
    onSuccess: () => {
      // Invalidate and refetch research history
      queryClient.invalidateQueries({ queryKey: ['research-history'] })
    }
  })
}

export function useSearchResearch(query: string, datasetId?: string) {
  return useQuery({
    queryKey: ['research-search', query, datasetId],
    queryFn: async () => {
      if (!query || query.length < 2) return { results: [], count: 0 }

      const params = new URLSearchParams({ q: query })
      if (datasetId) params.append('dataset_id', datasetId)

      const response = await api.get(`/deep-research/search?${params}`)
      return response.data as { success: boolean; query: string; count: number; results: any[] }
    },
    enabled: query.length >= 2
  })
}
