# Frontend Changes Required for Infographic Generation

## Overview
Add checkbox and options to generate infographics when using Deep Research mode.

---

## Option 1: Add to ChatSidebar (Simplest) ⭐ RECOMMENDED

### File: `src/components/chat/ChatSidebar.tsx`

Add infographic options to the chat sidebar when in `deep-research` mode.

#### Step 1: Add Props

```tsx
// Add to ChatSidebarProps interface (around line 25)
interface ChatSidebarProps {
  datasetId?: string
  datasetInfo?: DatasetInfo
  onQuerySubmit: (query: string, mode?: AnalysisMode) => void
  messages: Message[]
  isLoading?: boolean
  analysisMode?: AnalysisMode
  onModeChange?: (mode: AnalysisMode) => void

  // NEW: Add these props
  generateInfographic?: boolean
  onInfographicToggle?: (value: boolean) => void
  infographicFormat?: 'pdf' | 'png'
  onInfographicFormatChange?: (format: 'pdf' | 'png') => void
  infographicColorScheme?: 'professional' | 'modern' | 'corporate'
  onInfographicColorSchemeChange?: (scheme: 'professional' | 'modern' | 'corporate') => void
}
```

#### Step 2: Add UI Controls

Replace the Deep Research hint (around line 246-250) with:

```tsx
{analysisMode === 'deep-research' && (
  <div className="space-y-3">
    <div className="text-xs text-gray-500">
      🧠 Deep research: Multi-stage analysis with insights
    </div>

    {/* NEW: Infographic Options */}
    <div className="space-y-2 bg-blue-50 border border-blue-200 rounded-lg p-3">
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={generateInfographic}
          onChange={(e) => onInfographicToggle?.(e.target.checked)}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <span className="text-sm font-medium text-gray-700">
          📊 Generate infographic report
        </span>
      </label>

      {generateInfographic && (
        <div className="ml-6 space-y-2">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Format:
            </label>
            <select
              value={infographicFormat}
              onChange={(e) => onInfographicFormatChange?.(e.target.value as 'pdf' | 'png')}
              className="w-full text-xs border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="pdf">PDF (best for reports)</option>
              <option value="png">PNG (best for presentations)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Theme:
            </label>
            <select
              value={infographicColorScheme}
              onChange={(e) => onInfographicColorSchemeChange?.(e.target.value as any)}
              className="w-full text-xs border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="professional">Professional (clean blue)</option>
              <option value="modern">Modern (dark navy)</option>
              <option value="corporate">Corporate (traditional)</option>
            </select>
          </div>
        </div>
      )}
    </div>
  </div>
)}
```

---

## Step 3: Update DatasetDetail.tsx

### File: `src/pages/DatasetDetail.tsx`

#### A. Add State (after line 43)

```tsx
// Infographic options
const [generateInfographic, setGenerateInfographic] = useState(false)
const [infographicFormat, setInfographicFormat] = useState<'pdf' | 'png'>('pdf')
const [infographicColorScheme, setInfographicColorScheme] = useState<'professional' | 'modern' | 'corporate'>('professional')
const [currentInfographic, setCurrentInfographic] = useState<any>(null)
```

#### B. Update ChatSidebar Props (around line 534)

```tsx
<ChatSidebar
  datasetId={id}
  onQuerySubmit={handleQuerySubmit}
  messages={messages}
  isLoading={nlQueryMutation.isPending || isGeneratingCode || isExecuting}
  analysisMode={analysisMode}
  onModeChange={setAnalysisMode}

  {/* NEW: Add infographic props */}
  generateInfographic={generateInfographic}
  onInfographicToggle={setGenerateInfographic}
  infographicFormat={infographicFormat}
  onInfographicFormatChange={setInfographicFormat}
  infographicColorScheme={infographicColorScheme}
  onInfographicColorSchemeChange={setInfographicColorScheme}
/>
```

#### C. Modify Deep Research API Call (around line 248)

**IMPORTANT:** The streaming endpoint doesn't support infographics yet. You need to switch to the non-streaming endpoint when infographics are requested.

Replace the deep research section (lines 239-360) with:

