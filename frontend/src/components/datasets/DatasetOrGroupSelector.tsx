import { useState } from 'react'
import { Database, Users, ChevronDown } from 'lucide-react'
import { useDatasets } from '@/hooks/useDatasets'
import { useDatasetGroups } from '@/hooks/useDatasetGroups'

interface DatasetOrGroupSelectorProps {
  selectedDatasetId?: string
  selectedGroupId?: string
  onSelect: (selection: { datasetId?: string; groupId?: string }) => void
  className?: string
}

export function DatasetOrGroupSelector({
  selectedDatasetId,
  selectedGroupId,
  onSelect,
  className = '',
}: DatasetOrGroupSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const { data: datasets = [] } = useDatasets()
  const { data: groups = [] } = useDatasetGroups()

  const selectedDataset = datasets.find((d) => d.id === selectedDatasetId)
  const selectedGroup = groups.find((g) => g.id === selectedGroupId)

  const displayText = selectedDataset
    ? selectedDataset.name
    : selectedGroup
    ? `${selectedGroup.name} (${selectedGroup.dataset_count} datasets)`
    : 'Select dataset or group'

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-2 border rounded-lg hover:bg-gray-50"
      >
        <div className="flex items-center gap-2">
          {selectedDataset ? (
            <Database size={16} className="text-gray-500" />
          ) : selectedGroup ? (
            <Users size={16} className="text-gray-500" />
          ) : (
            <Database size={16} className="text-gray-400" />
          )}
          <span className={selectedDataset || selectedGroup ? '' : 'text-gray-400'}>
            {displayText}
          </span>
        </div>
        <ChevronDown size={16} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute z-10 mt-1 w-full bg-white border rounded-lg shadow-lg max-h-96 overflow-y-auto">
          {/* Single Datasets Section */}
          <div className="p-2 border-b bg-gray-50">
            <div className="text-xs font-semibold text-gray-600 px-2 py-1 flex items-center gap-1">
              <Database size={12} />
              SINGLE DATASETS
            </div>
          </div>
          <div className="p-2">
            {datasets.length === 0 ? (
              <div className="text-sm text-gray-500 px-2 py-2">No datasets available</div>
            ) : (
              datasets.map((dataset) => (
                <button
                  key={dataset.id}
                  onClick={() => {
                    onSelect({ datasetId: dataset.id })
                    setIsOpen(false)
                  }}
                  className={`w-full text-left px-3 py-2 rounded hover:bg-gray-100 ${
                    selectedDatasetId === dataset.id ? 'bg-blue-50 text-blue-700' : ''
                  }`}
                >
                  <div className="font-medium">{dataset.name}</div>
                  <div className="text-xs text-gray-500">
                    {dataset.row_count.toLocaleString()} rows
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Dataset Groups Section */}
          <div className="p-2 border-t bg-gray-50">
            <div className="text-xs font-semibold text-gray-600 px-2 py-1 flex items-center gap-1">
              <Users size={12} />
              DATASET GROUPS
            </div>
          </div>
          <div className="p-2">
            {groups.length === 0 ? (
              <div className="text-sm text-gray-500 px-2 py-2">
                No dataset groups. Create a group to query multiple datasets together.
              </div>
            ) : (
              groups.map((group) => (
                <button
                  key={group.id}
                  onClick={() => {
                    onSelect({ groupId: group.id })
                    setIsOpen(false)
                  }}
                  className={`w-full text-left px-3 py-2 rounded hover:bg-gray-100 ${
                    selectedGroupId === group.id ? 'bg-blue-50 text-blue-700' : ''
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Users size={14} />
                    <div>
                      <div className="font-medium">{group.name}</div>
                      <div className="text-xs text-gray-500">
                        {group.dataset_count} dataset{group.dataset_count !== 1 ? 's' : ''}
                      </div>
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
