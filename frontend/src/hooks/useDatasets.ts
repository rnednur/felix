import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  uploadDataset,
  getDataset,
  listDatasets,
  getDatasetPreview,
  getDatasetAllRows,
  getDatasetSchema,
  deleteDataset,
  importGoogleSheets,
} from '@/services/api'

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

export function useDatasetAllRows(id: string, enabled: boolean = false) {
  return useQuery({
    queryKey: ['dataset-all-rows', id],
    queryFn: () => getDatasetAllRows(id),
    enabled: !!id && enabled,
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

export function useDeleteDataset() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteDataset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
    },
  })
}

export function useImportGoogleSheets() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: importGoogleSheets,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
    },
  })
}
