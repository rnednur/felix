import { useState, useRef, useCallback, useEffect } from 'react'
import { CanvasItem, KPICardContent } from '@/types/canvas'
import { QueryResultItem } from './QueryResultItem'
import { ChartItem } from './ChartItem'
import { CodeBlockItem } from './CodeBlockItem'
import { InsightNoteItem } from './InsightNoteItem'
import { KPICard } from './KPICard'
import { DashboardGridView } from './DashboardGridView'
import { ExportDialog } from '@/components/export/ExportDialog'
import { ThemeExtractor } from '@/components/theming/ThemeExtractor'
import { Plus, Save, Download, Trash2, X, FolderOpen, LayoutGrid, Palette, Move, LayoutDashboard, Edit2, Check } from 'lucide-react'

type ViewMode = 'canvas' | 'dashboard'

interface CanvasWorkspaceProps {
  workspaceId: string
  items: CanvasItem[]
  title?: string
  onTitleChange?: (title: string) => void
  onItemsChange: (items: CanvasItem[]) => void
  onSave: (name: string, description?: string) => void
  onLoad?: () => void
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
          chartId={item.id}
          onTitleChange={(newTitle) => {
            const updatedContent = { ...item.content as any, title: newTitle }
            onContentChange(item.id, updatedContent)
          }}
        />
      case 'code-block':
        return <CodeBlockItem content={item.content as any} />
      case 'insight-note':
        return <InsightNoteItem content={item.content as any} />
      case 'kpi-card':
        return <KPICard content={item.content as KPICardContent} />
      default:
        return <div>Unknown item type</div>
    }
  }

  return (
    <div
      ref={itemRef}
      className="absolute rounded-xl overflow-hidden bg-white group/item shadow-[0_2px_8px_-2px_rgba(0,0,0,0.08),0_4px_12px_-4px_rgba(0,0,0,0.06)] hover:shadow-[0_4px_16px_-2px_rgba(0,0,0,0.1),0_8px_24px_-4px_rgba(0,0,0,0.08)] transition-shadow duration-200"
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
      {/* Subtle drag handle - appears on hover */}
      <div className="drag-handle absolute top-0 left-0 right-0 h-8 cursor-grab active:cursor-grabbing flex items-center justify-between px-3 bg-gradient-to-b from-slate-100/80 to-transparent opacity-0 group-hover/item:opacity-100 transition-opacity z-10">
        <div className="flex items-center gap-1.5">
          <div className="flex gap-0.5">
            <div className="w-1 h-1 bg-slate-400 rounded-full"></div>
            <div className="w-1 h-1 bg-slate-400 rounded-full"></div>
            <div className="w-1 h-1 bg-slate-400 rounded-full"></div>
          </div>
          <div className="flex gap-0.5">
            <div className="w-1 h-1 bg-slate-400 rounded-full"></div>
            <div className="w-1 h-1 bg-slate-400 rounded-full"></div>
            <div className="w-1 h-1 bg-slate-400 rounded-full"></div>
          </div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onDelete(item.id)
          }}
          className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      {/* Content - no offset needed anymore */}
      <div className="h-full overflow-hidden">
        {renderContent()}
      </div>

      {/* Subtle resize handle */}
      <div
        className="resize-handle absolute bottom-0 right-0 w-5 h-5 cursor-se-resize opacity-0 group-hover/item:opacity-100 transition-opacity"
        title="Drag to resize"
      >
        <svg className="absolute bottom-1 right-1 h-3 w-3 text-slate-400" viewBox="0 0 24 24" fill="currentColor">
          <path d="M22 22H20V20H22V22ZM22 18H20V16H22V18ZM18 22H16V20H18V22ZM22 14H20V12H22V14ZM18 18H16V16H18V18ZM14 22H12V20H14V22Z" />
        </svg>
      </div>
    </div>
  )
}

