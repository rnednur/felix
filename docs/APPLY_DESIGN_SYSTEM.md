# Applying the Design System

## Quick Migration Guide

This guide shows how to update existing components to use the new sophisticated design system.

## Color Migration

### Before → After

```tsx
// OLD: Hardcoded colors
className="bg-white"
className="text-gray-900"
className="border-gray-200"
className="bg-blue-600"

// NEW: Semantic tokens
className="bg-card"
className="text-foreground"
className="border-border"
className="bg-primary"
```

### Common Replacements

| Old (Hardcoded) | New (Semantic) | Usage |
|-----------------|----------------|-------|
| `bg-white` | `bg-card` | Card backgrounds |
| `bg-gray-50` | `bg-background` | Page background |
| `text-gray-900` | `text-foreground` | Primary text |
| `text-gray-600` | `text-slate-600` | Secondary text |
| `text-gray-500` | `text-muted-foreground` | Muted text |
| `border-gray-200` | `border-border` | Default borders |
| `bg-blue-600` | `bg-primary` | Primary buttons |
| `text-blue-600` | `text-primary` | Primary links |
| `bg-red-50` | `bg-destructive/10` | Error backgrounds |

## Typography Migration

### Headings

```tsx
// OLD
<h1 className="text-3xl font-bold text-gray-900">

// NEW
<h1 className="text-3xl font-display font-semibold text-foreground tracking-tight">
```

### Body Text

```tsx
// OLD
<p className="text-gray-600">

// NEW
<p className="text-slate-600 font-medium">
```

### Small Text

```tsx
// OLD
<span className="text-sm text-gray-500">

// NEW
<span className="text-sm text-muted-foreground font-medium">
```

## Component Examples

### Dataset Card (Before)

```tsx
<div className="p-6 bg-white rounded-lg shadow hover:shadow-md transition-shadow">
  <div className="flex items-start justify-between mb-4">
    <h3 className="text-lg font-semibold text-gray-900">
      {dataset.name}
    </h3>
    <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded">
      {dataset.status}
    </span>
  </div>

  <p className="text-sm text-gray-600 mb-4">
    {dataset.description}
  </p>

  <div className="text-sm text-gray-500">
    {dataset.row_count} rows
  </div>

  <button className="mt-4 w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
    Analyze Now
  </button>
</div>
```

### Dataset Card (After)

```tsx
<div className="p-6 bg-card rounded-xl border border-border shadow-md hover:shadow-lg transition-all duration-200">
  <div className="flex items-start justify-between mb-4">
    <h3 className="text-lg font-display font-semibold text-foreground">
      {dataset.name}
    </h3>
    <span className="px-2.5 py-1 text-xs font-semibold bg-emerald-50 text-emerald-700 rounded-md">
      {dataset.status}
    </span>
  </div>

  <p className="text-sm text-slate-600 font-medium mb-4">
    {dataset.description}
  </p>

  <div className="text-sm text-muted-foreground font-medium">
    {dataset.row_count.toLocaleString()} rows
  </div>

  <button className="mt-4 w-full px-4 py-2 bg-primary text-primary-foreground font-medium rounded-lg shadow-sm hover:shadow-md hover:bg-primary/90 transition-all">
    Analyze Now
  </button>
</div>
```

**Changes Made**:
- ✅ `rounded-lg` → `rounded-xl` (larger radius)
- ✅ Added `border border-border` for definition
- ✅ `shadow` → `shadow-md hover:shadow-lg` (premium elevation)
- ✅ `transition-shadow` → `transition-all duration-200` (smooth)
- ✅ `text-gray-900` → `text-foreground` (semantic)
- ✅ `font-semibold` → `font-display font-semibold` (heading font)
- ✅ `text-gray-600` → `text-slate-600 font-medium` (refined)
- ✅ `bg-green-100` → `bg-emerald-50` (brand colors)
- ✅ `bg-blue-600` → `bg-primary` (semantic)
- ✅ Added `font-medium` to button
- ✅ `hover:bg-blue-700` → `hover:bg-primary/90` (consistent)

### Button Variants

#### Primary Button
```tsx
// Before
<button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">

// After
<button className="px-4 py-2 bg-primary text-primary-foreground font-medium rounded-lg shadow-sm hover:shadow-md hover:bg-primary/90 transition-all">
```

#### Secondary Button
```tsx
// Before
<button className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">

// After
<button className="px-4 py-2 bg-secondary text-secondary-foreground font-medium border border-border rounded-lg hover:bg-secondary/80 transition-all">
```

#### Ghost Button
```tsx
// Before
<button className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">

// After
<button className="px-4 py-2 text-foreground/70 font-medium hover:bg-accent hover:text-accent-foreground rounded-lg transition-all">
```

### Input Fields

