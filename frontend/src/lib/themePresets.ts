/**
 * Theme Presets
 *
 * Pre-built theme personas for dashboards, inspired by thebricks.
 * Each theme defines a complete visual identity.
 */

import { ThemePersona } from '@/types/theme'

export const THEME_PRESETS: ThemePersona[] = [
  // Default - Light, soft colors, indigo/violet accents
  {
    id: 'default',
    name: 'Default',
    background: '#f8fafc',      // slate-50
    cardBackground: '#ffffff',
    cardBorder: '#e2e8f0',      // slate-200
    textPrimary: '#1e293b',     // slate-800
    textSecondary: '#475569',   // slate-600
    textMuted: '#94a3b8',       // slate-400
    primary: '#6366f1',         // indigo-500
    secondary: '#8b5cf6',       // violet-500
    accent: '#10b981',          // emerald-500
    kpiValueColor: '#6366f1',
    insightAccent: '#f59e0b',   // amber-500
    chartColors: ['#6366f1', '#8b5cf6', '#10b981', '#f59e0b', '#ec4899', '#06b6d4'],
    badgeStyle: 'light',
    isDark: false
  },

  // Creative - Purple/lavender background, teal accents
  {
    id: 'creative',
    name: 'Creative',
    background: '#ede9fe',      // violet-100
    cardBackground: '#f5f3ff',  // violet-50
    cardBorder: '#c4b5fd',      // violet-300
    textPrimary: '#4c1d95',     // violet-900
    textSecondary: '#6d28d9',   // violet-700
    textMuted: '#8b5cf6',       // violet-500
    primary: '#14b8a6',         // teal-500
    secondary: '#8b5cf6',       // violet-500
    accent: '#06b6d4',          // cyan-500
    kpiValueColor: '#14b8a6',
    insightAccent: '#8b5cf6',
    chartColors: ['#14b8a6', '#06b6d4', '#8b5cf6', '#a78bfa', '#2dd4bf', '#67e8f9'],
    badgeStyle: 'light',
    isDark: false
  },

  // Professional - Navy cards, blue/gold tones
  {
    id: 'professional',
    name: 'Professional',
    background: '#f1f5f9',      // slate-100
    cardBackground: '#1e3a5f',  // Custom navy
    cardBorder: '#2d4a6f',
    textPrimary: '#ffffff',
    textSecondary: '#cbd5e1',   // slate-300
    textMuted: '#94a3b8',       // slate-400
    primary: '#60a5fa',         // blue-400
    secondary: '#a78bfa',       // violet-400
    accent: '#c9a87c',          // Custom gold/tan
    kpiValueColor: '#60a5fa',
    insightAccent: '#60a5fa',
    chartColors: ['#60a5fa', '#93c5fd', '#c9a87c', '#a78bfa', '#67e8f9', '#fcd34d'],
    badgeStyle: 'dark',
    isDark: true
  },

  // Dark - Very dark background, orange/amber accents
  {
    id: 'dark',
    name: 'Dark',
    background: '#0f172a',      // slate-900
    cardBackground: '#1e293b',  // slate-800
    cardBorder: '#334155',      // slate-700
    textPrimary: '#f8fafc',     // slate-50
    textSecondary: '#cbd5e1',   // slate-300
    textMuted: '#64748b',       // slate-500
    primary: '#f97316',         // orange-500
    secondary: '#60a5fa',       // blue-400
    accent: '#fbbf24',          // amber-400
    kpiValueColor: '#f97316',
    insightAccent: '#f97316',
    chartColors: ['#f97316', '#60a5fa', '#fbbf24', '#a78bfa', '#2dd4bf', '#f472b6'],
    badgeStyle: 'dark',
    isDark: true
  },

  // Corporate - Black cards, light blue charts
  {
    id: 'corporate',
    name: 'Corporate',
    background: '#f8fafc',      // slate-50
    cardBackground: '#18181b',  // zinc-900
    cardBorder: '#27272a',      // zinc-800
    textPrimary: '#ffffff',
    textSecondary: '#a1a1aa',   // zinc-400
    textMuted: '#71717a',       // zinc-500
    primary: '#93c5fd',         // blue-300
    secondary: '#c4b5fd',       // violet-300
    accent: '#fde68a',          // amber-200
    kpiValueColor: '#93c5fd',
    insightAccent: '#93c5fd',
    chartColors: ['#93c5fd', '#bfdbfe', '#c4b5fd', '#a5b4fc', '#99f6e4', '#fde68a'],
    badgeStyle: 'dark',
    isDark: true
  },

  // Minimalist - White, grayscale only
  {
    id: 'minimalist',
    name: 'Minimalist',
    background: '#ffffff',
    cardBackground: '#fafafa',  // neutral-50
    cardBorder: '#e5e5e5',      // neutral-200
    textPrimary: '#171717',     // neutral-900
    textSecondary: '#404040',   // neutral-700
    textMuted: '#737373',       // neutral-500
    primary: '#404040',         // neutral-700
    secondary: '#525252',       // neutral-600
    accent: '#737373',          // neutral-500
    kpiValueColor: '#171717',
    insightAccent: '#a3a3a3',   // neutral-400
    chartColors: ['#171717', '#404040', '#525252', '#737373', '#a3a3a3', '#d4d4d4'],
    badgeStyle: 'muted',
    isDark: false
  },

  // Energetic - Mint/teal background, vibrant greens
  {
    id: 'energetic',
    name: 'Energetic',
    background: '#ccfbf1',      // teal-100
    cardBackground: '#f0fdfa',  // teal-50
    cardBorder: '#5eead4',      // teal-300
    textPrimary: '#134e4a',     // teal-900
    textSecondary: '#115e59',   // teal-800
    textMuted: '#0d9488',       // teal-600
    primary: '#10b981',         // emerald-500
    secondary: '#14b8a6',       // teal-500
    accent: '#22c55e',          // green-500
    kpiValueColor: '#10b981',
    insightAccent: '#14b8a6',
    chartColors: ['#10b981', '#14b8a6', '#22c55e', '#2dd4bf', '#34d399', '#6ee7b7'],
    badgeStyle: 'light',
    isDark: false
  }
]

/**
 * Get a theme by ID
 */
export function getThemeById(id: string): ThemePersona | undefined {
  return THEME_PRESETS.find(theme => theme.id === id)
}

/**
 * Get the default theme
 */
export function getDefaultTheme(): ThemePersona {
  return THEME_PRESETS[0]
}
