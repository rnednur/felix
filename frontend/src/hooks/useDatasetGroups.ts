import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  createDatasetGroup,
  listDatasetGroups,
  getDatasetGroup,
  updateDatasetGroup,
  deleteDatasetGroup,
  addDatasetToGroup,
  removeDatasetFromGroup,
} from '@/services/api'

export function useDatasetGroups() {
  return useQuery({
    queryKey: ['dataset-groups'],
    queryFn: listDatasetGroups,
  })
}

export function useDatasetGroup(id: string | undefined) {
  return useQuery({
    queryKey: ['dataset-group', id],
    queryFn: () => getDatasetGroup(id!),
    enabled: !!id,
  })
}

export function useCreateDatasetGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: createDatasetGroup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataset-groups'] })
    },
  })
}

export function useUpdateDatasetGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: { name?: string; description?: string } }) =>
      updateDatasetGroup(id, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['dataset-groups'] })
      queryClient.invalidateQueries({ queryKey: ['dataset-group', variables.id] })
    },
  })
}

export function useDeleteDatasetGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteDatasetGroup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataset-groups'] })
    },
  })
}

export function useAddDatasetToGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ groupId, membership }: {
      groupId: string
      membership: { dataset_id: string; alias?: string; display_order?: number }
    }) => addDatasetToGroup(groupId, membership),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['dataset-group', variables.groupId] })
      queryClient.invalidateQueries({ queryKey: ['dataset-groups'] })
    },
  })
}

export function useRemoveDatasetFromGroup() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ groupId, datasetId }: { groupId: string; datasetId: string }) =>
      removeDatasetFromGroup(groupId, datasetId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['dataset-group', variables.groupId] })
      queryClient.invalidateQueries({ queryKey: ['dataset-groups'] })
    },
  })
}
