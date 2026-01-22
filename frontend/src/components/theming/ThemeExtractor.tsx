import { useState, useRef } from 'react'
import { useMutation } from '@tanstack/react-query'
import { X, Upload, Palette, Check, Loader2, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useTheme, ExtractedColor, ThemePalette } from '@/contexts/ThemeContext'
import axios from '@/services/api'

interface ThemeExtractorProps {
  isOpen: boolean
  onClose: () => void
  workspaceId?: string
  onThemeApplied?: () => void
}

export function ThemeExtractor({
  isOpen,
  onClose,
  workspaceId,
  onThemeApplied
}: ThemeExtractorProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [previewImage, setPreviewImage] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string>('')

  const {
    extractedColors,
    setExtractedColors,
    applyTheme,
    clearTheme,
    theme,
    isLoading,
    setIsLoading
  } = useTheme()

  // Extract colors mutation
  const extractMutation = useMutation({
    mutationFn: async (imageData: string) => {
      const response = await axios.post('/theming/extract-colors', {
        image_data: imageData,
        num_colors: 5
      })
      return response.data
    },
    onSuccess: (data) => {
      setExtractedColors(data.colors)
    },
    onError: (error) => {
      console.error('Color extraction failed:', error)
    }
  })

  // Save theme to workspace mutation (optional - theme works locally even if save fails)
  const [themeSaved, setThemeSaved] = useState(false)
  const saveThemeMutation = useMutation({
    mutationFn: async (palette: ThemePalette) => {
      if (!workspaceId) return null
      const response = await axios.post(`/theming/workspaces/${workspaceId}/theme`, palette)
      return response.data
    },
    onSuccess: () => {
      setThemeSaved(true)
      onThemeApplied?.()
    },
    onError: (error: any) => {
      // Theme is still applied locally, just not saved to workspace
      // This is expected when not on a workspace page (e.g., dataset detail)
      if (error?.response?.status === 404) {
        console.log('Theme applied locally (not saved - not on workspace page)')
      } else {
        console.warn('Failed to save theme to workspace:', error)
      }
    }
  })

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file')
      return
    }

    setFileName(file.name)

    // Read file as base64
    const reader = new FileReader()
    reader.onload = async (e) => {
      const imageData = e.target?.result as string
      setPreviewImage(imageData)
      extractMutation.mutate(imageData)
    }
    reader.readAsDataURL(file)
  }

  const handleApplyTheme = () => {
    if (extractedColors.length === 0) return

    // Build palette from extracted colors
    const sortedByFrequency = [...extractedColors].sort((a, b) => b.frequency - a.frequency)
    const sortedByLightness = [...extractedColors].sort((a, b) => a.hsl[2] - b.hsl[2])

    const palette: ThemePalette = {
      primary: sortedByFrequency[0]?.hex || '#3b82f6',
      secondary: sortedByFrequency[1]?.hex,
      accent: extractedColors.reduce((max, c) => c.hsl[1] > max.hsl[1] ? c : max, extractedColors[0])?.hex,
      background: `hsl(${sortedByLightness[sortedByLightness.length - 1]?.hsl[0] || 0}, 10%, 97%)`,
      text: `hsl(${sortedByLightness[0]?.hsl[0] || 0}, 10%, 15%)`,
      colors: extractedColors,
      css_variables: {
        '--theme-primary': sortedByFrequency[0]?.hex || '#3b82f6',
        '--theme-secondary': sortedByFrequency[1]?.hex || '#6366f1',
        '--theme-accent': extractedColors.reduce((max, c) => c.hsl[1] > max.hsl[1] ? c : max, extractedColors[0])?.hex || '#f59e0b'
      }
    }

    applyTheme(palette)

    // Save to workspace if valid workspace ID provided (not 'temp' or dataset ID)
    // Theme saving only works on the WorkspaceDetail page where we have a real workspace ID
    if (workspaceId && workspaceId !== 'temp' && workspaceId.length > 10) {
      saveThemeMutation.mutate(palette)
    }
  }

  const handleClearTheme = () => {
    clearTheme()
    setPreviewImage(null)
    setFileName('')
    setThemeSaved(false)
  }

  const handleClose = () => {
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-card rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden border border-border">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Palette className="h-5 w-5 text-primary" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">
                Theme Extractor
              </h2>
              <p className="text-sm text-muted-foreground">
                Extract colors from your logo or brand image
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-5 space-y-5">
          {/* Upload Area */}
          <div
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
              previewImage
                ? 'border-primary bg-primary/5'
                : 'border-gray-300 hover:border-primary hover:bg-gray-50'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="hidden"
            />

            {previewImage ? (
              <div className="space-y-3">
                <img
                  src={previewImage}
                  alt="Preview"
                  className="max-h-32 mx-auto rounded-lg object-contain"
                />
                <p className="text-sm text-muted-foreground">{fileName}</p>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setPreviewImage(null)
                    setFileName('')
                    setExtractedColors([])
                  }}
                  className="text-xs text-red-600 hover:text-red-700"
                >
                  Remove image
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <Upload className="h-10 w-10 mx-auto text-gray-400" />
                <p className="text-sm font-medium text-gray-700">
                  Click to upload an image
                </p>
                <p className="text-xs text-gray-500">
                  PNG, JPG, GIF up to 10MB
                </p>
              </div>
            )}
          </div>

          {/* Extracted Colors */}
          {extractMutation.isPending && (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="h-6 w-6 text-primary animate-spin" />
              <span className="ml-2 text-sm text-muted-foreground">
                Extracting colors...
              </span>
            </div>
          )}

          {extractedColors.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-foreground">
                Extracted Colors
              </h4>
              <div className="flex items-center gap-2 flex-wrap">
                {extractedColors.map((color, idx) => (
                  <div
                    key={idx}
                    className="flex flex-col items-center gap-1"
                  >
                    <div
                      className="w-12 h-12 rounded-lg shadow-sm border border-gray-200"
                      style={{ backgroundColor: color.hex }}
                      title={`${color.hex} (${Math.round(color.frequency * 100)}%)`}
                    />
                    <span className="text-xs text-muted-foreground font-mono">
                      {color.hex}
                    </span>
                  </div>
                ))}
              </div>

              {/* Color roles */}
              <div className="bg-muted/50 rounded-lg p-3 text-xs space-y-1">
                <div className="flex items-center gap-2">
                  <div
                    className="w-4 h-4 rounded"
                    style={{ backgroundColor: extractedColors[0]?.hex }}
                  />
                  <span className="text-muted-foreground">Primary color</span>
                </div>
                {extractedColors[1] && (
                  <div className="flex items-center gap-2">
                    <div
                      className="w-4 h-4 rounded"
                      style={{ backgroundColor: extractedColors[1]?.hex }}
                    />
                    <span className="text-muted-foreground">Secondary color</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Current Theme Indicator */}
          {theme && (
            <div className="flex items-center justify-between bg-green-50 border border-green-200 rounded-lg p-3">
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <Check className="h-4 w-4 text-green-600" />
                  <span className="text-sm text-green-700">Theme applied</span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {themeSaved ? 'Saved to workspace' : 'Applied to this session'}
                </span>
              </div>
              <button
                onClick={handleClearTheme}
                className="text-xs text-red-600 hover:text-red-700"
              >
                Reset to default
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-border bg-muted/30">
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            onClick={handleApplyTheme}
            disabled={extractedColors.length === 0 || extractMutation.isPending}
          >
            <Palette className="h-4 w-4 mr-2" />
            Apply Theme
          </Button>
        </div>
      </div>
    </div>
  )
}
