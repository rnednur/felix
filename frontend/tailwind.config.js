/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        slate: {
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
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Space Grotesk', 'Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
      },
      boxShadow: {
        sm: 'var(--shadow-sm)',
        DEFAULT: 'var(--shadow-md)',
        md: 'var(--shadow-md)',
        lg: 'var(--shadow-lg)',
        xl: 'var(--shadow-xl)',
        '2xl': 'var(--shadow-2xl)',
      },
      transitionDuration: {
        fast: 'var(--transition-fast)',
        DEFAULT: 'var(--transition-base)',
        slow: 'var(--transition-slow)',
      },
      spacing: {
        xs: 'var(--spacing-xs)',
        sm: 'var(--spacing-sm)',
        md: 'var(--spacing-md)',
        lg: 'var(--spacing-lg)',
        xl: 'var(--spacing-xl)',
        '2xl': 'var(--spacing-2xl)',
      },
    },
  },
  plugins: [],
}
