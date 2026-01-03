import { useState, useEffect, useCallback, useRef } from 'react'
import { CanvasItem, AGUIEvent, CanvasItemCreateEvent } from '@/types/canvas'

interface UseAGUIStreamProps {
  workspaceId: string
  datasetId?: string
  datasetGroupId?: string
  onItemCreate: (item: Partial<CanvasItem>) => void
  onComplete: () => void
  onError: (error: string) => void
}

interface StreamState {
  isStreaming: boolean
  currentMessage: string
  events: AGUIEvent[]
}

export function useAGUIStream({
  workspaceId,
  datasetId,
  datasetGroupId,
  onItemCreate,
  onComplete,
  onError
}: UseAGUIStreamProps) {
  const [state, setState] = useState<StreamState>({
    isStreaming: false,
    currentMessage: '',
    events: []
  })
  const eventSourceRef = useRef<EventSource | null>(null)
  const itemCounterRef = useRef(0)

  const startStream = useCallback((message: string) => {
    if (state.isStreaming) {
      console.warn('Stream already in progress')
      return
    }

    setState(prev => ({
      ...prev,
      isStreaming: true,
      currentMessage: message,
      events: []
    }))

    // Create query params
    const params = new URLSearchParams({
      workspace_id: workspaceId,
      message: message
    })
    if (datasetId) params.append('dataset_id', datasetId)
    if (datasetGroupId) params.append('dataset_group_id', datasetGroupId)

    // Add auth token to query params (EventSource doesn't support custom headers)
    const token = localStorage.getItem('access_token')
    if (token) {
      params.append('token', token)
    }

    const url = `http://localhost:8000/api/v1/canvas/stream?${params.toString()}`

    try {
      const eventSource = new EventSource(url)
      eventSourceRef.current = eventSource

      eventSource.addEventListener('agent.thinking', (e) => {
        const data = JSON.parse(e.data)
        console.log('Agent thinking:', data)
        setState(prev => ({
          ...prev,
          events: [...prev.events, { event: 'agent.thinking', data }]
        }))
      })

      eventSource.addEventListener('agent.tool.use', (e) => {
        const data = JSON.parse(e.data)
        console.log('Tool use:', data)
        setState(prev => ({
          ...prev,
          events: [...prev.events, { event: 'agent.tool.use', data }]
        }))
      })

      eventSource.addEventListener('agent.tool.result', (e) => {
        const data = JSON.parse(e.data)
        console.log('Tool result:', data)
        setState(prev => ({
          ...prev,
          events: [...prev.events, { event: 'agent.tool.result', data }]
        }))
      })

      eventSource.addEventListener('canvas.item.create', (e) => {
        const data: CanvasItemCreateEvent = JSON.parse(e.data)
        console.log('Canvas item create:', data)

        // Generate unique ID for the item
        const itemId = `item-${Date.now()}-${itemCounterRef.current++}`

        // Create canvas item from event data
        const canvasItem: Partial<CanvasItem> = {
          id: itemId,
          workspaceId,
          type: data.itemType,
          x: data.position.x,
          y: data.position.y,
          width: data.width,
          height: data.height,
          zIndex: 0,
          content: data.content as any
        }

        onItemCreate(canvasItem)

        setState(prev => ({
          ...prev,
          events: [...prev.events, { event: 'canvas.item.create', data }]
        }))
      })

      eventSource.addEventListener('agent.complete', (e) => {
        const data = JSON.parse(e.data)
        console.log('Agent complete:', data)
        setState(prev => ({
          ...prev,
          isStreaming: false,
          events: [...prev.events, { event: 'agent.complete', data }]
        }))
        eventSource.close()
        onComplete()
      })

      eventSource.addEventListener('error', (e) => {
        console.error('SSE error:', e)
        const data = (e as any).data ? JSON.parse((e as any).data) : { message: 'Stream error' }
        onError(data.message || 'Unknown error')
        setState(prev => ({
          ...prev,
          isStreaming: false
        }))
        eventSource.close()
      })

      eventSource.onerror = (error) => {
        console.error('EventSource error:', error)
        onError('Connection error')
        setState(prev => ({
          ...prev,
          isStreaming: false
        }))
        eventSource.close()
      }

    } catch (error) {
      console.error('Failed to start stream:', error)
      onError('Failed to start stream')
      setState(prev => ({
        ...prev,
        isStreaming: false
      }))
    }
  }, [workspaceId, datasetId, datasetGroupId, onItemCreate, onComplete, onError, state.isStreaming])

  const stopStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setState(prev => ({
      ...prev,
      isStreaming: false
    }))
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [])

  return {
    isStreaming: state.isStreaming,
    currentMessage: state.currentMessage,
    events: state.events,
    startStream,
    stopStream
  }
}
