import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react'

/**
 * Theme types
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
  // Current theme
  theme: ThemePalette | null
  setTheme: (palette: ThemePalette | null) => void

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

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemePalette | null>(null)
  const [extractedColors, setExtractedColors] = useState<ExtractedColor[]>([])
  const [isLoading, setIsLoading] = useState(false)

  // Apply CSS variables to document
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
      // Also set some commonly used Tailwind-compatible variables
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
    // This makes the theme immediately visible
    const styleId = 'custom-theme-styles'
    let styleEl = document.getElementById(styleId) as HTMLStyleElement
    if (!styleEl) {
      styleEl = document.createElement('style')
      styleEl.id = styleId
      document.head.appendChild(styleEl)
    }

    const primaryColor = palette.primary || '#3b82f6'
    const secondaryColor = palette.secondary || palette.primary || '#6366f1'
    const accentColor = palette.accent || '#f59e0b'

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
