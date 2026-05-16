/**
 * Theme Persona System
 *
 * Defines complete visual personas for dashboards - not just chart colors,
 * but card backgrounds, text colors, badge styles, and overall mood.
 */

export interface ThemePersona {
  id: string
  name: string

  // Surface colors
  background: string        // Main dashboard background
  cardBackground: string    // Card/container background
  cardBorder: string        // Card border color

  // Text colors
  textPrimary: string       // Headings, titles
  textSecondary: string     // Body text, descriptions
  textMuted: string         // Subtle text

  // Accent colors
  primary: string           // Primary accent (buttons, highlights)
  secondary: string         // Secondary accent
  accent: string            // Tertiary accent

  // Component-specific
  kpiValueColor: string     // KPI value text
  insightAccent: string     // Insight card accent

  // Chart palette
  chartColors: string[]     // 6-8 colors for charts

  // Badge style for dark/light backgrounds
  badgeStyle: 'light' | 'dark' | 'muted'

  // Mode indicator
  isDark: boolean
}

export type ThemePersonaId =
  | 'default'
  | 'creative'
  | 'professional'
  | 'dark'
  | 'corporate'
  | 'minimalist'
  | 'energetic'