export function CanvasWorkspace({
  workspaceId,
  items,
  title,
  onTitleChange,
  onItemsChange,
  onSave,
  onLoad
}: CanvasWorkspaceProps) {
  const canvasRef = useRef<HTMLDivElement>(null)
  const exportCanvasRef = useRef<HTMLDivElement>(null)
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [showThemeExtractor, setShowThemeExtractor] = useState(false)
  const [workspaceName, setWorkspaceName] = useState('')
  const [workspaceDescription, setWorkspaceDescription] = useState('')
  const [viewMode, setViewMode] = useState<ViewMode>('dashboard')
  const [isEditingTitle, setIsEditingTitle] = useState(false)
  const [editedTitle, setEditedTitle] = useState('')
  const titleInputRef = useRef<HTMLInputElement>(null)

  // Focus input when editing starts
  useEffect(() => {
    if (isEditingTitle && titleInputRef.current) {
      titleInputRef.current.focus()
      titleInputRef.current.select()
    }
  }, [isEditingTitle])

  const handleStartEditingTitle = () => {
    setEditedTitle(title || `${viewMode === 'dashboard' ? 'Dashboard' : 'Canvas'} Workspace`)
    setIsEditingTitle(true)
  }

  const handleSaveTitle = () => {
    if (editedTitle.trim() && onTitleChange) {
      onTitleChange(editedTitle.trim())
    }
    setIsEditingTitle(false)
  }

  const handleCancelEditingTitle = () => {
    setIsEditingTitle(false)
    setEditedTitle('')
  }

  const handleTitleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSaveTitle()
    } else if (e.key === 'Escape') {
      handleCancelEditingTitle()
    }
  }

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

  const handleAutoArrange = () => {
    if (items.length === 0) return

    // Group items by question (headers with their related items)
    const groups: CanvasItem[][] = []
    let currentGroup: CanvasItem[] = []

    items.forEach(item => {
      const isHeader = item.type === 'insight-note' &&
                      (item.content as any)?.tags?.includes('query-header')

      if (isHeader && currentGroup.length > 0) {
        groups.push(currentGroup)
        currentGroup = [item]
      } else {
        currentGroup.push(item)
      }
    })
    if (currentGroup.length > 0) groups.push(currentGroup)

    // Arrange each group with proper spacing
    let currentY = 50
    const arrangedItems: CanvasItem[] = []

    groups.forEach(group => {
      // Find header, code, results, and charts
      const header = group.find(i => i.type === 'insight-note' && (i.content as any)?.tags?.includes('query-header'))
      const code = group.find(i => i.type === 'code-block')
      const results = group.find(i => i.type === 'query-result')
      const charts = group.filter(i => i.type === 'chart')

      // Position header
      if (header) {
        arrangedItems.push({ ...header, x: 50, y: currentY, width: 1400, height: 80 })
        currentY += 100
      }

      // Position code and results side by side
      if (code) {
        arrangedItems.push({ ...code, x: 50, y: currentY, width: 600, height: 250 })
      }
      if (results) {
        arrangedItems.push({ ...results, x: 700, y: currentY, width: 700, height: 400 })
      }
      currentY += 270

      // Position charts in a row
      charts.forEach((chart, i) => {
        arrangedItems.push({
          ...chart,
          x: 50 + (i * 650),
          y: currentY,
          width: 600,
          height: 400
        })
      })

      if (charts.length > 0) currentY += 450

      // Add spacing between groups
      currentY += 100
    })

    onItemsChange(arrangedItems)
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

      <div className="h-full flex flex-col bg-slate-50">
      {/* Toolbar */}
      <div className="bg-white border-b border-slate-200 px-4 py-3 flex items-center gap-3">
        {/* Editable Title */}
        {isEditingTitle ? (
          <div className="flex items-center gap-2">
            <input
              ref={titleInputRef}
              type="text"
              value={editedTitle}
              onChange={(e) => setEditedTitle(e.target.value)}
              onKeyDown={handleTitleKeyDown}
              onBlur={handleSaveTitle}
              className="text-lg font-semibold text-slate-800 bg-slate-100 border border-slate-300 rounded-lg px-3 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent min-w-[200px]"
              placeholder="Enter title..."
            />
            <button
              onClick={handleSaveTitle}
              className="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
              title="Save title"
            >
              <Check className="h-4 w-4" />
            </button>
            <button
              onClick={handleCancelEditingTitle}
              className="p-1.5 text-slate-400 hover:bg-slate-100 rounded-lg transition-colors"
              title="Cancel"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-2 group/title">
            <h2 className="text-lg font-semibold text-slate-800">
              {title || `${viewMode === 'dashboard' ? 'Dashboard' : 'Canvas'} Workspace`}
            </h2>
            {onTitleChange && (
              <button
                onClick={handleStartEditingTitle}
                className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors opacity-0 group-hover/title:opacity-100"
                title="Edit title"
              >
                <Edit2 className="h-4 w-4" />
              </button>
            )}
          </div>
        )}
        <span className="text-sm text-slate-500">
          {items.length} {items.length === 1 ? 'item' : 'items'}
        </span>

        {/* View Mode Toggle */}
        <div className="ml-4 flex items-center bg-slate-100 rounded-lg p-1">
          <button
            onClick={() => setViewMode('dashboard')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
              viewMode === 'dashboard'
                ? 'bg-white text-indigo-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <LayoutDashboard className="h-4 w-4" />
            Dashboard
          </button>
          <button
            onClick={() => setViewMode('canvas')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
              viewMode === 'canvas'
                ? 'bg-white text-indigo-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Move className="h-4 w-4" />
            Canvas
          </button>
        </div>

        <div className="ml-auto flex gap-2">
          {viewMode === 'canvas' && items.length > 1 && (
            <button
              onClick={handleAutoArrange}
              className="flex items-center gap-2 px-4 py-2 bg-violet-50 text-violet-600 rounded-lg hover:bg-violet-100 transition-colors"
              title="Auto-arrange all items"
            >
              <LayoutGrid className="h-4 w-4" />
              Auto-Arrange
            </button>
          )}
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
          {onLoad && (
            <button
              onClick={onLoad}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              <FolderOpen className="h-4 w-4" />
              Load
            </button>
          )}
          <button
            onClick={handleSaveClick}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Save className="h-4 w-4" />
            Save
          </button>
          <button
            onClick={() => setShowExportDialog(true)}
            disabled={items.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="h-4 w-4" />
            Export
          </button>
          <button
            onClick={() => setShowThemeExtractor(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200"
            title="Extract theme colors from image"
          >
            <Palette className="h-4 w-4" />
            Theme
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      {viewMode === 'dashboard' ? (
        <div ref={exportCanvasRef} data-export-canvas className="flex-1 overflow-hidden">
          <DashboardGridView
            items={items}
            onItemContentChange={handleContentChange}
          />
        </div>
      ) : (
        /* Canvas View */
        <div
          ref={canvasRef}
          className="flex-1 relative overflow-auto"
          style={{
            backgroundImage: `
              linear-gradient(rgba(0, 0, 0, 0.03) 1px, transparent 1px),
              linear-gradient(90deg, rgba(0, 0, 0, 0.03) 1px, transparent 1px)
            `,
            backgroundSize: '20px 20px'
          }}
        >
          {/* Export wrapper - captures this element for export */}
          <div
            ref={exportCanvasRef}
            data-export-canvas
            className="min-h-full"
            style={{ backgroundColor: '#f8fafc' }}
          >
          {items.length === 0 ? (
            <div className="absolute inset-0 flex items-center justify-center text-slate-500">
              <div className="text-center">
                <Plus className="h-12 w-12 mx-auto mb-2 text-slate-400" />
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
      )}
    </div>

    {/* Export Dialog */}
    <ExportDialog
      isOpen={showExportDialog}
      onClose={() => setShowExportDialog(false)}
      canvasElement={exportCanvasRef.current}
      workspaceName={workspaceName || 'dashboard'}
    />

    {/* Theme Extractor */}
    <ThemeExtractor
      isOpen={showThemeExtractor}
      onClose={() => setShowThemeExtractor(false)}
      workspaceId={workspaceId}
    />
    </>
  )
}
