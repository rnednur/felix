import { useState, useRef, useCallback, useEffect } from 'react'
import { CanvasItem, CanvasItemType } from '@/types/canvas'
import { QueryResultItem } from './QueryResultItem'
import { ChartItem } from './ChartItem'
import { CodeBlockItem } from './CodeBlockItem'
import { InsightNoteItem } from './InsightNoteItem'
import { Plus, Save, Download, Trash2, X } from 'lucide-react'

interface CanvasWorkspaceProps {
  workspaceId: string
  items: CanvasItem[]
  onItemsChange: (items: CanvasItem[]) => void
  onSave: (name: string, description?: string) => void
}

// Simplified draggable item component (proof of concept)
// In production, this would use your @rnednur/draggable-canvas package
function SimpleDraggableItem({
  item,
  onPositionChange,
  onSizeChange,
  onContentChange,
  onDelete
}: {
  item: CanvasItem
  onPositionChange: (id: string, x: number, y: number) => void
  onSizeChange: (id: string, width: number, height: number) => void
  onContentChange: (id: string, content: any) => void
  onDelete: (id: string) => void
}) {
  const [isDragging, setIsDragging] = useState(false)
  const [isResizing, setIsResizing] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [resizeStart, setResizeStart] = useState({ x: 0, y: 0, width: 0, height: 0 })
  const itemRef = useRef<HTMLDivElement>(null)

  const handleMouseDown = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement

    if (target.classList.contains('drag-handle')) {
      setIsDragging(true)
      setDragStart({
        x: e.clientX - item.x,
        y: e.clientY - item.y
      })
    } else if (target.classList.contains('resize-handle')) {
      e.stopPropagation()
      setIsResizing(true)
      setResizeStart({
        x: e.clientX,
        y: e.clientY,
        width: item.width,
        height: item.height
      })
    }
  }

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (isDragging) {
      const newX = e.clientX - dragStart.x
      const newY = e.clientY - dragStart.y
      onPositionChange(item.id, newX, newY)
    } else if (isResizing) {
      const deltaX = e.clientX - resizeStart.x
      const deltaY = e.clientY - resizeStart.y
      const newWidth = Math.max(200, resizeStart.width + deltaX)
      const newHeight = Math.max(150, resizeStart.height + deltaY)
      onSizeChange(item.id, newWidth, newHeight)
    }
  }, [isDragging, isResizing, dragStart, resizeStart, item.id, onPositionChange, onSizeChange])

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
    setIsResizing(false)
  }, [])

  // Add/remove event listeners
  useEffect(() => {
    if (isDragging || isResizing) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging, isResizing, handleMouseMove, handleMouseUp])

  const renderContent = () => {
    switch (item.type) {
      case 'query-result':
        return <QueryResultItem
          content={item.content as any}
          onTitleChange={(newTitle) => {
            const updatedContent = { ...item.content as any, title: newTitle }
            onContentChange(item.id, updatedContent)
          }}
        />
      case 'chart':
        return <ChartItem
          content={item.content as any}
          onTitleChange={(newTitle) => {
            const updatedContent = { ...item.content as any, title: newTitle }
            onContentChange(item.id, updatedContent)
          }}
        />
      case 'code-block':
        return <CodeBlockItem content={item.content as any} />
      case 'insight-note':
        return <InsightNoteItem content={item.content as any} />
      default:
        return <div>Unknown item type</div>
    }
  }

  return (
    <div
      ref={itemRef}
      className="absolute border-2 border-gray-300 rounded-lg shadow-lg overflow-hidden bg-white"
      style={{
        left: item.x,
        top: item.y,
        width: item.width,
        height: item.height,
        zIndex: item.zIndex,
        cursor: isDragging ? 'grabbing' : isResizing ? 'se-resize' : 'auto'
      }}
      onMouseDown={handleMouseDown}
    >
      {/* Drag handle */}
      <div className="drag-handle absolute top-0 left-0 right-0 h-10 bg-gradient-to-r from-blue-50 to-gray-50 border-b-2 border-blue-200 cursor-grab active:cursor-grabbing flex items-center justify-between px-4 hover:bg-blue-100 transition-colors">
        <div className="flex items-center gap-2">
          <div className="flex flex-col gap-1">
            <div className="w-4 h-0.5 bg-gray-400 rounded"></div>
            <div className="w-4 h-0.5 bg-gray-400 rounded"></div>
            <div className="w-4 h-0.5 bg-gray-400 rounded"></div>
          </div>
          <span className="text-xs font-medium text-gray-700">Drag to move</span>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onDelete(item.id)
          }}
          className="text-gray-400 hover:text-red-600 hover:bg-red-50 rounded px-2 py-1 transition-colors font-bold text-lg"
        >
          ×
        </button>
      </div>

      {/* Content */}
      <div className="mt-10 h-[calc(100%-2.5rem)] overflow-hidden">
        {renderContent()}
      </div>

      {/* Resize Handle */}
      <div
        className="resize-handle absolute bottom-0 right-0 w-6 h-6 cursor-se-resize"
        style={{
          background: 'linear-gradient(135deg, transparent 50%, #3b82f6 50%)',
        }}
        title="Drag to resize"
      >
        <div className="absolute bottom-1 right-1 w-1 h-1 bg-white rounded-full"></div>
      </div>
    </div>
  )
}

