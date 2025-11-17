import { useMutation } from '@tanstack/react-query'
import { executeNLQuery, executeSQLQuery } from '@/services/api'

export function useNLQuery() {
  return useMutation({
    mutationFn: ({ datasetId, query }: { datasetId: string; query: string }) =>
      executeNLQuery(datasetId, query),
  })
}

export function useSQLQuery() {
  return useMutation({
    mutationFn: ({ datasetId, sql }: { datasetId: string; sql: string }) =>
      executeSQLQuery(datasetId, sql),
  })
}
