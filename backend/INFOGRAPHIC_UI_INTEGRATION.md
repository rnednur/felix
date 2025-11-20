# Infographic UI Integration Guide

## How to Trigger Infographic Generation from Frontend

You now have **3 options** for generating infographics from your UI:

---

## ✅ Option 1: Automatic with Flag (RECOMMENDED) ⭐

The `/analyze` endpoint now accepts an optional `generate_infographic` parameter.

### Backend API

**Endpoint:** `POST /deep-research/analyze`

**Request:**
```json
{
  "dataset_id": "abc123",
  "question": "What are the sales trends?",
  "generate_infographic": true,
  "infographic_format": "pdf",
  "infographic_color_scheme": "professional"
}
```

**Response:**
```json
{
  "success": true,
  "main_question": "...",
  "direct_answer": "...",
  "key_findings": [...],
  "infographic": {
    "data": "base64_encoded_pdf...",
    "format": "pdf",
    "filename": "research_infographic_20241120_123456.pdf",
    "size_bytes": 4963
  }
}
```

### Frontend Implementation

#### 1. Add Checkbox to Deep Research Form

```tsx
// In your deep research component
import { useState } from 'react';

export function DeepResearchPanel() {
  const [generateInfographic, setGenerateInfographic] = useState(false);
  const [infographicFormat, setInfographicFormat] = useState('pdf');
  const [colorScheme, setColorScheme] = useState('professional');

  return (
    <div>
      {/* Existing question input */}
      <textarea
        placeholder="Ask a deep research question..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />

      {/* NEW: Infographic options */}
      <div className="mt-4 space-y-2">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={generateInfographic}
            onChange={(e) => setGenerateInfographic(e.target.checked)}
          />
          <span>Generate Infographic</span>
        </label>

        {generateInfographic && (
          <div className="ml-6 space-y-2">
            <select
              value={infographicFormat}
              onChange={(e) => setInfographicFormat(e.target.value)}
            >
              <option value="pdf">PDF</option>
              <option value="png">PNG</option>
            </select>

            <select
              value={colorScheme}
              onChange={(e) => setColorScheme(e.target.value)}
            >
              <option value="professional">Professional</option>
              <option value="modern">Modern</option>
              <option value="corporate">Corporate</option>
            </select>
          </div>
        )}
      </div>

      <button onClick={handleSubmit}>Analyze</button>
    </div>
  );
}
```

#### 2. Update API Call

```tsx
const handleSubmit = async () => {
  const response = await fetch('/deep-research/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      dataset_id: datasetId,
      question: question,
      generate_infographic: generateInfographic,
      infographic_format: infographicFormat,
      infographic_color_scheme: colorScheme
    })
  });

  const result = await response.json();

  // Display research results
  setResearchResults(result);

  // If infographic was generated, show download button
  if (result.infographic) {
    setInfographic(result.infographic);
  }
};
```

#### 3. Add Download Button

```tsx
// Show download button if infographic exists
{infographic && (
  <button
    onClick={() => downloadInfographic(infographic)}
    className="btn-primary"
  >
    📊 Download {infographic.format.toUpperCase()} Infographic
  </button>
)}
```

#### 4. Download Handler

```tsx
const downloadInfographic = (infographic: any) => {
  // Decode base64
  const byteCharacters = atob(infographic.data);
  const byteNumbers = new Array(byteCharacters.length);
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  const byteArray = new Uint8Array(byteNumbers);

  // Create blob
  const mimeType = infographic.format === 'pdf'
    ? 'application/pdf'
    : 'image/png';
  const blob = new Blob([byteArray], { type: mimeType });

  // Download
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = infographic.filename;
  link.click();
  URL.revokeObjectURL(url);
};
```

---

## Option 2: Separate Button (Manual Trigger)

Add a "Generate Infographic" button that appears AFTER research completes.

### Frontend Implementation

```tsx
// After deep research completes
{researchResults && (
  <div>
    {/* Show research results */}
    <ResearchResults data={researchResults} />

    {/* NEW: Generate infographic button */}
    <button onClick={handleGenerateInfographic}>
      📊 Generate Infographic
    </button>
  </div>
)}
```

```tsx
const handleGenerateInfographic = async () => {
  const response = await fetch('/deep-research/generate-infographic', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      research_result: researchResults,
      infographic_request: {
        format: 'pdf',
        color_scheme: 'professional',
        include_charts: true,
        include_visualizations: true
      }
    })
  });

  const result = await response.json();

  if (result.success) {
    downloadInfographic(result);
  }
};
```

---

## Option 3: Always Auto-Generate (Simplest UX)

