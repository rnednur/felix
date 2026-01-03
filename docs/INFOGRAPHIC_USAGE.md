# Infographic Generation for Deep Research

Professional, enterprise-grade infographic generation for deep research results using template-based approach with reportlab, Pillow, and matplotlib.

## Features

✅ **Enterprise-Ready**
- No external API dependencies (works offline/air-gapped environments)
- Fully deterministic and reproducible
- No per-generation costs
- Compliant with enterprise security policies

✅ **Professional Design**
- 3 color schemes: Professional, Modern, Corporate
- PDF and PNG output formats
- Clean typography and layouts
- Data visualizations and charts

✅ **Easy Integration**
- RESTful API endpoints
- Base64 encoded output
- Simple request/response models

## API Endpoints

### 1. Generate Infographic from Research Results

**POST** `/deep-research/generate-infographic`

Takes existing research results and generates an infographic.

```json
{
  "research_result": {
    "main_question": "...",
    "direct_answer": "...",
    "key_findings": [...],
    ...
  },
  "infographic_request": {
    "format": "pdf",
    "color_scheme": "professional",
    "include_charts": true,
    "include_visualizations": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": "base64_encoded_pdf_or_png...",
  "format": "pdf",
  "filename": "research_infographic_20241120_123456.pdf",
  "size_bytes": 4963
}
```

### 2. Analyze + Generate Infographic (All-in-One)

**POST** `/deep-research/analyze-with-infographic`

Runs deep research AND generates infographic in a single call.

```json
{
  "dataset_id": "my_dataset",
  "question": "What are the key sales trends?",
  "max_sub_questions": 10,
  "enable_python": true,
  "enable_world_knowledge": true,
  "format": "pdf",
  "color_scheme": "professional",
  "include_charts": true,
  "include_visualizations": true
}
```

**Response:**
```json
{
  "success": true,
  "research": {
    "main_question": "...",
    "direct_answer": "...",
    "key_findings": [...],
    ...
  },
  "infographic": {
    "data": "base64_encoded_pdf...",
    "format": "pdf",
    "filename": "research_infographic_20241120_123456.pdf",
    "size_bytes": 4963
  }
}
```

## Usage Examples

### Python Example

```python
import httpx
import base64

# Option 1: Generate infographic from existing research
async def generate_infographic():
    # First, run deep research
    research_response = await httpx.post(
        "http://localhost:8000/deep-research/analyze",
        json={
            "dataset_id": "sales_data",
            "question": "What are the key sales trends?",
            "max_sub_questions": 10
        }
    )
    research_result = research_response.json()

    # Then generate infographic
    infographic_response = await httpx.post(
        "http://localhost:8000/deep-research/generate-infographic",
        json={
            "research_result": research_result,
            "infographic_request": {
                "format": "pdf",
                "color_scheme": "professional",
                "include_charts": True,
                "include_visualizations": True
            }
        }
    )

    result = infographic_response.json()

    # Save PDF to file
    pdf_bytes = base64.b64decode(result['data'])
    with open(result['filename'], 'wb') as f:
        f.write(pdf_bytes)

    print(f"Infographic saved: {result['filename']}")


# Option 2: All-in-one (recommended)
async def analyze_with_infographic():
    response = await httpx.post(
        "http://localhost:8000/deep-research/analyze-with-infographic",
        json={
            "dataset_id": "sales_data",
            "question": "What are the key sales trends?",
            "format": "pdf",
            "color_scheme": "corporate"
        }
    )

    result = response.json()

    # Access research results
    print(result['research']['direct_answer'])

    # Save infographic
    pdf_bytes = base64.b64decode(result['infographic']['data'])
    with open(result['infographic']['filename'], 'wb') as f:
        f.write(pdf_bytes)
```

### cURL Example