```tsx
// Before
<input className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" />

// After
<input className="w-full px-4 py-2 bg-background border border-input rounded-lg font-medium focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-shadow" />
```

### Action Bar

```tsx
// Before
<div className="flex items-center justify-between bg-white rounded-lg shadow-sm border border-gray-200 p-4">

// After
<div className="flex items-center justify-between bg-card rounded-xl border border-border shadow-sm hover:shadow-md p-4 transition-shadow">
```

### Page Header

```tsx
// Before
<div>
  <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
    Felix
  </h1>
  <p className="mt-1 text-gray-600">
    Upload your data and start asking questions
  </p>
</div>

// After
<div>
  <h1 className="text-4xl font-display font-bold bg-gradient-to-r from-emerald-600 to-emerald-800 bg-clip-text text-transparent tracking-tight">
    Felix
  </h1>
  <p className="mt-2 text-slate-600 font-medium">
    Upload your data and start asking questions
  </p>
</div>
```

### Icon Button

```tsx
// Before
const variantClasses = {
  default: 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50',
  primary: 'bg-blue-600 text-white hover:bg-blue-700',
}

// After
const variantClasses = {
  default: 'bg-card border border-border text-foreground hover:bg-accent hover:text-accent-foreground shadow-sm',
  primary: 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm hover:shadow-md',
}
```

## Spacing Updates

### Card Spacing

```tsx
// Before
<div className="p-4 space-y-4">

// After
<div className="p-6 space-y-6">  // More generous, premium feel
```

### Grid Gaps

```tsx
// Before
<div className="grid grid-cols-3 gap-4">

// After
<div className="grid grid-cols-3 gap-6">  // Better breathing room
```

## Shadow Updates

```tsx
// Before: Flat cards
<div className="bg-white border">

// After: Elevated cards
<div className="bg-card border border-border shadow-md hover:shadow-lg transition-shadow">
```

## Transition Updates

```tsx
// Before: Basic transitions
className="transition-colors"

// After: Smooth, comprehensive
className="transition-all duration-200"  // 200ms for UI interactions
```

## Quick Search & Replace

Use your IDE to find and replace:

1. Find: `bg-white` → Replace: `bg-card`
2. Find: `text-gray-900` → Replace: `text-foreground`
3. Find: `border-gray-200` → Replace: `border-border`
4. Find: `bg-blue-600` → Replace: `bg-primary`
5. Find: `text-blue-600` → Replace: `text-primary`
6. Find: `rounded-lg` → Replace: `rounded-xl` (for cards)
7. Find: `shadow hover:shadow-md` → Replace: `shadow-md hover:shadow-lg`
8. Find: `font-bold` → Replace: `font-display font-semibold` (for headings)

## Testing Checklist

After applying the design system:

- [ ] All text is readable (check contrast)
- [ ] Buttons have proper hover states
- [ ] Cards have subtle shadows
- [ ] Transitions are smooth (200ms)
- [ ] Typography uses correct fonts
- [ ] Spacing feels premium (generous)
- [ ] Colors are consistent across components
- [ ] Dark mode works (if enabled)
- [ ] Responsive design maintained
- [ ] Keyboard navigation still works

## Component Priority

Update in this order:

1. **High Priority**
   - DatasetHub (main landing)
   - DatasetDetail (main view)
   - Home page header
   - IconButton component

2. **Medium Priority**
   - DatasetGroupManager
   - DatasetUploader
   - Modal components
   - Form inputs

3. **Low Priority**
   - Utility components
   - Internal components
   - Legacy code

## Performance Notes

- CSS variables add ~0ms overhead (compiled at build)
- Semantic tokens make refactoring easier
- Transition duration of 200ms is optimal
- Shadows use GPU acceleration (performant)

## Common Pitfalls

❌ **Don't**: Mix old and new colors
```tsx
<div className="bg-card text-gray-900">  // Inconsistent!
```

✅ **Do**: Use semantic tokens
```tsx
<div className="bg-card text-foreground">  // Consistent!
```

❌ **Don't**: Hardcode specific shades
```tsx
<span className="bg-emerald-500">
```

✅ **Do**: Use semantic colors
```tsx
<span className="bg-primary">
```

❌ **Don't**: Forget font classes
```tsx
<h1 className="text-3xl font-bold">  // Missing font-display!
```

✅ **Do**: Add display font to headings
```tsx
<h1 className="text-3xl font-display font-semibold tracking-tight">
```

## Final Result

After applying the design system, you should have:

- ✨ Sophisticated slate/emerald color palette
- 🎨 Elegant Space Grotesk headings
- 📝 Clean Inter body text
- 🌟 Subtle shadows and depth
- ⚡ Smooth 200ms transitions
- 📐 Consistent 6-8-12-16px border radii
- 🎯 Semantic, maintainable code

Your app will look professional, polished, and premium!
