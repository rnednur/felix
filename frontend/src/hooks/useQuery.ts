import { useMutation } from '@tanstack/react-query'
import { executeNLQuery, executeSQLQuery } from '@/services/api'

export function useNLQuery() {
  return useMutation({
    mutationFn: ({ query, datasetId, groupId }: { query: string; datasetId?: string; groupId?: string }) =>
      executeNLQuery(query, { datasetId, groupId }),
  })
}

export function useSQLQuery() {
  return useMutation({
    mutationFn: ({ sql, datasetId, groupId }: { sql: string; datasetId?: string; groupId?: string }) =>
      executeSQLQuery(sql, { datasetId, groupId }),
  })
}