```bash
# Generate infographic from research results
curl -X POST http://localhost:8000/deep-research/analyze-with-infographic \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "sales_data",
    "question": "What are the sales trends?",
    "format": "pdf",
    "color_scheme": "modern"
  }' | jq -r '.infographic.data' | base64 -d > infographic.pdf
```

## Configuration Options

### Formats

- **`pdf`**: Professional PDF document (recommended for reports)
- **`png`**: Single-page image (good for presentations)

### Color Schemes

#### Professional (Default)
- Primary: Dark slate blue (#2C3E50)
- Secondary: Blue (#3498DB)
- Clean, corporate look
- Best for: Executive reports, board presentations

#### Modern
- Primary: Deep navy (#1A1A2E)
- Accent: Purple (#533483)
- Contemporary design
- Best for: Tech companies, startups

#### Corporate
- Primary: Navy blue (#003366)
- Accent: Orange (#FF6B35)
- Traditional business style
- Best for: Enterprise, finance

### Options

- **`include_charts`**: Add summary charts (coverage, methods used)
- **`include_visualizations`**: Include visualizations from research results

## Output Structure

### PDF Infographic Includes:

1. **Header**
   - Title: "Deep Research Analysis"
   - Main question
   - Metadata (timestamp, execution time, sub-questions count)

2. **Executive Summary**
   - Direct answer in highlighted box
   - Concise 2-3 sentence summary

3. **Key Findings**
   - Bulleted list of insights
   - Data-backed findings with numbers

4. **Data Coverage Chart**
   - Pie chart showing questions answered vs unanswered
   - Methods used (SQL, Python, LLM)

5. **Visualizations** (optional)
   - Charts and graphs from research
   - Captions for each visualization

6. **Supporting Analysis**
   - Details of each analysis performed
   - Methods and results

7. **Recommended Next Steps**
   - Follow-up questions
   - Areas for deeper investigation

8. **Footer**
   - Research ID
   - Timestamp
   - Page numbers

## Testing

Run the test script to verify infographic generation:

```bash
cd backend
source venv/bin/activate
python test_infographic.py
```

This generates sample infographics in `backend/test_outputs/`:
- `infographic_professional.pdf`
- `infographic_modern.pdf`
- `infographic_corporate.pdf`
- `infographic_professional.png`

## Technical Details

### Dependencies

```
reportlab==4.0.9  # PDF generation
Pillow==10.2.0    # Image manipulation
matplotlib==3.8.2 # Data visualizations
```

### Service Architecture

```
InfographicService
├── Template System (3 color schemes)
├── PDF Generation (reportlab)
│   ├── Header/Footer
│   ├── Executive Summary
│   ├── Key Findings
│   ├── Charts (pie, bar)
│   └── Visualizations
└── PNG Generation (matplotlib)
    └── Single-page layout
```

### Performance

- **PDF Generation**: ~100-200ms (5KB typical)
- **PNG Generation**: ~200-300ms (150KB typical)
- **No external API calls**: 100% local processing
- **Memory efficient**: Streams output, no disk writes

## Best Practices

1. **For Enterprise Reports**: Use PDF format with "corporate" or "professional" scheme
2. **For Presentations**: Use PNG format for easy embedding in slides
3. **For Sharing**: PDF format includes all metadata and is universally readable
4. **For Email**: PNG format has smaller file size, displays inline

## Troubleshooting

**Q: PDF shows "Invalid PDF" error**
- Ensure you're base64 decoding the `data` field
- Check that the full response was received

**Q: Charts not appearing**
- Set `include_charts: true` in request
- Verify research result has `data_coverage` field

**Q: Custom fonts not working**
- Current implementation uses built-in fonts (Helvetica)
- Enterprise environments may restrict font installation

## Future Enhancements

Potential additions (not yet implemented):
- Custom templates (user-defined layouts)
- Additional chart types (line, scatter)
- Multi-page reports with sections
- Logo/branding support
- Interactive PDF forms
- Email integration (auto-send infographics)

## License

Part of the Felix - AI Analytics Platform
