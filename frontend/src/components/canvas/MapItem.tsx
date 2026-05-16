import { useState } from 'react'
import { MapContent, DisplaySize } from '@/types/canvas'
import { MapView } from '@/components/map/MapView'
import { Edit2, Check, Minimize2, Square, Maximize2, RectangleHorizontal, Trash2 } from 'lucide-react'
import { CardBadge } from '@/components/ui/card-badge'
import { useTheme } from '@/contexts/ThemeContext'

interface MapItemProps {
  content: MapContent
  mapId?: string
  mapIndex?: number
  onTitleChange?: (newTitle: string) => void
  onSizeChange?: (newSize: DisplaySize) => void
  onDelete?: () => void
}

const SIZE_OPTIONS: { size: DisplaySize; icon: typeof Square; label: string; tooltip: string }[] = [
  { size: 'small', icon: Minimize2, label: 'S', tooltip: 'Small (1 column)' },
  { size: 'medium', icon: Square, label: 'M', tooltip: 'Medium (1 column)' },
  { size: 'large', icon: Maximize2, label: 'L', tooltip: 'Large (2 columns)' },
  { size: 'full', icon: RectangleHorizontal, label: 'Full', tooltip: 'Full width' },
]

export function MapItem({ content, mapId, mapIndex, onTitleChange, onSizeChange, onDelete }: MapItemProps) {
  const { title, data, spatialColumns, config, datasetId, displaySize } = content
  const currentSize = displaySize || 'large'
  const { persona } = useTheme()
  const [isEditing, setIsEditing] = useState(false)
  const [editedTitle, setEditedTitle] = useState(title || 'Geographic Distribution')

  // Serialize config for annotation system
  const felixConfig = mapId ? JSON.stringify({
    title: title || 'Geographic Distribution',
    spatialColumns,
    dataCount: data?.length
  }) : undefined

  const handleSaveTitle = () => {
    if (onTitleChange && editedTitle.trim()) {
      onTitleChange(editedTitle.trim())
    }
    setIsEditing(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSaveTitle()
    } else if (e.key === 'Escape') {
      setEditedTitle(title || 'Geographic Distribution')
      setIsEditing(false)
    }
  }

  // Don't render if no data or spatial columns
  if (!data || data.length === 0 || !spatialColumns) {
    return (
      <div
        className="h-full flex flex-col bg-card rounded-xl border border-border/50 overflow-hidden shadow-[0_2px_8px_-2px_rgba(0,0,0,0.05),0_4px_12px_-4px_rgba(0,0,0,0.05)]"
        data-felix-id={mapId}
        data-felix-type="map"
        data-felix-config={felixConfig}
      >
        <div className="px-5 py-4 border-b border-border/30">
          <CardBadge
            variant="map"
            label={mapIndex !== undefined ? `Map ${mapIndex + 1}` : undefined}
          />
        </div>
        <div className="flex-1 flex items-center justify-center text-muted-foreground">
          <p>No spatial data available</p>
        </div>
      </div>
    )
  }

  return (
    <div
      className="h-full flex flex-col bg-card rounded-xl border border-border/50 overflow-hidden shadow-[0_2px_8px_-2px_rgba(0,0,0,0.05),0_4px_12px_-4px_rgba(0,0,0,0.05)]"
      data-map-container={mapId}
      data-felix-id={mapId}
      data-felix-type="map"
      data-felix-config={felixConfig}
    >
      {/* Header */}
      <div className="px-5 py-4 flex items-center justify-between group border-b border-border/30">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <CardBadge
            variant="map"
            label={mapIndex !== undefined ? `Map ${mapIndex + 1}` : undefined}
          />
          {isEditing ? (
            <div className="flex items-center gap-2 flex-1">
              <input
                type="text"
                value={editedTitle}
                onChange={(e) => setEditedTitle(e.target.value)}
                onKeyDown={handleKeyDown}
                onBlur={handleSaveTitle}
                className="flex-1 px-2 py-1 text-sm font-semibold text-foreground border border-teal-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                autoFocus
              />
              <button
                onClick={handleSaveTitle}
                className="p-1.5 text-emerald-600 hover:bg-emerald-50 rounded-lg"
              >
                <Check className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <h3 className="text-base font-semibold text-foreground truncate font-display">
              {editedTitle}
            </h3>
          )}
        </div>
        <div className="flex items-center gap-1.5 ml-2">
          {/* Size controls */}
          {onSizeChange && (
            <div
              className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-all rounded-lg p-0.5"
              style={{
                backgroundColor: persona.isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.03)'
              }}
            >
              {SIZE_OPTIONS.map(({ size, icon: Icon, tooltip }) => (
                <button
                  key={size}
                  onClick={() => onSizeChange(size)}
                  className="p-1 rounded transition-all"
                  style={{
                    color: currentSize === size ? persona.primary : persona.textMuted,
                    backgroundColor: currentSize === size
                      ? (persona.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)')
                      : 'transparent'
                  }}
                  title={tooltip}
                >
                  <Icon className="h-3.5 w-3.5" />
                </button>
              ))}
            </div>
          )}
          {onTitleChange && !isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="p-1.5 text-muted-foreground hover:text-teal-600 hover:bg-teal-50 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
              title="Edit title"
            >
              <Edit2 className="h-3.5 w-3.5" />
            </button>
          )}
          {onDelete && (
            <button
              onClick={onDelete}
              className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-all hover:bg-red-50 dark:hover:bg-red-900/20"
              style={{
                color: persona.textMuted,
              }}
              title="Delete map"
            >
              <Trash2 className="h-3.5 w-3.5 hover:text-red-500" />
            </button>
          )}
        </div>
      </div>

      {/* Map Container */}
      <div className="flex-1 min-h-0 relative">
        <MapView
          datasetId={datasetId || mapId || 'default'}
          data={data}
          spatialColumns={spatialColumns}
          config={config}
        />
      </div>
    </div>
  )
}
