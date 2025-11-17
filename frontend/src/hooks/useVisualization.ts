import { useQuery, useMutation } from '@tanstack/react-query'
import { getVisualizationSuggestions, createVisualization } from '@/services/api'

export function useVisualizationSuggestions(queryId: string) {
  return useQuery({
    queryKey: ['viz-suggestions', queryId],
    queryFn: () => getVisualizationSuggestions(queryId),
    enabled: !!queryId,
  })
}

export function useCreateVisualization() {
  return useMutation({
    mutationFn: createVisualization,
  })
}
