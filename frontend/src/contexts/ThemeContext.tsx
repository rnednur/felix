import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react'
import { ThemePersona } from '@/types/theme'
import { THEME_PRESETS, getThemeById, getDefaultTheme } from '@/lib/themePresets'

/**
 * Theme types (legacy - for image extraction)
 */
export interface ExtractedColor {
  rgb: [number, number, number]
  hex: string
  hsl: [number, number, number]
  hsl_css: string
  frequency: number
}

export interface ThemePalette {
  primary: string
  secondary?: string
  accent?: string
  background?: string
  text?: string
  colors: ExtractedColor[]
  css_variables: { [key: string]: string }
}

export interface ThemeContextType {
  // Current theme (legacy)
  theme: ThemePalette | null
  setTheme: (palette: ThemePalette | null) => void

  // Theme Persona (new)
  persona: ThemePersona
  setPersona: (id: string) => void
  personas: ThemePersona[]

  // Apply theme to document
  applyTheme: (palette: ThemePalette) => void
  clearTheme: () => void

  // Loading state
  isLoading: boolean
  setIsLoading: (loading: boolean) => void

  // Extracted colors (before applying)
  extractedColors: ExtractedColor[]
  setExtractedColors: (colors: ExtractedColor[]) => void
}

const PERSONA_STORAGE_KEY = 'dashboard-theme-persona'

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemePalette | null>(null)
  const [persona, setPersonaState] = useState<ThemePersona>(getDefaultTheme())
  const [extractedColors, setExtractedColors] = useState<ExtractedColor[]>([])
  const [isLoading, setIsLoading] = useState(false)

  // Apply persona CSS variables to document
  const applyPersona = useCallback((p: ThemePersona) => {
    const root = document.documentElement

    // Set CSS variables for persona
    root.style.setProperty('--theme-bg', p.background)
    root.style.setProperty('--theme-card-bg', p.cardBackground)
    root.style.setProperty('--theme-card-border', p.cardBorder)
    root.style.setProperty('--theme-text-primary', p.textPrimary)
    root.style.setProperty('--theme-text-secondary', p.textSecondary)
    root.style.setProperty('--theme-text-muted', p.textMuted)
    root.style.setProperty('--theme-primary', p.primary)
    root.style.setProperty('--theme-secondary', p.secondary)
    root.style.setProperty('--theme-accent', p.accent)
    root.style.setProperty('--theme-kpi-value', p.kpiValueColor)
    root.style.setProperty('--theme-insight-accent', p.insightAccent)
    root.style.setProperty('--theme-is-dark', p.isDark ? '1' : '0')
    root.style.setProperty('--theme-badge-style', p.badgeStyle)

    // Set chart colors as a CSS variable (comma-separated for easy parsing)
    root.style.setProperty('--theme-chart-colors', p.chartColors.join(','))

    // Set data attribute for CSS selectors
    root.setAttribute('data-theme-persona', p.id)
    root.setAttribute('data-theme-dark', p.isDark ? 'true' : 'false')

    setPersonaState(p)

    // Persist to localStorage
    localStorage.setItem(PERSONA_STORAGE_KEY, p.id)
  }, [])

  // Set persona by ID
  const setPersona = useCallback((id: string) => {
    const newPersona = getThemeById(id)
    if (newPersona) {
      applyPersona(newPersona)
    }
  }, [applyPersona])

  // Load persona from localStorage on mount
  useEffect(() => {
    const savedPersonaId = localStorage.getItem(PERSONA_STORAGE_KEY)
    if (savedPersonaId) {
      const savedPersona = getThemeById(savedPersonaId)
      if (savedPersona) {
        applyPersona(savedPersona)
        return
      }
    }
    // Apply default theme on first load
    applyPersona(getDefaultTheme())
  }, [applyPersona])

  // Apply legacy CSS variables to document (for image-extracted themes)
  const applyTheme = useCallback((palette: ThemePalette) => {
    const root = document.documentElement

    // Apply CSS variables
    if (palette.css_variables) {
      Object.entries(palette.css_variables).forEach(([key, value]) => {
        root.style.setProperty(key, value)
      })
    }

    // Apply direct color values
    if (palette.primary) {
      root.style.setProperty('--theme-primary', palette.primary)
      root.style.setProperty('--primary', palette.primary)
    }
    if (palette.secondary) {
      root.style.setProperty('--theme-secondary', palette.secondary)
    }
    if (palette.accent) {
      root.style.setProperty('--theme-accent', palette.accent)
    }
    if (palette.background) {
      root.style.setProperty('--theme-background', palette.background)
    }
    if (palette.text) {
      root.style.setProperty('--theme-text', palette.text)
    }

    // Add a data attribute to indicate theme is active
    root.setAttribute('data-theme', 'custom')

    // Apply visible theme styles directly to key elements
    const styleId = 'custom-theme-styles'
    let styleEl = document.getElementById(styleId) as HTMLStyleElement
    if (!styleEl) {
      styleEl = document.createElement('style')
      styleEl.id = styleId
      document.head.appendChild(styleEl)
    }

    const primaryColor = palette.primary || '#3b82f6'
    const secondaryColor = palette.secondary || palette.primary || '#6366f1'

    styleEl.textContent = `
      /* Applied theme colors */
      [data-theme="custom"] .bg-blue-600,
      [data-theme="custom"] .bg-primary {
        background-color: ${primaryColor} !important;
      }
      [data-theme="custom"] .text-blue-600,
      [data-theme="custom"] .text-primary {
        color: ${primaryColor} !important;
      }
      [data-theme="custom"] .border-blue-600,
      [data-theme="custom"] .border-primary {
        border-color: ${primaryColor} !important;
      }
      [data-theme="custom"] .hover\\:bg-blue-700:hover {
        background-color: ${primaryColor} !important;
        filter: brightness(0.9);
      }
      [data-theme="custom"] .bg-purple-100 {
        background-color: ${secondaryColor}20 !important;
      }
      [data-theme="custom"] .text-purple-700 {
        color: ${secondaryColor} !important;
      }
      [data-theme="custom"] .bg-purple-600 {
        background-color: ${secondaryColor} !important;
      }
      /* KPI cards accent */
      [data-theme="custom"] .from-blue-500 {
        --tw-gradient-from: ${primaryColor} !important;
      }
      [data-theme="custom"] .to-blue-600 {
        --tw-gradient-to: ${primaryColor} !important;
      }
      /* Chart header accents */
      [data-theme="custom"] .bg-gradient-to-r.from-blue-50 {
        background: linear-gradient(to right, ${primaryColor}10, white) !important;
      }
    `

    setThemeState(palette)
  }, [])

  // Clear custom theme
  const clearTheme = useCallback(() => {
    const root = document.documentElement

    // Remove custom CSS variables
    const customProps = [
      '--theme-primary',
      '--theme-secondary',
      '--theme-accent',
      '--theme-background',
      '--theme-text',
      '--theme-primary-hsl',
      '--theme-secondary-hsl',
      '--theme-accent-hsl',
      '--primary'
    ]

    customProps.forEach(prop => {
      root.style.removeProperty(prop)
    })

    // Remove custom style element
    const styleEl = document.getElementById('custom-theme-styles')
    if (styleEl) {
      styleEl.remove()
    }

    root.removeAttribute('data-theme')
    setThemeState(null)
    setExtractedColors([])
  }, [])

  const setTheme = useCallback((palette: ThemePalette | null) => {
    if (palette) {
      applyTheme(palette)
    } else {
      clearTheme()
    }
  }, [applyTheme, clearTheme])

  return (
    <ThemeContext.Provider value={{
      theme,
      setTheme,
      persona,
      setPersona,
      personas: THEME_PRESETS,
      applyTheme,
      clearTheme,
      isLoading,
      setIsLoading,
      extractedColors,
      setExtractedColors
    }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
