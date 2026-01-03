import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '@/services/api'

export interface ResearchJob {
  job_id: string
  dataset_id: string
  main_question: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress_percentage: number
  current_stage: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
  execution_time_seconds: number | null
  has_result: boolean
  error_message: string | null
}

export interface JobStatusResponse {
  success: boolean
  job_id: string
  status: string
  current_stage: string | null
  progress_percentage: number
  result: any | null
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
  execution_time_seconds: number | null
}

export function useSubmitResearchJob() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({
      datasetId,
      question,
      verbose = 0
    }: {
      datasetId: string
      question: string
      verbose?: number
    }) => {
      const response = await api.post('/deep-research/jobs/submit', {
        dataset_id: datasetId,
        question,
        verbose
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['research-jobs'] })
    }
  })
}

export function useJobStatus(jobId: string | null, options?: {
  enabled?: boolean
  refetchInterval?: number | false
}) {
  return useQuery<JobStatusResponse>({
    queryKey: ['research-job', jobId],
    queryFn: async () => {
      if (!jobId) throw new Error('No job ID')
      const response = await api.get(`/deep-research/jobs/${jobId}`)
      return response.data
    },
    enabled: !!jobId && (options?.enabled ?? true),
    refetchInterval: options?.refetchInterval ?? false,
    staleTime: 1000 // Consider data stale after 1 second
  })
}

export function useResearchJobs(datasetId?: string) {
  return useQuery<{ success: boolean; count: number; jobs: ResearchJob[] }>({
    queryKey: ['research-jobs', datasetId],
    queryFn: async () => {
      const params = datasetId ? { dataset_id: datasetId } : {}
      const response = await api.get('/deep-research/jobs', { params })
      return response.data
    }
  })
}

export function useCancelJob() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (jobId: string) => {
      const response = await api.delete(`/deep-research/jobs/${jobId}`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['research-jobs'] })
    }
  })
}
