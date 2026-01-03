# PowerPoint Generation for Deep Research

Generate professional PowerPoint presentations from deep research results with customizable themes.

## Features

- ✅ **Auto-generation from research results** - One-click PowerPoint creation
- ✅ **4 Professional themes** - Professional, Modern, Corporate, Vibrant
- ✅ **Complete coverage** - Title, summary, findings, details, recommendations
- ✅ **Verbose mode support** - Include methodology and technical sections
- ✅ **Data tables** - Automatic formatting of analysis results
- ✅ **Download support** - Base64 encoding for direct download
- ✅ **Custom styling** - Branded colors, fonts, and layouts

## Quick Start

### 1. Install Dependencies

```bash
pip install python-pptx
```

### 2. Generate Presentation

**From API:**

```bash
curl -X POST http://localhost:8000/api/v1/deep-research/generate-presentation \
  -H "Content-Type: application/json" \
  -d '{
    "research_id": "abc123",
    "theme": "professional",
    "include_verbose": true
  }'
```

**From Frontend:**

Click the **PowerPoint** button in the report view, select a theme, and download!

## Themes

### Professional
- **Primary**: Dark Blue (#1F4E79)
- **Secondary**: Light Blue (#4472C4)
- **Accent**: Orange (#ED7D31)
- **Use case**: Business presentations, corporate reports

### Modern
- **Primary**: Cyan (#00B0F0)
- **Secondary**: Sky Blue (#5B9BD5)
- **Accent**: Gold (#FFC000)
- **Use case**: Tech presentations, innovation reports

### Corporate
- **Primary**: Navy (#29384F)
- **Secondary**: Corporate Blue (#4F81BD)
- **Accent**: Red (#C00000)
- **Use case**: Executive presentations, formal reports

### Vibrant
- **Primary**: Purple (#8E44AD)
- **Secondary**: Bright Blue (#3498DB)
- **Accent**: Green (#2ECC71)
- **Use case**: Creative presentations, marketing decks

## Slide Structure

Generated presentations include:

1. **Title Slide** - Research question + date
2. **Executive Summary** - Direct answer to main question
3. **Key Findings** - Bullet points (auto-paginated if > 5)
4. **Supporting Details** - One slide per analysis with data tables
5. **Methodology** *(if verbose)* - Research approach and methods
6. **Recommendations** *(if verbose)* - Action items
7. **Limitations** - Caveats and constraints
8. **Next Steps** - Suggested follow-up questions

## API Reference

### Generate Presentation

**POST** `/deep-research/generate-presentation`

Request:
```json
{
  "research_id": "abc123",  // OR provide research_result directly
  "research_result": {...},  // Optional: provide data instead of ID
  "theme": "professional",   // professional, modern, corporate, vibrant
  "include_verbose": true    // Include methodology sections
}
```

Response:
```json
{
  "success": true,
  "message": "Presentation generated successfully",
  "file_path": "data/presentations/research_20241127_150430.pptx",
  "file_name": "research_20241127_150430.pptx",
  "file_size": 45678,
  "data": "UEsDBBQABgAI...",  // Base64 encoded PPTX
  "theme": "professional"
}
```

### Download Presentation

**GET** `/deep-research/download-presentation/{filename}`

Returns PPTX file with proper Content-Disposition headers.

## Frontend Integration

### React Hook

```typescript
import { useGeneratePresentation, downloadPresentationFromBase64 } from '@/hooks/usePresentation'

const generatePresentation = useGeneratePresentation()

generatePresentation.mutate(
  {
    research_result: myResearchData,
    theme: 'modern',
    include_verbose: true
  },
  {
    onSuccess: (data) => {
      // Auto-download
      downloadPresentationFromBase64(data.data, data.file_name)
    }
  }
)
```

### Button Component

```tsx
<button onClick={() => generatePresentation.mutate({...})}>
  <Presentation className="h-4 w-4" />
  Generate PowerPoint
</button>
```

## Customization

### Add Custom Theme

Edit `app/services/presentation_service.py`:

```python
THEMES = {
    "custom": {
        "primary": RGBColor(12, 34, 56),
        "secondary": RGBColor(78, 90, 12),
        "accent": RGBColor(34, 56, 78),
        "text": RGBColor(51, 51, 51),
        "background": RGBColor(255, 255, 255),
    }
}
```

### Customize Slide Content

Modify methods in `PresentationService`:

```python
def _add_custom_slide(self, data: Dict[str, Any]):
    slide = self.prs.slides.add_slide(self.prs.slide_layouts[6])
    # Add your custom content
    self._add_slide_title(slide, "Custom Slide")
    # ...
```

### Change Fonts

```python
# In slide text formatting
p.font.name = "Arial"
p.font.size = Pt(14)
p.font.bold = True
```

## Architecture

```
Research Result (JSON)
        ↓
PresentationService
        ↓
python-pptx (PPTX generation)
        ↓
Base64 encoding
        ↓
API Response → Frontend → Download
```

## File Storage

Generated presentations are saved to:
```
data/presentations/research_{timestamp}.pptx
```

Format: `research_YYYYMMDD_HHMMSS.pptx`

## Performance

- **Generation time**: ~2-5 seconds for typical report
- **File size**: 40-100 KB (depending on content)
- **Slide limit**: 20 slides max (configurable)

## Limitations

1. **No images**: Current implementation doesn't include charts/graphs
2. **Basic tables**: Limited to 5 rows per table
3. **Text only**: No embedded visualizations
4. **Static themes**: Themes are predefined, not AI-generated

## Future Enhancements

- [ ] **Chart generation** - Convert Vega-Lite specs to PowerPoint charts
- [ ] **Image support** - Embed infographics and visualizations
- [ ] **Custom templates** - User-uploaded PPTX templates
- [ ] **AI theme generation** - LLM-generated color schemes
- [ ] **Speaker notes** - Auto-generated presentation notes
- [ ] **Animations** - Slide transitions and animations
- [ ] **Master slides** - Professional slide masters
- [ ] **Branding** - Logo and corporate identity integration

## Comparison with presentation-ai

| Feature | Our Implementation | presentation-ai |
|---------|-------------------|-----------------|
| Backend | Python + FastAPI | Next.js + Prisma |
| Generation | python-pptx | Browser-based |
| Integration | Deep research | Standalone app |
| Themes | 4 built-in | 9 + custom |
| Export | PPTX | Web view only* |
| AI Content | Research-driven | OpenAI-generated |
| Deployment | Server-side | Full web app |

*Note: presentation-ai has PowerPoint export on roadmap

## Why This Approach?

**Advantages:**
- ✅ Server-side generation (no browser limits)
- ✅ Tight integration with research pipeline
- ✅ No additional UI needed
- ✅ Direct file download
- ✅ Consistent formatting

**vs presentation-ai:**
- Their approach: Full-featured web app for creating presentations from scratch
- Our approach: Auto-generate from research results, no manual editing needed

## Examples

### Basic Usage

```python
from app.services.presentation_service import PresentationService

service = PresentationService()
output_path = service.generate_presentation(
    research_result=my_research_data,
    theme="modern",
    include_verbose=True
)
# Returns: data/presentations/research_20241127_150430.pptx
```

### Custom Output Path

```python
output_path = service.generate_presentation(
    research_result=data,
    theme="corporate",
    output_path="custom/path/my_presentation.pptx"
)
```

## Troubleshooting

### Import Error: No module named 'pptx'

```bash
pip install python-pptx
```

### Presentation won't download

Check browser console for errors. Verify base64 decoding:

```javascript
console.log(data.data.substring(0, 50))  // Should start with "UEsDBB..."
```

### Theme not applied

Ensure theme name is valid:
```python
valid_themes = ["professional", "modern", "corporate", "vibrant"]
```

### File too large

Presentations with many details can be large. Limit supporting_details:

```python
details = data.get("supporting_details", [])[:10]  # Limit to 10
```

## Resources

- [python-pptx documentation](https://python-pptx.readthedocs.io/)
- [PowerPoint XML reference](https://docs.microsoft.com/en-us/office/open-xml/working-with-presentations)
- [presentation-ai repo](https://github.com/allweonedev/presentation-ai)
