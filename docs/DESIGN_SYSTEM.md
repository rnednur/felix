# Sophisticated Design System

## Overview
A premium, professional design system with refined slate/emerald palette, elegant typography, and polished components.

## 🎨 Color Palette

### Slate (Base Colors)
```css
--color-slate-50:  248 250 252   /* Lightest background */
--color-slate-100: 241 245 249   /* Cards, secondary backgrounds */
--color-slate-200: 226 232 240   /* Borders, dividers */
--color-slate-300: 203 213 225   /* Disabled states */
--color-slate-400: 148 163 184   /* Placeholders */
--color-slate-500: 100 116 139   /* Muted text */
--color-slate-600: 71 85 105     /* Secondary text */
--color-slate-700: 51 65 85      /* Body text */
--color-slate-800: 30 41 59      /* Headings */
--color-slate-900: 15 23 42      /* Primary text */
--color-slate-950: 2 6 23        /* Maximum contrast */
```

### Emerald (Accent Colors)
```css
--color-emerald-50:  236 253 245  /* Success background */
--color-emerald-100: 209 250 229  /* Light accent */
--color-emerald-500: 16 185 129   /* Primary brand */
--color-emerald-600: 5 150 105    /* Primary hover */
--color-emerald-700: 4 120 87     /* Primary active */
--color-emerald-900: 6 78 59      /* Dark accent text */
```

## ✍️ Typography

### Font Families
- **Display**: Space Grotesk - Headings, hero text
- **Sans**: Inter - Body text, UI elements
- **Mono**: JetBrains Mono - Code blocks

### Type Scale
```tsx
// Headings (font-display)
h1: text-4xl font-semibold tracking-tight    // 36px
h2: text-3xl font-semibold tracking-tight    // 30px
h3: text-2xl font-semibold                   // 24px
h4: text-xl font-medium                      // 20px
h5: text-lg font-medium                      // 18px

// Body (font-sans)
body: text-base font-normal                  // 16px
small: text-sm font-normal                   // 14px
tiny: text-xs font-medium                    // 12px
```

### Font Weights
```css
300: Light (rarely used)
400: Normal/Regular (body text)
500: Medium (UI elements)
600: Semibold (headings)
700: Bold (emphasis)
```

## 🎯 Semantic Colors

```css
--primary: emerald-600        /* Primary actions, links */
--secondary: slate-100        /* Secondary buttons */
--accent: emerald-50          /* Highlighted areas */
--muted: slate-100            /* Muted backgrounds */
--destructive: red-600        /* Delete, errors */
--success: emerald-500        /* Success states */
--warning: amber-500          /* Warnings */
--error: red-600              /* Errors */
--info: blue-600              /* Info messages */
```

## 📐 Spacing Scale

```css
--spacing-xs:  4px    (0.25rem)
--spacing-sm:  8px    (0.5rem)
--spacing-md:  16px   (1rem)
--spacing-lg:  24px   (1.5rem)
--spacing-xl:  32px   (2rem)
--spacing-2xl: 48px   (3rem)
```

### Common Patterns
- **Card padding**: `p-6` (24px)
- **Section gap**: `space-y-6` (24px)
- **Button padding**: `px-4 py-2` (16px/8px)
- **Icon gap**: `gap-2` (8px)
- **Page padding**: `p-8` (32px)

## 🔲 Border Radius

```css
--radius-sm:  6px     /* Small elements */
--radius-md:  8px     /* Buttons, inputs */
--radius-lg:  12px    /* Cards */
--radius-xl:  16px    /* Modals, large cards */
```

### Usage
```tsx
rounded-sm   // 6px - Badges, small buttons
rounded-md   // 8px - Default buttons, inputs
rounded-lg   // 12px - Cards, containers
rounded-xl   // 16px - Large cards, modals
rounded-2xl  // 24px - Feature cards
```

## 🌟 Shadows

```css
--shadow-sm:  Subtle lift (1-2px)
--shadow-md:  Default elevation (4-6px)
--shadow-lg:  Prominent (10-15px)
--shadow-xl:  Floating (20-25px)
--shadow-2xl: Maximum depth (25-50px)
```

### When to Use
- **sm**: Buttons, inputs at rest
- **md**: Cards, dropdowns
- **lg**: Modals, popovers
- **xl**: Floating action buttons
- **2xl**: Hero elements

## ⚡ Transitions

```css
--transition-fast: 150ms   /* Hover, focus */
--transition-base: 200ms   /* Default */
--transition-slow: 300ms   /* Complex animations */
```

### Easing
```css
cubic-bezier(0.4, 0, 0.2, 1)  /* Smooth, natural */
```

## 🎨 Component Patterns

