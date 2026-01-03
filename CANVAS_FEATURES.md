# 🎨 Canvas Features Guide

## Editable Titles ✏️

All canvas items now have editable titles!

### How to Edit Titles:

1. **Hover over any item header**
   - You'll see a small pencil icon (✏️) appear on the right
   - Works for: Charts, Query Results

2. **Click the pencil icon**
   - The title becomes an editable text field
   - Cursor automatically focuses in the input

3. **Edit the title**
   - Type your new title
   - Press **Enter** to save
   - Press **Escape** to cancel

4. **Alternative: Click outside**
   - The title auto-saves when you click elsewhere

### Examples:

**Before:**
```
┌────────────────────────────┐
│ Bar Chart            ✏️    │
│                            │
│   [chart visualization]    │
└────────────────────────────┘
```

**While Editing:**
```
┌────────────────────────────┐
│ [Sales by Region___] ✓     │
│                            │
│   [chart visualization]    │
└────────────────────────────┘
```

**After:**
```
┌────────────────────────────┐
│ Sales by Region            │
│                            │
│   [chart visualization]    │
└────────────────────────────┘
```

## Resizing Items 📏

All items can be resized!

### How to Resize:

1. **Find the resize handle**
   - Look at the bottom-right corner of any item
   - Blue triangle indicator

2. **Drag to resize**
   - Click and hold on the triangle
   - Drag to make larger or smaller
   - Release to finish

3. **Minimum sizes**
   - Width: 200px minimum
   - Height: 150px minimum

### Tips:
- **Charts**: Make bigger to see details
- **Tables**: Expand to show more rows
- **Code blocks**: Shrink if SQL is short
- **Headers**: Adjust to fit your layout

## Dragging Items 🖱️

Move items anywhere on the canvas!

### How to Drag:

1. **Click the drag handle**
   - Blue gradient bar at the top
   - Has hamburger icon (≡) and "Drag to move" text

2. **Drag to new position**
   - Hold and move mouse
   - Item follows cursor
   - Release to drop

3. **Visual feedback**
   - Cursor changes to "grabbing" 👊
   - Handle highlights on hover

## Grouping Questions 📑

Each question creates an organized group!

### Auto-Layout:
```
┌─────────────────────────────────┐
│ 🔍 Question 1                   │  ← Header (blue)
└─────────────────────────────────┘
┌──────────┐  ┌─────────────────┐
│   Code   │  │   Results       │  ← Side-by-side
└──────────┘  └─────────────────┘
┌────────┐ ┌────────┐ ┌────────┐
│ Chart1 │ │ Chart2 │ │ Chart3 │  ← 3 charts
└────────┘ └────────┘ └────────┘

[100px spacing]

┌─────────────────────────────────┐
│ 🔍 Question 2                   │  ← New group
└─────────────────────────────────┘
...
```

## Canvas Controls 🎛️

### Toolbar Features:

**Item Counter**
- Shows total items on canvas
- Updates in real-time

**Clear All**
- Removes all items
- Shows confirmation dialog
- Quick way to start fresh

**Save**
- Saves workspace
- (Demo: shows alert)
- Future: persists to database

**Export**
- Coming soon!
- Will export as PDF/image

### Per-Item Controls:

**Drag Handle** (Top bar)
- Hamburger icon (≡)
- "Drag to move" label
- Hover for highlight

**Delete Button** (×)
- Top-right corner
- Removes individual items
- No confirmation (quick action)

**Resize Handle** (▼)
- Bottom-right corner
- Blue triangle
- Drag to resize

**Edit Title** (✏️)
- Top-right (on hover)
- Charts and tables only
- Inline editing

## Keyboard Shortcuts ⌨️

### While Editing Title:
- **Enter** - Save changes
- **Escape** - Cancel editing

### Coming Soon:
- **Cmd/Ctrl + Z** - Undo
- **Cmd/Ctrl + Y** - Redo
- **Delete** - Delete selected item
- **Cmd/Ctrl + A** - Select all
- **Cmd/Ctrl + D** - Duplicate

## Best Practices 💡

### Organizing Your Canvas:

1. **Use descriptive titles**
   - Rename charts: "Revenue by Quarter"
   - Rename tables: "Top 10 Customers"

2. **Group related items**
   - Keep question groups together
   - Arrange charts for comparison

3. **Resize for clarity**
   - Make important items larger
   - Shrink less critical info

4. **Use Clear All wisely**
   - Start new analysis sessions fresh
   - Don't delete valuable insights

### Creating Dashboards:

1. **Ask multiple questions**
2. **Delete unwanted items**
3. **Rename remaining items**
4. **Resize for balance**
5. **Arrange spatially**
6. **Save (when available)**

## Troubleshooting 🔧

**Title won't edit?**
- Make sure you clicked the pencil icon
- Try clicking directly on the title

**Can't drag item?**
- Click the blue header bar
- Not the content area

**Resize not working?**
- Click the blue triangle in bottom-right
- Not the border

**Item disappeared?**
- Check if scrolled off canvas
- Use Clear All to reset

## Future Features 🚀

- [ ] **Undo/Redo** - Full history
- [ ] **Snap to grid** - Align items
- [ ] **Auto-arrange** - Organize button
- [ ] **Zoom/Pan** - Navigate large canvases
- [ ] **Templates** - Save layouts
- [ ] **Export** - PDF/PNG
- [ ] **Connections** - Draw lines between items
- [ ] **Comments** - Annotate items
- [ ] **Sharing** - Collaborative editing

---

**Happy analyzing! 🎨📊**
