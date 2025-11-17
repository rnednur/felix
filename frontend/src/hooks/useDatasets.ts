import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { uploadDataset, getDataset, listDatasets, getDatasetPreview, getDatasetSchema } from '@/services/api'

export function useDatasets() {
  return useQuery({
    queryKey: ['datasets'],
    queryFn: listDatasets,
  })
}

export function useDataset(id: string) {
  return useQuery({
    queryKey: ['dataset', id],
    queryFn: () => getDataset(id),
    enabled: !!id,
  })
}

export function useDatasetPreview(id: string) {
  return useQuery({
    queryKey: ['dataset-preview', id],
    queryFn: () => getDatasetPreview(id),
    enabled: !!id,
  })
}

export function useDatasetSchema(id: string) {
  return useQuery({
    queryKey: ['dataset-schema', id],
    queryFn: () => getDatasetSchema(id),
    enabled: !!id,
  })
}

export function useUploadDataset() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: uploadDataset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
    },
  })
}