```tsx
// Deep Research mode
if (mode === 'deep-research') {
  setMessages((prev) => [...prev, {
    role: 'assistant',
    content: '🧠 Starting deep research analysis...'
  }])

  try {
    const apiUrl = import.meta.env.VITE_API_URL || '/api/v1'

    // Use regular POST endpoint (supports infographics)
    const response = await fetch(`${apiUrl}/deep-research/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dataset_id: id!,
        question: query,
        max_sub_questions: 10,
        enable_python: true,
        enable_world_knowledge: true,
        generate_infographic: generateInfographic,
        infographic_format: infographicFormat,
        infographic_color_scheme: infographicColorScheme
      })
    })

    const result = await response.json()

    if (!result.success) {
      throw new Error(result.error || 'Deep research failed')
    }

    // Format response
    let responseText = `## ${result.main_question}\n\n`
    responseText += `**Direct Answer:**\n${result.direct_answer}\n\n`

    if (result.key_findings?.length > 0) {
      responseText += `**Key Findings:**\n`
      result.key_findings.forEach((finding: string, idx: number) => {
        responseText += `${idx + 1}. ${finding}\n`
      })
      responseText += '\n'
    }

    // Add visualizations
    if (result.visualizations?.length > 0) {
      responseText += `**Visualizations:**\n\n`
      result.visualizations.forEach((viz: any, idx: number) => {
        responseText += `<div class="visualization-container" style="margin: 16px 0; padding: 12px; background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">\n`
        responseText += `<p style="font-size: 13px; color: #6b7280; margin-bottom: 8px;"><strong>Figure ${idx + 1}:</strong> ${viz.caption}</p>\n`
        responseText += `<img src="data:${viz.format === 'png' ? 'image/png' : 'image/jpeg'};base64,${viz.data}" style="max-width: 100%; height: auto; border-radius: 4px;" />\n`
        responseText += `</div>\n\n`
      })
    }

    if (result.data_coverage) {
      responseText += `**Data Coverage:**\n`
      if (result.data_coverage.questions_answered) {
        responseText += `✅ Answered: ${result.data_coverage.questions_answered} sub-questions\n`
      }
      if (result.data_coverage.gaps?.length > 0) {
        responseText += `⚠️ Gaps: ${result.data_coverage.gaps.join(', ')}\n`
      }
      responseText += '\n'
    }

    if (result.follow_up_questions?.length > 0) {
      responseText += `**Suggested Follow-ups:**\n`
      result.follow_up_questions.forEach((q: string, idx: number) => {
        responseText += `${idx + 1}. ${q}\n`
      })
    }

    responseText += `\n_Analysis completed in ${result.execution_time_seconds.toFixed(1)}s_`

    // Save infographic if generated
    if (result.infographic) {
      setCurrentInfographic(result.infographic)
      responseText += `\n\n📊 **Infographic report generated!** Click Download button above.`
    }

    // Save full report
    setDeepResearchReport(result)
    setCurrentView('report')

    // Update messages
    setMessages((prev) => {
      const newMessages = [...prev]
      newMessages[newMessages.length - 1] = {
        role: 'assistant',
        content: `✅ Deep research complete! View the full report in the **Report** tab.`
      }
      return newMessages
    })

  } catch (error) {
    console.error('Deep research failed:', error)
    setMessages((prev) => {
      const newMessages = [...prev]
      newMessages[newMessages.length - 1] = {
        role: 'assistant',
        content: `❌ Deep research failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      }
      return newMessages
    })
  }

  return
}
```

#### D. Add Download Button in Report Tab

Add a download infographic button when viewing the report. Find the `<ReportView>` component (around line 547) and add a button above it:

```tsx
{currentView === 'report' && deepResearchReport && (
  <div className="p-4 border-b border-gray-200 bg-gray-50">
    <div className="flex items-center justify-between">
      <div>
        <h3 className="font-semibold text-gray-900">Deep Research Report</h3>
        <p className="text-sm text-gray-600">{deepResearchReport.main_question}</p>
      </div>

      {/* NEW: Infographic Download Button */}
      {currentInfographic && (
        <button
          onClick={() => {
            // Download infographic
            const { data, format, filename } = currentInfographic

            // Convert base64 to blob
            const byteCharacters = atob(data)
            const byteNumbers = new Array(byteCharacters.length)
            for (let i = 0; i < byteCharacters.length; i++) {
              byteNumbers[i] = byteCharacters.charCodeAt(i)
            }
            const byteArray = new Uint8Array(byteNumbers)
            const mimeType = format === 'pdf' ? 'application/pdf' : 'image/png'
            const blob = new Blob([byteArray], { type: mimeType })

            // Trigger download
            const url = URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url
            link.download = filename
            link.click()
            URL.revokeObjectURL(url)
          }}
          className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg flex items-center gap-2 text-sm font-medium transition-colors"
        >
          📊 Download {currentInfographic.format.toUpperCase()} Infographic
          <span className="text-xs opacity-90">
            ({(currentInfographic.size_bytes / 1024).toFixed(1)} KB)
          </span>
        </button>
      )}
    </div>
  </div>
)}
```

---

## Testing

1. **Start backend**: `uvicorn app.main:app --reload`
2. **Start frontend**: `cd frontend && npm run dev`
3. **Test flow**:
   - Select a dataset
   - Click "Deep" mode
   - Check "Generate infographic report"
   - Select format (PDF/PNG) and theme
   - Ask a deep research question
   - Wait for analysis
   - Click "Download PDF Infographic" button

---

## Quick Visual Guide

### Before (Current):
```
┌─────────────────────────────────────┐
│ [Auto] [SQL] [Python] [Deep]       │
│                                      │
│ ┌─────────────────────────────────┐ │
│ │ Try: "Why are sales declining?" │ │
│ └─────────────────────────────────┘ │
│                                      │
│ 🧠 Deep research: Multi-stage...    │
└─────────────────────────────────────┘
```

### After (With Infographic Option):
```
┌─────────────────────────────────────┐
│ [Auto] [SQL] [Python] [Deep]       │
│                                      │
│ ┌─────────────────────────────────┐ │
│ │ Try: "Why are sales declining?" │ │
│ └─────────────────────────────────┘ │
│                                      │
│ 🧠 Deep research: Multi-stage...    │
│                                      │
│ ┌─────────────────────────────────┐ │
│ │ ☑ 📊 Generate infographic report│ │
│ │   Format: [PDF ▼]               │ │
│ │   Theme:  [Professional ▼]      │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

---

## Summary of Changes

**Files to Modify:**

1. ✅ `src/components/chat/ChatSidebar.tsx`
   - Add props for infographic options
   - Add UI controls (checkbox + selectors)

2. ✅ `src/pages/DatasetDetail.tsx`
   - Add state for infographic preferences
   - Pass props to ChatSidebar
   - Modify deep research API call to include infographic params
   - Add download button in report view

**Total Changes:** ~100 lines of code across 2 files

**Difficulty:** Easy (copy-paste changes)

**Time Estimate:** 15-20 minutes