Set `generate_infographic: true` by default - no UI changes needed!

```tsx
const handleSubmit = async () => {
  const response = await fetch('/deep-research/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      dataset_id: datasetId,
      question: question,
      generate_infographic: true,  // Always true
      infographic_format: 'pdf',
      infographic_color_scheme: 'professional'
    })
  });

  const result = await response.json();

  // Infographic is always available in result.infographic
  if (result.infographic) {
    // Auto-show download button
  }
};
```

---

## Comparison of Options

| Option | User Control | UX Simplicity | When to Use |
|--------|--------------|---------------|-------------|
| **Option 1: Flag** ⭐ | ✅ High | Medium | Best for most cases - users can opt-in |
| **Option 2: Button** | ✅ High | Low | When infographics are optional/advanced |
| **Option 3: Auto** | ❌ None | ✅ High | When you always want infographics |

---

## Recommended UX Flow (Option 1)

1. User asks deep research question
2. Checkbox: "☐ Generate infographic report"
   - If checked, shows format selector (PDF/PNG) and color scheme
3. Click "Analyze"
4. Results appear with research + download button (if infographic was requested)

### Benefits:
- ✅ User has control
- ✅ No extra step needed
- ✅ Fast (generated during research)
- ✅ Simple to implement

---

## Example: Complete Component

```tsx
import { useState } from 'react';

export function DeepResearchPanel({ datasetId }: { datasetId: string }) {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);

  // Infographic options
  const [generateInfographic, setGenerateInfographic] = useState(false);
  const [format, setFormat] = useState('pdf');
  const [colorScheme, setColorScheme] = useState('professional');

  const handleAnalyze = async () => {
    setLoading(true);

    try {
      const response = await fetch('/deep-research/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_id: datasetId,
          question: question,
          generate_infographic: generateInfographic,
          infographic_format: format,
          infographic_color_scheme: colorScheme
        })
      });

      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadInfographic = () => {
    if (!results?.infographic) return;

    const { data, format, filename } = results.infographic;

    // Base64 to blob
    const byteCharacters = atob(data);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const mimeType = format === 'pdf' ? 'application/pdf' : 'image/png';
    const blob = new Blob([byteArray], { type: mimeType });

    // Download
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-bold">Deep Research</h2>

      <textarea
        className="w-full p-2 border rounded"
        placeholder="Ask a research question..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        rows={3}
      />

      <div className="space-y-2">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={generateInfographic}
            onChange={(e) => setGenerateInfographic(e.target.checked)}
          />
          <span>Generate infographic report</span>
        </label>

        {generateInfographic && (
          <div className="ml-6 space-y-2">
            <div>
              <label className="block text-sm">Format:</label>
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                className="border rounded p-1"
              >
                <option value="pdf">PDF (for reports)</option>
                <option value="png">PNG (for presentations)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm">Theme:</label>
              <select
                value={colorScheme}
                onChange={(e) => setColorScheme(e.target.value)}
                className="border rounded p-1"
              >
                <option value="professional">Professional</option>
                <option value="modern">Modern</option>
                <option value="corporate">Corporate</option>
              </select>
            </div>
          </div>
        )}
      </div>

      <button
        onClick={handleAnalyze}
        disabled={loading || !question}
        className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
      >
        {loading ? 'Analyzing...' : 'Analyze'}
      </button>

      {results && (
        <div className="mt-6 space-y-4">
          <div className="p-4 bg-gray-50 rounded">
            <h3 className="font-bold">Direct Answer:</h3>
            <p>{results.direct_answer}</p>
          </div>

          <div>
            <h3 className="font-bold">Key Findings:</h3>
            <ul className="list-disc ml-6">
              {results.key_findings.map((finding: string, i: number) => (
                <li key={i}>{finding}</li>
              ))}
            </ul>
          </div>

          {results.infographic && (
            <button
              onClick={downloadInfographic}
              className="px-4 py-2 bg-green-600 text-white rounded"
            >
              📊 Download {results.infographic.format.toUpperCase()} Infographic
            </button>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## Testing

1. **Start backend**: `uvicorn app.main:app --reload`
2. **Test with curl**:
```bash
curl -X POST http://localhost:8000/deep-research/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "your_dataset_id",
    "question": "What are the trends?",
    "generate_infographic": true,
    "infographic_format": "pdf",
    "infographic_color_scheme": "professional"
  }' | jq '.infographic'
```

---

## Summary

**Recommended Approach: Option 1 (Checkbox)**

✅ User has control
✅ Generated automatically if checked
✅ No extra API call needed
✅ Results include infographic when available

Just add a checkbox to your form and handle the download!
