# How to Enable/Disable Verbose Mode in the UI

## Quick Start

**Location:** Deep Research mode in the chat sidebar

**Default:** ✅ Verbose Mode is ENABLED by default (you get comprehensive reports automatically)

---

## Step-by-Step Guide

### 1. Select Deep Research Mode

Click the **"Deep"** button in the analysis mode selector at the top of the chat sidebar.

```
[Auto] [SQL] [Python] [Deep] ← Click here
```

---

### 2. Find the Verbose Mode Toggle

Once Deep Research mode is selected, you'll see a **purple-bordered section** with verbose mode options:

```
┌────────────────────────────────────────────────┐
│ 🧠 Deep research: Multi-stage analysis         │
│                                                 │
│ ┌─────────────────────────────────────────┐   │
│ │ ☑ 📄 Verbose Mode (Multi-page           │   │ ← Purple section
│ │    comprehensive analysis)               │   │
│ │                                          │   │
│ │ Includes: Executive Summary,             │   │
│ │ Methodology, Detailed Findings,          │   │
│ │ Cross-Analysis, Limitations,             │   │
│ │ Recommendations, Technical Appendix      │   │
│ └─────────────────────────────────────────┘   │
└────────────────────────────────────────────────┘
```

---

### 3. Toggle Verbose Mode

#### Enabled (Default):
```
☑ 📄 Verbose Mode (Multi-page comprehensive analysis)

Includes: Executive Summary, Methodology, Detailed Findings,
Cross-Analysis, Limitations, Recommendations, Technical Appendix
```

**What you get:**
- Executive Summary (2-3 paragraphs)
- Methodology & Data Sources
- Detailed Findings (one section per question)
- Cross-Analysis & Patterns
- Limitations & Caveats
- Recommendations with priorities
- Technical Appendix

**Best for:**
- Stakeholder presentations
- Executive reports
- Documentation
- Strategic analysis

---

#### Disabled (Brief Mode):
```
☐ 📄 Verbose Mode (Multi-page comprehensive analysis)

Brief mode: Quick insights and key findings only
```

**What you get:**
- Direct answer (2-3 sentences)
- 5-7 key findings
- Supporting details
- Follow-up questions

**Best for:**
- Quick exploration
- Interactive discovery
- Fast iteration

---

## Complete UI Layout

When Deep Research mode is selected, you'll see options in this order:

```
┌──────────────────────────────────────────────────┐
│ 🧠 Deep research: Multi-stage analysis           │
│                                                   │
│ ┌──────────────────────────────────────────┐    │
│ │ VERBOSE MODE (Purple Section)            │    │ ← 1st
│ │ ☑ Multi-page comprehensive analysis      │    │
│ └──────────────────────────────────────────┘    │
│                                                   │
│ ┌──────────────────────────────────────────┐    │
│ │ INFOGRAPHIC OPTIONS (Blue Section)       │    │ ← 2nd
│ │ ☐ Generate infographic report            │    │
│ │   └─ Generation Method: [Template ▼]     │    │
│ │   └─ Format: [PDF ▼]                     │    │
│ │   └─ Theme: [Professional ▼]             │    │
│ └──────────────────────────────────────────┘    │
│                                                   │
│ [Type your research question here...]            │
│ [Send]                                            │
└──────────────────────────────────────────────────┘
```

---

## Common Workflows

### Workflow 1: Comprehensive Report (Default)
```
1. Select "Deep" mode
2. ☑ Verbose Mode is already checked
3. ☐ Optionally enable infographic
4. Ask your question
5. Get multi-page comprehensive report
```

**Example Question:**
> "What are the revenue trends by segment over the past year?"

**Result:**
- 7-section comprehensive report
- ~60-120 seconds processing time
- Suitable for stakeholder presentation

---

### Workflow 2: Quick Exploration
```
1. Select "Deep" mode
2. ☐ Uncheck Verbose Mode
3. Ask your question
4. Get quick insights
```

**Example Question:**
> "What's our top performing segment?"

**Result:**
- Brief answer with key findings
- ~30-60 seconds processing time
- Perfect for quick checks

---

### Workflow 3: Full Analysis with AI Infographic
```
1. Select "Deep" mode
2. ☑ Verbose Mode (leave enabled)
3. ☑ Check "Generate infographic report"
4. Select "AI-Powered (Gemini Nano Banana Pro)"
5. Ask your question
6. Get comprehensive report + elegant AI-generated infographic
```

**Example Question:**
> "Analyze our customer acquisition trends and profitability"

**Result:**
- 7-section comprehensive report
- AI-generated professional infographic
- ~90-150 seconds processing time
- Publication-ready deliverable

---

## Visual Indicators

### Verbose Mode Enabled
```
┌─────────────────────────────────────────┐
│ ☑ 📄 Verbose Mode                       │ ← Checkbox checked
│                                          │
│ Includes: Executive Summary,             │ ← Green text
│ Methodology, Detailed Findings...        │
└─────────────────────────────────────────┘
```

### Verbose Mode Disabled
```
┌─────────────────────────────────────────┐
│ ☐ 📄 Verbose Mode                       │ ← Checkbox unchecked
│                                          │
│ Brief mode: Quick insights and key       │ ← Gray text
│ findings only                            │
└─────────────────────────────────────────┘
```

---

## Processing Time Comparison

| Mode | Sections | LLM Calls | Time | Best For |
|------|----------|-----------|------|----------|
| **Verbose** | 7 + base | ~12 | 60-120s | Reports, Docs |
| **Brief** | 4 | ~5 | 30-60s | Quick checks |

---

## Tips

1. **Leave Verbose Enabled by default** - You'll get richer insights without extra effort

2. **Disable for rapid iteration** - When exploring data interactively, brief mode is faster

3. **Combine with AI Infographic** - For ultimate deliverable quality:
   - ☑ Verbose Mode
   - ☑ Generate infographic
   - AI-Powered method

4. **Review limitations section** - Verbose mode includes honest assessment of data quality

5. **Use recommendations** - Verbose mode provides prioritized next steps

---

## Troubleshooting

**Q: I don't see the verbose mode toggle**
- **A:** Make sure you've selected "Deep" analysis mode (not SQL/Python/Auto)

**Q: Verbose mode takes too long**
- **A:** This is normal - comprehensive analysis requires more AI processing
- **A:** Use brief mode for faster results during exploration

**Q: Where do I see the verbose sections?**
- **A:** In the Report tab after analysis completes
- **A:** Look for: Executive Summary, Methodology, Detailed Findings, etc.

**Q: Can I change verbose mode mid-analysis?**
- **A:** No - set it before sending your question
- **A:** You can run the same question again with different settings

---

## Summary

**Default Behavior:**
- Verbose Mode is ☑ **ENABLED** by default
- You automatically get comprehensive multi-page reports
- No action needed for full analysis

**To Disable:**
- Click the checkbox to ☐ **uncheck** Verbose Mode
- You'll get brief mode (quick insights only)

**Location:**
- Purple-bordered section in Deep Research mode
- Above the blue infographic options
- Can't miss it! 📄

Enjoy your comprehensive research reports! 🎉
