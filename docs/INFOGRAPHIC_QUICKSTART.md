# Infographic Generation - Quick Start Guide

Get professional infographics from your deep research in 5 minutes.

## 🚀 Quick Start

### 1. Dependencies Already Installed ✅

The required libraries are already installed:
- reportlab==4.0.9
- Pillow==10.2.0
- matplotlib==3.8.2

### 2. Test It Works

```bash
cd backend
source venv/bin/activate
python test_infographic.py
```

You should see:
```
✅ Success! infographic_professional.pdf
✅ Success! infographic_modern.pdf
✅ Success! infographic_corporate.pdf
✅ Success! infographic_professional.png
```

Check `backend/test_outputs/` for generated files.

### 3. Use It in Your Code

#### Option A: All-in-One (Recommended)

```python
import httpx
import base64

async def analyze_and_generate():
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "http://localhost:8000/deep-research/analyze-with-infographic",
            json={
                "dataset_id": "your_dataset_id",
                "question": "What are the key sales trends?",
                "format": "pdf",
                "color_scheme": "professional"
            }
        )

        result = response.json()

        # Get research results
        print(result['research']['direct_answer'])

        # Save infographic
        pdf_bytes = base64.b64decode(result['infographic']['data'])
        with open('infographic.pdf', 'wb') as f:
            f.write(pdf_bytes)

        print(f"Saved: {result['infographic']['filename']}")
```

#### Option B: Separate Calls

```python
# 1. Run research
research = await client.post("/deep-research/analyze", json={
    "dataset_id": "your_dataset_id",
    "question": "What are the key sales trends?"
})
research_data = research.json()

# 2. Generate infographic
infographic = await client.post("/deep-research/generate-infographic", json={
    "research_result": research_data,
    "infographic_request": {
        "format": "pdf",
        "color_scheme": "corporate",
        "include_charts": True,
        "include_visualizations": True
    }
})

result = infographic.json()
pdf_bytes = base64.b64decode(result['data'])
```

## 📝 Available Options

### Formats
- `"pdf"` - Professional PDF document (5KB, best for reports)
- `"png"` - Single-page image (150KB, best for presentations)

### Color Schemes
- `"professional"` - Dark blue, clean (default)
- `"modern"` - Navy, purple (contemporary)
- `"corporate"` - Navy, orange (traditional business)

### Options
- `include_charts: true` - Add data coverage charts
- `include_visualizations: true` - Include research visualizations

## 🎯 Common Use Cases

### 1. Executive Report (PDF)
```json
{
  "format": "pdf",
  "color_scheme": "professional",
  "include_charts": true,
  "include_visualizations": true
}
```

### 2. Client Deliverable (PDF)
```json
{
  "format": "pdf",
  "color_scheme": "corporate",
  "include_charts": true,
  "include_visualizations": false
}
```

### 3. Presentation Slide (PNG)
```json
{
  "format": "png",
  "color_scheme": "modern",
  "include_charts": false,
  "include_visualizations": true
}
```

## 📊 What Gets Included

Your infographic automatically includes:

1. ✅ **Header**: Question + metadata
2. ✅ **Executive Summary**: Direct answer in highlighted box
3. ✅ **Key Findings**: Bulleted insights
4. ✅ **Data Coverage Chart**: Visual breakdown
5. ✅ **Visualizations**: Charts from research (optional)
6. ✅ **Supporting Details**: Analysis breakdown
7. ✅ **Follow-up Questions**: Recommended next steps
8. ✅ **Footer**: Timestamp + research ID

## 🔧 Troubleshooting

**Q: I get a connection error**
```
Make sure backend is running:
uvicorn app.main:app --reload --port 8000
```

**Q: Import error for reportlab/Pillow/matplotlib**
```bash
cd backend
source venv/bin/activate
pip install reportlab==4.0.9 Pillow==10.2.0 matplotlib==3.8.2
```

**Q: Base64 decode error**
```python
# Ensure you're decoding the 'data' field:
pdf_bytes = base64.b64decode(result['data'])
# NOT: base64.b64decode(result)
```

## 📚 Next Steps

- **Full Documentation**: See `INFOGRAPHIC_USAGE.md`
- **Examples**: See `example_infographic_client.py`
- **Implementation Details**: See `INFOGRAPHIC_SUMMARY.md`

## ⚡ Performance

- Generation: ~100-200ms
- PDF Size: ~5KB
- PNG Size: ~150KB
- No external API calls
- Works offline

## 🎓 Tips

1. **For enterprise**: Use PDF format (universal, small size)
2. **For presentations**: Use PNG format (embeds easily in slides)
3. **Test first**: Run `test_infographic.py` to verify setup
4. **Multiple versions**: Generate all 3 color schemes, pick the best

---

**Ready to use!** 🚀

Start with: `python test_infographic.py`
