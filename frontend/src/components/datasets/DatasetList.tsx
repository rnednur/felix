import { Link } from 'react-router-dom'
import { useDatasets } from '@/hooks/useDatasets'
import { formatDistanceToNow } from 'date-fns'

export function DatasetList() {
  const { data: datasets, isLoading } = useDatasets()

  if (isLoading) {
    return <div className="text-center py-8">Loading datasets...</div>
  }

  if (!datasets || datasets.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No datasets yet. Upload your first one above!</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {datasets.map((dataset) => (
        <Link
          key={dataset.id}
          to={`/datasets/${dataset.id}`}
          className="block p-6 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 truncate">
                {dataset.name}
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                {dataset.row_count.toLocaleString()} rows
              </p>
            </div>
            <span className={`
              px-2 py-1 text-xs font-medium rounded
              ${dataset.status === 'READY' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}
            `}>
              {dataset.status}
            </span>
          </div>

          <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
            <span>{dataset.source_type}</span>
            <span>
              {formatDistanceToNow(new Date(dataset.created_at), { addSuffix: true })}
            </span>
          </div>
        </Link>
      ))}
    </div>
  )
}
