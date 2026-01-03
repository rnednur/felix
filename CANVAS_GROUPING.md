# 🎨 Canvas Grouping & Organization

## New Features

### 1. **Question Headers**
Each question now gets a beautiful header card that creates a visual group:

```
┌────────────────────────────────────────────────────────┐
│ 🔍 give me incidence of disaster type by country      │
│                                                        │
│ Analysis in progress...                               │
└────────────────────────────────────────────────────────┘
```

**Styling:**
- Blue gradient background
- Large, prominent text
- Spans full width (1400px)
- Auto-positions at the top of each group

### 2. **Auto-Positioning**
Items are automatically organized into groups:

```
Question 1 Header
├── SQL Code Block (left)
├── Results Table (right)
└── Charts Row (3 charts side-by-side)

[100px spacing]

Question 2 Header
├── SQL Code Block (left)
├── Results Table (right)
└── Charts Row (3 charts side-by-side)
```

### 3. **Layout Structure**

**Per Question Group:**
- **Y = base**: Header (80px height)
- **Y = base + 100**: Code Block (left) + Results Table (right)
- **Y = base + 370**: Charts (up to 3, side-by-side)

**Between Groups:**
- 100px spacing automatically added

## Usage

### Ask Multiple Questions

1. **First Question:**
   - Type: "Show sales by region"
   - Items appear: Header → Code → Results → Charts

2. **Second Question:**
   - Type: "What's the average order value?"
   - New group appears below with 100px spacing
   - Items appear: Header → Code → Results → Charts

3. **Third Question:**
   - Keep going! Each question creates its own group

### Canvas Controls

**Toolbar:**
- **Item Count**: Shows total items on canvas
- **Clear All**: Remove all items (with confirmation)
- **Save**: Save workspace (demo alert)
- **Export**: Export canvas (coming soon)

**Per Item:**
- **Drag Handle**: Blue gradient bar with hamburger icon
- **Delete Button**: × on the right side of drag handle
- **Hover Effects**: Highlights on hover

## Visual Hierarchy

### Header (Query Title)
- **Color**: Blue gradient (from-blue-50 to-indigo-50)
- **Border**: 2px blue border
- **Shadow**: Large shadow for emphasis
- **Width**: 1400px (spans most of canvas)
- **Height**: 80px

### Code Block
- **Color**: Dark gray/black background
- **Position**: Left side, below header
- **Width**: 600px
- **Height**: 250px

### Results Table
- **Color**: White background
- **Position**: Right side, next to code
- **Width**: 700px
- **Height**: 400px

### Charts
- **Color**: White background
- **Position**: Below code/results, side-by-side
- **Width**: 600px each
- **Height**: 400px each
- **Spacing**: 650px apart (50px gap)

### Regular Notes (Not Headers)
- **Color**: Yellow gradient
- **Border**: Left border only (4px yellow)
- **With**: Lightbulb icon and "AI Insight" label

## Example Workflow

```bash
1. Enable Canvas Mode
   Click "Tabs Mode" → "Canvas Mode"

2. Ask Question 1
   "Show top customers"

   Canvas shows:
   ┌─────────────────────────────────┐
   │ 🔍 Show top customers           │  ← Header
   └─────────────────────────────────┘
   ┌──────────┐  ┌─────────────────┐
   │   SQL    │  │   Results (10)  │   ← Code + Table
   └──────────┘  └─────────────────┘
   ┌────────┐ ┌────────┐ ┌────────┐
   │  Bar   │ │ Line   │ │ Pie    │   ← 3 Charts
   └────────┘ └────────┘ └────────┘

3. Ask Question 2
   "Sales by region"

   Canvas shows (stacked):
   [Question 1 group from above]

   [100px spacing]

   ┌─────────────────────────────────┐
   │ 🔍 Sales by region              │  ← New Header
   └─────────────────────────────────┘
   ┌──────────┐  ┌─────────────────┐
   │   SQL    │  │   Results       │   ← New Code + Table
   └──────────┘  └─────────────────┘
   ┌────────┐ ┌────────┐
   │  Bar   │ │ Map    │              ← New Charts
   └────────┘ └────────┘

4. Organize
   - Drag items to rearrange
   - Delete items you don't need
   - Clear all to start fresh
```

## Tips

### Best Practices
- **Keep groups together**: Don't drag items too far from their header
- **Use Clear All**: When starting a new analysis session
- **Ask related questions**: Build a narrative flow

### Advanced Usage
- **Compare Results**: Ask similar questions, then arrange charts side-by-side
- **Build Dashboards**: Ask multiple questions, delete unwanted items, arrange the rest
- **Export**: (Coming soon) Save canvas as PDF for reports

## Future Enhancements

- [ ] **Collapsible Groups**: Click header to collapse/expand entire group
- [ ] **Group Background**: Subtle background color for each group
- [ ] **Auto-arrange**: Button to auto-organize all groups
- [ ] **Templates**: Save group arrangements as templates
- [ ] **Connections**: Draw lines between related items
- [ ] **Zoom/Pan**: Navigate large canvases
- [ ] **Mini-map**: Overview of entire canvas

---

**Pro Tip**: Think of canvas mode as your analytical notebook. Each question is a new section, and you can organize sections however makes sense for your story! 📊
