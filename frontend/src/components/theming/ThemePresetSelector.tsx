/**
 * Theme Preset Selector
 *
 * Dropdown UI for selecting from prebuilt theme presets.
 */

import { useState, useRef, useEffect } from 'react'
import { Palette, Check, ChevronDown } from 'lucide-react'
import { useTheme } from '@/contexts/ThemeContext'
import { ThemePersona } from '@/types/theme'

interface ThemePresetSelectorProps {
  className?: string
}

function ThemePreview({ theme, isSelected }: { theme: ThemePersona; isSelected: boolean }) {
  return (
    <div className="flex items-center gap-3 w-full">
      {/* Color swatches preview */}
      <div
        className="flex-shrink-0 w-10 h-10 rounded-lg overflow-hidden border shadow-sm"
        style={{
          backgroundColor: theme.background,
          borderColor: theme.cardBorder
        }}
      >
        {/* Mini card preview */}
        <div
          className="m-1 rounded"
          style={{
            backgroundColor: theme.cardBackground,
            height: '60%',
            width: '80%'
          }}
        />
        {/* Chart color dots */}
        <div className="flex gap-0.5 px-1">
          {theme.chartColors.slice(0, 4).map((color, i) => (
            <div
              key={i}
              className="w-1.5 h-1.5 rounded-full"
              style={{ backgroundColor: color }}
            />
          ))}
        </div>
      </div>

      {/* Theme name and description */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span
            className="font-medium text-sm truncate"
            style={{ color: isSelected ? theme.primary : undefined }}
          >
            {theme.name}
          </span>
          {theme.isDark && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700 text-slate-300">
              Dark
            </span>
          )}
        </div>
      </div>

      {/* Selected indicator */}
      {isSelected && (
        <Check className="w-4 h-4 text-emerald-500 flex-shrink-0" />
      )}
    </div>
  )
}

export function ThemePresetSelector({ className = '' }: ThemePresetSelectorProps) {
  const { persona, setPersona, personas } = useTheme()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  // Close on escape key
  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen])

  const handleSelectTheme = (themeId: string) => {
    setPersona(themeId)
    setIsOpen(false)
  }

  return (
    <div ref={dropdownRef} className={`relative ${className}`}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors"
        title="Select theme preset"
      >
        <Palette className="h-4 w-4" />
        <span className="hidden sm:inline">{persona.name}</span>
        <ChevronDown className={`h-3 w-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-64 bg-white rounded-xl shadow-xl border border-slate-200 py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
          <div className="px-3 py-2 border-b border-slate-100">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">
              Theme Presets
            </p>
          </div>

          <div className="py-1 max-h-80 overflow-y-auto">
            {personas.map((theme) => (
              <button
                key={theme.id}
                onClick={() => handleSelectTheme(theme.id)}
                className={`w-full px-3 py-2.5 hover:bg-slate-50 transition-colors text-left ${
                  persona.id === theme.id ? 'bg-slate-50' : ''
                }`}
              >
                <ThemePreview
                  theme={theme}
                  isSelected={persona.id === theme.id}
                />
              </button>
            ))}
          </div>

          <div className="px-3 py-2 border-t border-slate-100">
            <p className="text-[11px] text-slate-400">
              Theme applies to dashboard cards and charts
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
