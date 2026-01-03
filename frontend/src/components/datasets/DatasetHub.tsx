import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useDatasets, useDeleteDataset } from '@/hooks/useDatasets'
import { useDatasetGroups, useDeleteDatasetGroup } from '@/hooks/useDatasetGroups'
import { formatDistanceToNow } from 'date-fns'
import {
  Database,
  Users,
  Upload,
  FolderPlus,
  Trash2,
  CheckCircle,
  AlertCircle,
  Clock,
  XCircle,
} from 'lucide-react'
import { DatasetUploader } from './DatasetUploader'

type FilterType = 'all' | 'datasets' | 'groups'

export function DatasetHub() {
  const [filter, setFilter] = useState<FilterType>('all')
  const [showUploader, setShowUploader] = useState(false)
  const navigate = useNavigate()

  const { data: datasets = [], isLoading: datasetsLoading } = useDatasets()
  const { data: groups = [], isLoading: groupsLoading } = useDatasetGroups()
  const deleteDataset = useDeleteDataset()
  const deleteGroup = useDeleteDatasetGroup()

  const isLoading = datasetsLoading || groupsLoading

  // Calculate health score for datasets
  const getHealthScore = (dataset: any) => {
    if (dataset.status !== 'READY') return 0
    // Simple health calculation based on completeness
    let score = 80
    if (dataset.description) score += 10
    if (dataset.row_count > 0) score += 10
    return score
  }

  const getHealthColor = (score: number) => {
    if (score >= 90) return 'text-green-600 bg-green-50 border-green-200'
    if (score >= 60) return 'text-yellow-600 bg-yellow-50 border-yellow-200'
    return 'text-red-600 bg-red-50 border-red-200'
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'READY':
        return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'PROCESSING':
        return <Clock className="w-4 h-4 text-yellow-600" />
      case 'FAILED':
        return <XCircle className="w-4 h-4 text-red-600" />
      default:
        return <AlertCircle className="w-4 h-4 text-gray-600" />
    }
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i)) + ' ' + sizes[i]
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-display font-semibold text-slate-900 tracking-tight">Dataset Hub</h1>
          <p className="mt-2 text-slate-600 font-medium">
            Manage your datasets and dataset groups
          </p>
        </div>
      </div>

      {/* Action Bar */}
      <div className="flex items-center justify-between bg-card rounded-xl shadow-sm border border-border p-4 transition-shadow hover:shadow-md">
        <div className="flex gap-2">
          <button
            onClick={() => setShowUploader(!showUploader)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Upload className="w-4 h-4" />
            Upload New Dataset
          </button>
          <button
            onClick={() => navigate('/dataset-groups/new')}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <FolderPlus className="w-4 h-4" />
            Create Group
          </button>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              filter === 'all'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            All Datasets
          </button>
          <button
            onClick={() => setFilter('groups')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              filter === 'groups'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Groups
          </button>
          <button
            onClick={() => setFilter('datasets')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              filter === 'datasets'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Single Datasets
          </button>
        </div>

        <div className="text-sm text-gray-500">
          Status: <span className="font-medium text-gray-900">All</span>
        </div>
      </div>

      {/* Uploader */}
      {showUploader && (
        <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 p-6">
          <DatasetUploader />
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading...</p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && datasets.length === 0 && groups.length === 0 && (
        <div className="text-center py-16 bg-white rounded-lg border-2 border-dashed border-gray-300">
          <Database className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">No datasets yet</h3>
          <p className="mt-2 text-gray-500">
            Get started by uploading your first dataset or creating a dataset group
          </p>
          <button
            onClick={() => setShowUploader(true)}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Upload Dataset
          </button>
        </div>
      )}

      {/* Grid of Cards */}
      {!isLoading && (datasets.length > 0 || groups.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Dataset Group Cards */}
          {(filter === 'all' || filter === 'groups') &&
            groups.map((group) => (
              <div
                key={group.id}
                className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow overflow-hidden"
              >
                <div className="p-6">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <div className="p-2 bg-purple-50 rounded-lg">
                        <Users className="w-5 h-5 text-purple-600" />
                      </div>
                      <div>
                        <div className="text-xs font-semibold text-purple-600 uppercase tracking-wide">
                          Dataset Group
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Title */}
                  <h3 className="text-lg font-semibold text-gray-900 mb-2 truncate">
                    {group.name}
                  </h3>

                  {/* Description */}
                  {group.description && (
                    <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                      {group.description}
                    </p>
                  )}

                  {/* Stats */}
                  <div className="flex items-center gap-4 text-sm text-gray-600 mb-4">
                    <div className="flex items-center gap-1">
                      <Users className="w-4 h-4" />
                      <span>
                        {group.dataset_count} dataset{group.dataset_count !== 1 ? 's' : ''}
                      </span>
                    </div>
                  </div>

                  {/* Metadata */}
                  <div className="text-xs text-gray-500 mb-4">
                    Created {formatDistanceToNow(new Date(group.created_at), { addSuffix: true })}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Link
                      to={`/dataset-groups/${group.id}`}
                      className="flex-1 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors text-center"
                    >
                      Analyze Now
                    </Link>
                    <button
                      onClick={(e) => {
                        e.preventDefault()
                        if (confirm('Delete this group? Datasets will not be deleted.')) {
                          deleteGroup.mutate(group.id)
                        }
                      }}
                      disabled={deleteGroup.isPending}
                      className="p-2 border border-gray-300 rounded-lg hover:bg-red-50 hover:border-red-300 transition-colors disabled:opacity-50"
                      title="Delete group"
                    >
                      <Trash2 className="w-4 h-4 text-gray-600 hover:text-red-600" />
                    </button>
                  </div>
                </div>
              </div>
            ))}

          {/* Dataset Cards */}
          {(filter === 'all' || filter === 'datasets') &&
            datasets.map((dataset) => {
              const healthScore = getHealthScore(dataset)
              const healthColorClass = getHealthColor(healthScore)

              return (
                <div
                  key={dataset.id}
                  className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow overflow-hidden"
                >
                  <div className="p-6">
                    {/* Header with Health Score */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <div className="p-2 bg-blue-50 rounded-lg">
                          <Database className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                          <div className="text-xs font-semibold text-blue-600 uppercase tracking-wide">
                            Dataset
                          </div>
                        </div>
                      </div>
                      <div className={`flex items-center gap-1 px-2 py-1 rounded-full border ${healthColorClass}`}>
                        <span className="text-sm font-semibold">{healthScore}%</span>
                        <span className="text-xs">Health</span>
                        {getStatusIcon(dataset.status)}
                      </div>
                    </div>

                    {/* Title */}
                    <h3 className="text-lg font-semibold text-gray-900 mb-2 truncate">
                      {dataset.name}
                    </h3>

                    {/* Description */}
                    {dataset.description ? (
                      <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                        {dataset.description}
                      </p>
                    ) : (
                      <p className="text-sm text-gray-400 mb-4 italic">
                        No description available
                      </p>
                    )}

                    {/* Stats */}
                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
                          Rows
                        </div>
                        <div className="text-sm font-semibold text-gray-900">
                          {dataset.row_count.toLocaleString()}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
                          Size
                        </div>
                        <div className="text-sm font-semibold text-gray-900">
                          {formatBytes(dataset.size_bytes)}
                        </div>
                      </div>
                    </div>

                    {/* Metadata */}
                    <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
                      <span className="px-2 py-1 bg-gray-100 rounded">
                        {dataset.source_type}
                      </span>
                      <span>
                        {formatDistanceToNow(new Date(dataset.created_at), { addSuffix: true })}
                      </span>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2">
                      <Link
                        to={`/datasets/${dataset.id}`}
                        className={`flex-1 px-4 py-2 text-sm font-medium rounded-lg transition-colors text-center ${
                          dataset.status === 'READY'
                            ? 'bg-blue-600 text-white hover:bg-blue-700'
                            : 'bg-gray-300 text-gray-600 cursor-not-allowed'
                        }`}
                      >
                        {dataset.status === 'READY' ? 'Analyze Now' : 'Processing...'}
                      </Link>
                      <button
                        onClick={(e) => {
                          e.preventDefault()
                          if (confirm('Delete this dataset? This action cannot be undone.')) {
                            deleteDataset.mutate(dataset.id)
                          }
                        }}
                        disabled={deleteDataset.isPending}
                        className="p-2 border border-gray-300 rounded-lg hover:bg-red-50 hover:border-red-300 transition-colors disabled:opacity-50"
                        title="Delete dataset"
                      >
                        <Trash2 className="w-4 h-4 text-gray-600 hover:text-red-600" />
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
        </div>
      )}
    </div>
  )
}
