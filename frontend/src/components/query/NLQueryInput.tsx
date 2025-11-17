import { useState } from 'react'
import { useNLQuery } from '@/hooks/useQuery'

interface Props {
  datasetId: string
  onSuccess: (result: any) => void
}

export function NLQueryInput({ datasetId, onSuccess }: Props) {
  const [query, setQuery] = useState('')
  const queryMutation = useNLQuery()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      queryMutation.mutate(
        { datasetId, query },
        {
          onSuccess: (data) => {
            onSuccess(data)
            setQuery('')
          },
        }
      )
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question about your data... (e.g., 'show top 10 by revenue')"
          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={queryMutation.isPending}
        />
        <button
          type="submit"
          disabled={queryMutation.isPending || !query.trim()}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {queryMutation.isPending ? 'Running...' : 'Ask'}
        </button>
      </div>

      {queryMutation.isError && (
        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
          {queryMutation.error instanceof Error
            ? queryMutation.error.message
            : 'Query failed'}
        </div>
      )}
    </form>
  )
}
