import { useState } from 'react'
import { Plus, Trash2, Edit2, Users } from 'lucide-react'
import {
  useDatasetGroups,
  useCreateDatasetGroup,
  useDeleteDatasetGroup,
  useDatasetGroup,
  useAddDatasetToGroup,
  useRemoveDatasetFromGroup,
} from '@/hooks/useDatasetGroups'
import { useDatasets } from '@/hooks/useDatasets'

export function DatasetGroupManager() {
  const [selectedGroupId, setSelectedGroupId] = useState<string>()
  const [isCreating, setIsCreating] = useState(false)
  const [isAddingDataset, setIsAddingDataset] = useState(false)
  const [newGroupName, setNewGroupName] = useState('')
  const [newGroupDescription, setNewGroupDescription] = useState('')

  const { data: groups = [], isLoading: groupsLoading } = useDatasetGroups()
  const { data: datasets = [] } = useDatasets()
  const { data: selectedGroup } = useDatasetGroup(selectedGroupId)
  const createGroup = useCreateDatasetGroup()
  const deleteGroup = useDeleteDatasetGroup()
  const addDataset = useAddDatasetToGroup()
  const removeDataset = useRemoveDatasetFromGroup()

  const handleCreateGroup = async () => {
    if (!newGroupName.trim()) return

    await createGroup.mutateAsync({
      name: newGroupName,
      description: newGroupDescription || undefined,
    })

    setNewGroupName('')
    setNewGroupDescription('')
    setIsCreating(false)
  }

  const handleAddDataset = async (datasetId: string, alias?: string) => {
    if (!selectedGroupId) return

    await addDataset.mutateAsync({
      groupId: selectedGroupId,
      membership: {
        dataset_id: datasetId,
        alias,
        display_order: selectedGroup?.memberships.length || 0,
      },
    })

    setIsAddingDataset(false)
  }

  const handleRemoveDataset = async (datasetId: string) => {
    if (!selectedGroupId) return
    if (!confirm('Remove this dataset from the group?')) return

    await removeDataset.mutateAsync({
      groupId: selectedGroupId,
      datasetId,
    })
  }

  const handleDeleteGroup = async (groupId: string) => {
    if (!confirm('Delete this dataset group? This will not delete the datasets themselves.')) return

    await deleteGroup.mutateAsync(groupId)
    if (selectedGroupId === groupId) {
      setSelectedGroupId(undefined)
    }
  }

  const availableDatasets = datasets.filter(
    (d) => !selectedGroup?.memberships.some((m) => m.dataset_id === d.id)
  )

  return (
    <div className="flex gap-4 h-full">
      {/* Groups List */}
      <div className="w-1/3 border-r pr-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Dataset Groups</h3>
          <button
            onClick={() => setIsCreating(true)}
            className="p-2 hover:bg-gray-100 rounded"
            title="Create new group"
          >
            <Plus size={20} />
          </button>
        </div>

        {groupsLoading ? (
          <div className="text-gray-500">Loading...</div>
        ) : groups.length === 0 ? (
          <div className="text-gray-500 text-sm">
            No dataset groups yet. Create one to query multiple datasets together.
          </div>
        ) : (
          <div className="space-y-2">
            {groups.map((group) => (
              <div
                key={group.id}
                className={`p-3 rounded cursor-pointer hover:bg-gray-50 ${
                  selectedGroupId === group.id ? 'bg-blue-50 border border-blue-200' : 'border'
                }`}
                onClick={() => setSelectedGroupId(group.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="font-medium">{group.name}</div>
                    {group.description && (
                      <div className="text-sm text-gray-600 mt-1">{group.description}</div>
                    )}
                    <div className="text-xs text-gray-500 mt-2 flex items-center gap-1">
                      <Users size={12} />
                      {group.dataset_count} dataset{group.dataset_count !== 1 ? 's' : ''}
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteGroup(group.id)
                    }}
                    className="p-1 hover:bg-red-100 rounded text-red-600"
                    title="Delete group"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Create Group Form */}
        {isCreating && (
          <div className="mt-4 p-4 border rounded bg-gray-50">
            <h4 className="font-medium mb-3">Create New Group</h4>
            <input
              type="text"
              placeholder="Group name"
              value={newGroupName}
              onChange={(e) => setNewGroupName(e.target.value)}
              className="w-full p-2 border rounded mb-2"
            />
            <textarea
              placeholder="Description (optional)"
              value={newGroupDescription}
              onChange={(e) => setNewGroupDescription(e.target.value)}
              className="w-full p-2 border rounded mb-2"
              rows={2}
            />
            <div className="flex gap-2">
              <button
                onClick={handleCreateGroup}
                disabled={!newGroupName.trim() || createGroup.isPending}
                className="flex-1 px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {createGroup.isPending ? 'Creating...' : 'Create'}
              </button>
              <button
                onClick={() => {
                  setIsCreating(false)
                  setNewGroupName('')
                  setNewGroupDescription('')
                }}
                className="px-3 py-2 border rounded hover:bg-gray-100"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Group Details */}
      <div className="flex-1">
        {selectedGroup ? (
          <div>
            <div className="mb-4">
              <h3 className="text-xl font-semibold">{selectedGroup.name}</h3>
              {selectedGroup.description && (
                <p className="text-gray-600 mt-1">{selectedGroup.description}</p>
              )}
            </div>

            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium">Datasets in this group</h4>
              <button
                onClick={() => setIsAddingDataset(true)}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                <Plus size={16} className="inline mr-1" />
                Add Dataset
              </button>
            </div>

            {selectedGroup.memberships.length === 0 ? (
              <div className="text-gray-500 text-sm border rounded p-4">
                No datasets in this group yet. Add datasets to enable multi-table queries.
              </div>
            ) : (
              <div className="space-y-2">
                {selectedGroup.memberships
                  .sort((a, b) => a.display_order - b.display_order)
                  .map((membership) => (
                    <div key={membership.id} className="flex items-center justify-between p-3 border rounded">
                      <div>
                        <div className="font-medium">{membership.dataset.name}</div>
                        {membership.alias && (
                          <div className="text-sm text-gray-600">
                            Alias: <code className="bg-gray-100 px-1 rounded">{membership.alias}</code>
                          </div>
                        )}
                        <div className="text-xs text-gray-500 mt-1">
                          {membership.dataset.row_count.toLocaleString()} rows
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveDataset(membership.dataset_id)}
                        className="p-2 hover:bg-red-100 rounded text-red-600"
                        title="Remove from group"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
              </div>
            )}

            {/* Add Dataset Dialog */}
            {isAddingDataset && (
              <div className="mt-4 p-4 border rounded bg-gray-50">
                <h4 className="font-medium mb-3">Add Dataset to Group</h4>
                {availableDatasets.length === 0 ? (
                  <div className="text-gray-500 text-sm">All datasets are already in this group.</div>
                ) : (
                  <div className="space-y-2">
                    {availableDatasets.map((dataset) => (
                      <div
                        key={dataset.id}
                        className="flex items-center justify-between p-2 border rounded bg-white hover:bg-gray-50"
                      >
                        <div>
                          <div className="font-medium">{dataset.name}</div>
                          <div className="text-xs text-gray-500">
                            {dataset.row_count.toLocaleString()} rows
                          </div>
                        </div>
                        <button
                          onClick={() => handleAddDataset(dataset.id)}
                          disabled={addDataset.isPending}
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                        >
                          Add
                        </button>
                      </div>
                    ))}
                  </div>
                )}
                <button
                  onClick={() => setIsAddingDataset(false)}
                  className="mt-3 px-3 py-2 border rounded hover:bg-gray-100 w-full"
                >
                  Close
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="text-gray-500 text-center py-12">
            Select a dataset group to view details
          </div>
        )}
      </div>
    </div>
  )
}
