/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      /* ============================================
         COLORS
         ============================================ */
      colors: {
        // Semantic colors (primary use)
        border: 'hsl(var(--border))',
        'border-muted': 'hsl(var(--border-muted))',
        'border-strong': 'hsl(var(--border-strong))',
        input: 'hsl(var(--input))',
        'input-focus': 'hsl(var(--input-focus))',
        ring: 'hsl(var(--ring))',
        'ring-offset': 'hsl(var(--ring-offset))',

        // Backgrounds
        background: 'hsl(var(--background))',
        'background-subtle': 'hsl(var(--background-subtle))',
        'background-muted': 'hsl(var(--background-muted))',
        foreground: 'hsl(var(--foreground))',
        'foreground-muted': 'hsl(var(--foreground-muted))',

        // Primary
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          hover: 'hsl(var(--primary-hover))',
          active: 'hsl(var(--primary-active))',
          foreground: 'hsl(var(--primary-foreground))',
          muted: 'hsl(var(--primary-muted))',
        },

        // Secondary
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          hover: 'hsl(var(--secondary-hover))',
          active: 'hsl(var(--secondary-active))',
          foreground: 'hsl(var(--secondary-foreground))',
        },

        // Muted
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },

        // Accent
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          hover: 'hsl(var(--accent-hover))',
          foreground: 'hsl(var(--accent-foreground))',
        },

        // Card
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
          hover: 'hsl(var(--card-hover))',
        },

        // Popover
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },

        // Semantic states
        success: {
          DEFAULT: 'hsl(var(--success))',
          hover: 'hsl(var(--success-hover))',
          muted: 'hsl(var(--success-muted))',
          foreground: 'hsl(var(--success-foreground))',
        },
        warning: {
          DEFAULT: 'hsl(var(--warning))',
          hover: 'hsl(var(--warning-hover))',
          muted: 'hsl(var(--warning-muted))',
          foreground: 'hsl(var(--warning-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          hover: 'hsl(var(--destructive-hover))',
          muted: 'hsl(var(--destructive-muted))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        info: {
          DEFAULT: 'hsl(var(--info))',
          hover: 'hsl(var(--info-hover))',
          muted: 'hsl(var(--info-muted))',
          foreground: 'hsl(var(--info-foreground))',
        },

        // Raw color palette (for exceptions)
        slate: {
          25: 'hsl(var(--color-slate-25))',
          50: 'hsl(var(--color-slate-50))',
          100: 'hsl(var(--color-slate-100))',
          200: 'hsl(var(--color-slate-200))',
          300: 'hsl(var(--color-slate-300))',
          400: 'hsl(var(--color-slate-400))',
          500: 'hsl(var(--color-slate-500))',
          600: 'hsl(var(--color-slate-600))',
          700: 'hsl(var(--color-slate-700))',
          800: 'hsl(var(--color-slate-800))',
          900: 'hsl(var(--color-slate-900))',
          950: 'hsl(var(--color-slate-950))',
        },
        indigo: {
          50: 'hsl(var(--color-indigo-50))',
          100: 'hsl(var(--color-indigo-100))',
          200: 'hsl(var(--color-indigo-200))',
          300: 'hsl(var(--color-indigo-300))',
          400: 'hsl(var(--color-indigo-400))',
          500: 'hsl(var(--color-indigo-500))',
          600: 'hsl(var(--color-indigo-600))',
          700: 'hsl(var(--color-indigo-700))',
          800: 'hsl(var(--color-indigo-800))',
          900: 'hsl(var(--color-indigo-900))',
          950: 'hsl(var(--color-indigo-950))',
        },
        emerald: {
          50: 'hsl(var(--color-emerald-50))',
          100: 'hsl(var(--color-emerald-100))',
          200: 'hsl(var(--color-emerald-200))',
          300: 'hsl(var(--color-emerald-300))',
          400: 'hsl(var(--color-emerald-400))',
          500: 'hsl(var(--color-emerald-500))',
          600: 'hsl(var(--color-emerald-600))',
          700: 'hsl(var(--color-emerald-700))',
          800: 'hsl(var(--color-emerald-800))',
          900: 'hsl(var(--color-emerald-900))',
          950: 'hsl(var(--color-emerald-950))',
        },
        amber: {
          50: 'hsl(var(--color-amber-50))',
          100: 'hsl(var(--color-amber-100))',
          200: 'hsl(var(--color-amber-200))',
          300: 'hsl(var(--color-amber-300))',
          400: 'hsl(var(--color-amber-400))',
          500: 'hsl(var(--color-amber-500))',
          600: 'hsl(var(--color-amber-600))',
          700: 'hsl(var(--color-amber-700))',
          800: 'hsl(var(--color-amber-800))',
          900: 'hsl(var(--color-amber-900))',
          950: 'hsl(var(--color-amber-950))',
        },
        rose: {
          50: 'hsl(var(--color-rose-50))',
          100: 'hsl(var(--color-rose-100))',
          200: 'hsl(var(--color-rose-200))',
          300: 'hsl(var(--color-rose-300))',
          400: 'hsl(var(--color-rose-400))',
          500: 'hsl(var(--color-rose-500))',
          600: 'hsl(var(--color-rose-600))',
          700: 'hsl(var(--color-rose-700))',
          800: 'hsl(var(--color-rose-800))',
          900: 'hsl(var(--color-rose-900))',
          950: 'hsl(var(--color-rose-950))',
        },
        violet: {
          50: 'hsl(var(--color-violet-50))',
          100: 'hsl(var(--color-violet-100))',
          200: 'hsl(var(--color-violet-200))',
          300: 'hsl(var(--color-violet-300))',
          400: 'hsl(var(--color-violet-400))',
          500: 'hsl(var(--color-violet-500))',
          600: 'hsl(var(--color-violet-600))',
          700: 'hsl(var(--color-violet-700))',
          800: 'hsl(var(--color-violet-800))',
          900: 'hsl(var(--color-violet-900))',
          950: 'hsl(var(--color-violet-950))',
        },
      },

      /* ============================================
         TYPOGRAPHY
         ============================================ */
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        display: ['Space Grotesk', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'SF Mono', 'monospace'],
      },

      fontSize: {
        'xs': ['var(--text-xs)', { lineHeight: 'var(--leading-normal)' }],
        'sm': ['var(--text-sm)', { lineHeight: 'var(--leading-normal)' }],
        'base': ['var(--text-base)', { lineHeight: 'var(--leading-normal)' }],
        'lg': ['var(--text-lg)', { lineHeight: 'var(--leading-relaxed)' }],
        'xl': ['var(--text-xl)', { lineHeight: 'var(--leading-relaxed)' }],
        '2xl': ['var(--text-2xl)', { lineHeight: 'var(--leading-tight)' }],
        '3xl': ['var(--text-3xl)', { lineHeight: 'var(--leading-tight)' }],
        '4xl': ['var(--text-4xl)', { lineHeight: 'var(--leading-none)' }],
        '5xl': ['var(--text-5xl)', { lineHeight: 'var(--leading-none)' }],
        '6xl': ['var(--text-6xl)', { lineHeight: 'var(--leading-none)' }],
      },

      letterSpacing: {
        tighter: 'var(--tracking-tighter)',
        tight: 'var(--tracking-tight)',
        normal: 'var(--tracking-normal)',
        wide: 'var(--tracking-wide)',
        wider: 'var(--tracking-wider)',
        widest: 'var(--tracking-widest)',
      },

      lineHeight: {
        none: 'var(--leading-none)',
        tight: 'var(--leading-tight)',
        snug: 'var(--leading-snug)',
        normal: 'var(--leading-normal)',
        relaxed: 'var(--leading-relaxed)',
        loose: 'var(--leading-loose)',
      },

      /* ============================================
         SPACING
         ============================================ */
      spacing: {
        'px': 'var(--spacing-px)',
        '0.5': 'var(--spacing-0-5)',
        '1': 'var(--spacing-1)',
        '1.5': 'var(--spacing-1-5)',
        '2': 'var(--spacing-2)',
        '2.5': 'var(--spacing-2-5)',
        '3': 'var(--spacing-3)',
        '3.5': 'var(--spacing-3-5)',
        '4': 'var(--spacing-4)',
        '5': 'var(--spacing-5)',
        '6': 'var(--spacing-6)',
        '7': 'var(--spacing-7)',
        '8': 'var(--spacing-8)',
        '9': 'var(--spacing-9)',
        '10': 'var(--spacing-10)',
        '12': 'var(--spacing-12)',
        '14': 'var(--spacing-14)',
        '16': 'var(--spacing-16)',
        '20': 'var(--spacing-20)',
        '24': 'var(--spacing-24)',
      },

      /* ============================================
         BORDER RADIUS
         ============================================ */
      borderRadius: {
        'none': 'var(--radius-none)',
        'sm': 'var(--radius-sm)',
        DEFAULT: 'var(--radius-md)',
        'md': 'var(--radius-md)',
        'lg': 'var(--radius-lg)',
        'xl': 'var(--radius-xl)',
        '2xl': 'var(--radius-2xl)',
        'full': 'var(--radius-full)',
      },

      /* ============================================
         SHADOWS & ELEVATION
         ============================================ */
      boxShadow: {
        'none': 'none',
        'xs': 'var(--shadow-xs)',
        'sm': 'var(--shadow-sm)',
        DEFAULT: 'var(--shadow-md)',
        'md': 'var(--shadow-md)',
        'lg': 'var(--shadow-lg)',
        'xl': 'var(--shadow-xl)',
        '2xl': 'var(--shadow-2xl)',
        // Elevation levels
        'elevation-1': 'var(--elevation-1)',
        'elevation-2': 'var(--elevation-2)',
        'elevation-3': 'var(--elevation-3)',
        'elevation-4': 'var(--elevation-4)',
        // Glows
        'glow-primary': 'var(--glow-primary)',
        'glow-success': 'var(--glow-success)',
        'glow-warning': 'var(--glow-warning)',
        'glow-error': 'var(--glow-error)',
      },

      /* ============================================
         TRANSITIONS
         ============================================ */
      transitionDuration: {
        '75': 'var(--duration-75)',
        '100': 'var(--duration-100)',
        '150': 'var(--duration-150)',
        '200': 'var(--duration-200)',
        '300': 'var(--duration-300)',
        '500': 'var(--duration-500)',
        '700': 'var(--duration-700)',
        '1000': 'var(--duration-1000)',
      },

      transitionTimingFunction: {
        'linear': 'var(--ease-linear)',
        'in': 'var(--ease-in)',
        'out': 'var(--ease-out)',
        'in-out': 'var(--ease-in-out)',
        'out-expo': 'var(--ease-out-expo)',
        'out-back': 'var(--ease-out-back)',
        'spring': 'var(--ease-spring)',
      },

      /* ============================================
         Z-INDEX
         ============================================ */
      zIndex: {
        'base': 'var(--z-base)',
        'dropdown': 'var(--z-dropdown)',
        'sticky': 'var(--z-sticky)',
        'fixed': 'var(--z-fixed)',
        'modal-backdrop': 'var(--z-modal-backdrop)',
        'modal': 'var(--z-modal)',
        'popover': 'var(--z-popover)',
        'tooltip': 'var(--z-tooltip)',
        'toast': 'var(--z-toast)',
      },

      /* ============================================
         BACKGROUNDS (Gradients)
         ============================================ */
      backgroundImage: {
        'gradient-primary': 'var(--gradient-primary)',
        'gradient-primary-subtle': 'var(--gradient-primary-subtle)',
        'gradient-success': 'var(--gradient-success)',
        'gradient-surface': 'var(--gradient-surface)',
        'gradient-shimmer': 'var(--gradient-shimmer)',
      },

      /* ============================================
         ANIMATIONS
         ============================================ */
      animation: {
        'fade-in': 'fade-in var(--duration-300) var(--ease-out-expo)',
        'slide-in-right': 'slide-in-right var(--duration-300) var(--ease-out-expo)',
        'slide-in-up': 'slide-in-up var(--duration-300) var(--ease-out-expo)',
        'scale-in': 'scale-in var(--duration-200) var(--ease-out-back)',
        'pulse-subtle': 'pulse-subtle 2s var(--ease-in-out) infinite',
        'skeleton-shimmer': 'skeleton-shimmer 1.5s ease-in-out infinite',
      },

      keyframes: {
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in-right': {
          from: { opacity: '0', transform: 'translateX(16px)' },
          to: { opacity: '1', transform: 'translateX(0)' },
        },
        'slide-in-up': {
          from: { opacity: '0', transform: 'translateY(16px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'scale-in': {
          from: { opacity: '0', transform: 'scale(0.95)' },
          to: { opacity: '1', transform: 'scale(1)' },
        },
        'pulse-subtle': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        'skeleton-shimmer': {
          '0%': { backgroundPosition: '200% 0' },
          '100%': { backgroundPosition: '-200% 0' },
        },
      },
    },
  },
  plugins: [],
}