export function CanvasWorkspace({
  workspaceId,
  items,
  onItemsChange,
  onSave
}: CanvasWorkspaceProps) {
  const canvasRef = useRef<HTMLDivElement>(null)
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [workspaceName, setWorkspaceName] = useState('')
  const [workspaceDescription, setWorkspaceDescription] = useState('')

  const handlePositionChange = (id: string, x: number, y: number) => {
    const updatedItems = items.map(item =>
      item.id === id ? { ...item, x, y } : item
    )
    onItemsChange(updatedItems)
  }

  const handleSizeChange = (id: string, width: number, height: number) => {
    const updatedItems = items.map(item =>
      item.id === id ? { ...item, width, height } : item
    )
    onItemsChange(updatedItems)
  }

  const handleContentChange = (id: string, content: any) => {
    const updatedItems = items.map(item =>
      item.id === id ? { ...item, content } : item
    )
    onItemsChange(updatedItems)
  }

  const handleDelete = (id: string) => {
    const updatedItems = items.filter(item => item.id !== id)
    onItemsChange(updatedItems)
  }

  const handleSaveClick = () => {
    setShowSaveDialog(true)
  }

  const handleSaveWorkspace = () => {
    if (workspaceName.trim()) {
      onSave(workspaceName.trim(), workspaceDescription.trim() || undefined)
      setShowSaveDialog(false)
      setWorkspaceName('')
      setWorkspaceDescription('')
    }
  }

  return (
    <>
      {/* Save Dialog */}
      {showSaveDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Save Workspace</h3>
              <button
                onClick={() => setShowSaveDialog(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Workspace Name *
                </label>
                <input
                  type="text"
                  value={workspaceName}
                  onChange={(e) => setWorkspaceName(e.target.value)}
                  placeholder="e.g., Sales Analysis Q1 2024"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description (optional)
                </label>
                <textarea
                  value={workspaceDescription}
                  onChange={(e) => setWorkspaceDescription(e.target.value)}
                  placeholder="Brief description of this analysis..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-800">
                  💡 <strong>{items.length} items</strong> will be saved in this workspace
                </p>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setShowSaveDialog(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveWorkspace}
                  disabled={!workspaceName.trim()}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  Save Workspace
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="h-full flex flex-col bg-gray-50">
      {/* Toolbar */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
        <h2 className="text-lg font-semibold text-gray-800">Canvas Workspace</h2>
        <span className="text-sm text-gray-500">
          {items.length} {items.length === 1 ? 'item' : 'items'}
        </span>
        <div className="ml-auto flex gap-2">
          {items.length > 0 && (
            <button
              onClick={() => {
                if (confirm('Clear all items from canvas?')) {
                  onItemsChange([])
                }
              }}
              className="flex items-center gap-2 px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100"
            >
              <Trash2 className="h-4 w-4" />
              Clear All
            </button>
          )}
          <button
            onClick={handleSaveClick}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Save className="h-4 w-4" />
            Save
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
            <Download className="h-4 w-4" />
            Export
          </button>
        </div>
      </div>

      {/* Canvas */}
      <div
        ref={canvasRef}
        className="flex-1 relative overflow-auto"
        style={{
          backgroundImage: `
            linear-gradient(rgba(0, 0, 0, 0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 0, 0, 0.05) 1px, transparent 1px)
          `,
          backgroundSize: '20px 20px'
        }}
      >
        {items.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <Plus className="h-12 w-12 mx-auto mb-2 text-gray-400" />
              <p className="text-lg font-medium">No items yet</p>
              <p className="text-sm mt-1">Ask a question in the chat to add items to the canvas</p>
            </div>
          </div>
        ) : (
          items.map(item => (
            <SimpleDraggableItem
              key={item.id}
              item={item}
              onPositionChange={handlePositionChange}
              onSizeChange={handleSizeChange}
              onContentChange={handleContentChange}
              onDelete={handleDelete}
            />
          ))
        )}
      </div>
    </div>
    </>
  )
}