### Card
```tsx
<div className="bg-card rounded-xl border border-border shadow-md hover:shadow-lg transition-shadow p-6">
  {/* Content */}
</div>
```

### Button (Primary)
```tsx
<button className="px-4 py-2 bg-emerald-600 text-white font-medium rounded-lg shadow-sm hover:bg-emerald-700 hover:shadow-md transition-all">
  Click Me
</button>
```

### Button (Secondary)
```tsx
<button className="px-4 py-2 bg-slate-100 text-slate-900 font-medium rounded-lg hover:bg-slate-200 transition-colors">
  Cancel
</button>
```

### Input
```tsx
<input className="px-4 py-2 bg-background border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-shadow" />
```

### Badge
```tsx
<span className="px-2.5 py-1 text-xs font-semibold bg-emerald-50 text-emerald-700 rounded-md">
  Active
</span>
```

## 🎭 States & Variants

### Hover States
```css
hover:bg-slate-50          /* Subtle background change */
hover:shadow-lg            /* Elevation increase */
hover:scale-[1.02]         /* Subtle zoom */
hover:border-emerald-500   /* Accent border */
```

### Focus States
```css
focus:outline-none
focus:ring-2
focus:ring-emerald-500
focus:ring-offset-2
```

### Active States
```css
active:scale-95            /* Press effect */
active:shadow-sm           /* Reduce shadow */
```

### Disabled States
```css
disabled:opacity-50
disabled:pointer-events-none
disabled:cursor-not-allowed
```

## 📱 Responsive Design

### Breakpoints
```css
sm:  640px   /* Mobile landscape */
md:  768px   /* Tablet */
lg:  1024px  /* Desktop */
xl:  1280px  /* Large desktop */
2xl: 1536px  /* Extra large */
```

### Mobile-First Approach
```tsx
// Stack on mobile, grid on desktop
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
```

## 🎨 Color Usage Guide

### Text Hierarchy
```tsx
Primary text:   text-slate-900
Secondary text: text-slate-600
Muted text:     text-slate-500
Disabled text:  text-slate-400
```

### Backgrounds
```tsx
Page background:   bg-slate-50
Card background:   bg-card (white)
Muted background:  bg-slate-100
Active background: bg-emerald-50
```

### Borders
```tsx
Default border: border-slate-200
Active border:  border-emerald-500
Error border:   border-red-500
```

## ✨ Premium Details

### Subtle Gradients
```tsx
className="bg-gradient-to-br from-emerald-500 to-emerald-700"
className="bg-gradient-to-r from-slate-900 to-slate-700"
```

### Glass Morphism
```tsx
className="bg-white/80 backdrop-blur-sm border border-slate-200"
```

### Smooth Scrollbar
```css
::-webkit-scrollbar {
  width: 8px;
  background: hsl(var(--muted));
}

::-webkit-scrollbar-thumb {
  background: hsl(var(--muted-foreground) / 0.3);
  border-radius: 4px;
}
```

## 🎯 Design Principles

1. **Clarity** - Clear visual hierarchy
2. **Consistency** - Use design tokens consistently
3. **Elegance** - Subtle, refined touches
4. **Performance** - Optimize for 60fps
5. **Accessibility** - WCAG 2.1 AA compliance

## 📋 Checklist for New Components

- [ ] Use semantic color tokens (not hardcoded values)
- [ ] Apply appropriate shadow for elevation
- [ ] Add smooth transitions (150-300ms)
- [ ] Use Space Grotesk for headings
- [ ] Use Inter for body text
- [ ] Test hover/focus/active states
- [ ] Ensure responsive behavior
- [ ] Add proper spacing (use scale)
- [ ] Check contrast ratios (4.5:1 min)
- [ ] Test with keyboard navigation

## 🎨 Quick Reference

### Common Combinations

**Primary Button**
```
bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm hover:shadow-md
```

**Card**
```
bg-card border border-border rounded-xl shadow-md hover:shadow-lg
```

**Input**
```
bg-background border border-input rounded-lg focus:ring-2 focus:ring-emerald-500
```

**Badge**
```
bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-md text-xs font-semibold
```

## 🚀 Implementation Status

- [x] Design tokens defined (CSS variables)
- [x] Tailwind config updated
- [x] Typography system ready
- [x] Color palette implemented
- [ ] Update all components (in progress)
- [ ] Dark mode ready (tokens defined)
- [ ] Component library documentation

## 📚 Resources

- **Fonts**: Google Fonts (Inter, Space Grotesk)
- **Icons**: Lucide React
- **Framework**: Tailwind CSS 3.x
- **Inspiration**: Vercel, Linear, Stripe design systems
