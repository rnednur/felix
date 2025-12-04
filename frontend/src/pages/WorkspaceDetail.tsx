import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { DataWorkspaceLayout } from '@/components/layout/DataWorkspaceLayout'
import { CanvasWorkspace } from '@/components/canvas/CanvasWorkspace'
import { useAGUIStream } from '@/hooks/useAGUIStream'
import { CanvasItem, Workspace } from '@/types/canvas'
import { Send, Loader2 } from 'lucide-react'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api/v1'

export default function WorkspaceDetail() {
  const { id } = useParams<{ id: string }>()
  const [workspace, setWorkspace] = useState<Workspace | null>(null)
  const [items, setItems] = useState<CanvasItem[]>([])
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const { isStreaming, startStream } = useAGUIStream({
    workspaceId: id || '',
    datasetId: workspace?.datasetId,
    datasetGroupId: workspace?.datasetGroupId,
    onItemCreate: (item) => {
      setItems(prev => [...prev, item as CanvasItem])
    },
    onComplete: () => {
      console.log('Stream completed')
    },
    onError: (err) => {
      setError(err)
    }
  })

  // Load workspace
  useEffect(() => {
    if (!id) return

    const loadWorkspace = async () => {
      try {
        setIsLoading(true)
        const response = await axios.get(`${API_BASE_URL}/workspaces/${id}`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
          }
        })
        setWorkspace(response.data)
        setItems(response.data.items || [])
      } catch (err: any) {
        setError(err.message)
      } finally {
        setIsLoading(false)
      }
    }

    loadWorkspace()
  }, [id])

  const handleSendQuery = () => {
    if (!query.trim() || isStreaming) return
    startStream(query)
    setQuery('')
  }

  const handleSaveWorkspace = async () => {
    if (!id) return

    try {
      // Save items to backend
      await axios.put(
        `${API_BASE_URL}/workspaces/${id}`,
        {
          name: workspace?.name,
          description: workspace?.description
        },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      )

      // Save each item
      for (const item of items) {
        if (item.id.startsWith('item-')) {
          // New item, create it
          await axios.post(
            `${API_BASE_URL}/workspaces/${id}/items`,
            {
              type: item.type,
              x: item.x,
              y: item.y,
              width: item.width,
              height: item.height,
              z_index: item.zIndex,
              content: item.content
            },
            {
              headers: {
                Authorization: `Bearer ${localStorage.getItem('access_token')}`
              }
            }
          )
        } else {
          // Existing item, update it
          await axios.put(
            `${API_BASE_URL}/workspaces/${id}/items/${item.id}`,
            {
              x: item.x,
              y: item.y,
              width: item.width,
              height: item.height,
              z_index: item.zIndex,
              content: item.content
            },
            {
              headers: {
                Authorization: `Bearer ${localStorage.getItem('access_token')}`
              }
            }
          )
        }
      }

      alert('Workspace saved!')
    } catch (err: any) {
      setError(err.message)
    }
  }

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 font-medium">Error</p>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    )
  }

  const sidebar = (
    <div className="flex flex-col h-full bg-white">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-800">Chat</h2>
        <p className="text-sm text-gray-600">Ask questions to add items to canvas</p>
      </div>

      <div className="flex-1 overflow-auto p-4">
        {/* Message history would go here */}
      </div>

      <div className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendQuery()}
            placeholder="Ask a question..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isStreaming}
          />
          <button
            onClick={handleSendQuery}
            disabled={isStreaming || !query.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {isStreaming ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  )

  const header = (
    <div className="px-6 py-4">
      <h1 className="text-xl font-bold text-gray-900">{workspace?.name || 'Workspace'}</h1>
      {workspace?.description && (
        <p className="text-sm text-gray-600 mt-1">{workspace.description}</p>
      )}
    </div>
  )

  return (
    <DataWorkspaceLayout
      sidebar={sidebar}
      header={header}
    >
      <CanvasWorkspace
        workspaceId={id || ''}
        items={items}
        onItemsChange={setItems}
        onSave={handleSaveWorkspace}
      />
    </DataWorkspaceLayout>
  )
}
