import { useState } from 'react'
import { MapContent } from '@/types/canvas'
import { MapView } from '@/components/map/MapView'
import { Edit2, Check } from 'lucide-react'
import { CardBadge } from '@/components/ui/card-badge'

interface MapItemProps {
  content: MapContent
  mapId?: string
  mapIndex?: number
  onTitleChange?: (newTitle: string) => void
}

export function MapItem({ content, mapId, mapIndex, onTitleChange }: MapItemProps) {
  const { title, data, spatialColumns, config, datasetId } = content
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
          {onTitleChange && !isEditing && (
            <button
              onClick={() => setIsEditing(true)}
              className="p-1.5 text-muted-foreground hover:text-teal-600 hover:bg-teal-50 rounded-lg opacity-0 group-hover:opacity-100 transition-all"
              title="Edit title"
            >
              <Edit2 className="h-3.5 w-3.5" />
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
