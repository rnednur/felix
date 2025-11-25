"""
Infographic Generation Service

Generates professional, enterprise-grade infographics from deep research results
using either template-based approach or AI-powered generation.

Features:
- PDF generation with professional layouts
- Data visualizations (charts, graphs)
- Template-based design system (no external APIs)
- AI-powered generation using Gemini Nano Banana Pro (optional, via OpenRouter)
"""

import io
import base64
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure

from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont


class InfographicTemplate:
    """Base template configuration"""

    # Color schemes - Professional enterprise palettes
    COLOR_SCHEMES = {
        'professional': {
            'primary': colors.HexColor('#2C3E50'),
            'secondary': colors.HexColor('#3498DB'),
            'accent': colors.HexColor('#E74C3C'),
            'success': colors.HexColor('#27AE60'),
            'warning': colors.HexColor('#F39C12'),
            'background': colors.HexColor('#ECF0F1'),
            'text': colors.HexColor('#2C3E50'),
            'light_gray': colors.HexColor('#BDC3C7')
        },
        'modern': {
            'primary': colors.HexColor('#1A1A2E'),
            'secondary': colors.HexColor('#16213E'),
            'accent': colors.HexColor('#0F3460'),
            'success': colors.HexColor('#533483'),
            'warning': colors.HexColor('#E94560'),
            'background': colors.HexColor('#F5F5F5'),
            'text': colors.HexColor('#1A1A2E'),
            'light_gray': colors.HexColor('#D1D5DB')
        },
        'corporate': {
            'primary': colors.HexColor('#003366'),
            'secondary': colors.HexColor('#0066CC'),
            'accent': colors.HexColor('#FF6B35'),
            'success': colors.HexColor('#4CAF50'),
            'warning': colors.HexColor('#FFA726'),
            'background': colors.HexColor('#F8F9FA'),
            'text': colors.HexColor('#212529'),
            'light_gray': colors.HexColor('#CED4DA')
        }
    }

    def __init__(self, color_scheme: str = 'professional'):
        self.colors = self.COLOR_SCHEMES.get(color_scheme, self.COLOR_SCHEMES['professional'])
        self.page_width, self.page_height = letter
        self.margin = 0.75 * inch
        self.content_width = self.page_width - (2 * self.margin)


class InfographicService:
    """Service for generating infographics from research data"""

    def __init__(self, template: str = 'professional'):
        self.template = InfographicTemplate(template)
        self.styles = self._create_styles()

    def generate_infographic(self,
                           research_result: Dict[str, Any],
                           format: str = 'pdf',
                           include_charts: bool = True,
                           include_visualizations: bool = True,
                           generation_method: str = 'template') -> Dict[str, Any]:
        """
        Generate infographic from deep research results

        Args:
            research_result: Output from DeepResearchService
            format: 'pdf' or 'png'
            include_charts: Whether to generate summary charts
            include_visualizations: Whether to include existing visualizations
            generation_method: 'template' (default, free) or 'ai' (Gemini Nano Banana Pro, paid)

        Returns:
            Dict with 'data' (base64 encoded), 'format', 'filename'
        """

        if generation_method == 'ai':
            return self._generate_ai_infographic(research_result, format)
        elif generation_method == 'template':
            if format == 'pdf':
                return self._generate_pdf_infographic(
                    research_result,
                    include_charts,
                    include_visualizations
                )
            elif format == 'png':
                return self._generate_png_infographic(research_result)
            else:
                raise ValueError(f"Unsupported format: {format}")
        else:
            raise ValueError(f"Unsupported generation method: {generation_method}")

    def _generate_pdf_infographic(self,
                                  research_result: Dict[str, Any],
                                  include_charts: bool,
                                  include_visualizations: bool) -> Dict[str, Any]:
        """Generate professional PDF infographic"""

        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=self.template.margin,
            leftMargin=self.template.margin,
            topMargin=self.template.margin,
            bottomMargin=self.template.margin,
            title=f"Research Analysis: {research_result.get('main_question', 'Analysis')}"
        )

        # Build document content
        story = []

        # Header
        story.extend(self._create_header(research_result))
        story.append(Spacer(1, 0.3 * inch))

        # Executive Summary Section
        story.extend(self._create_executive_summary(research_result))
        story.append(Spacer(1, 0.3 * inch))

        # Key Findings Section
        story.extend(self._create_key_findings(research_result))
        story.append(Spacer(1, 0.3 * inch))

        # Data Coverage Chart
        if include_charts:
            coverage_chart = self._create_coverage_chart(research_result)
            if coverage_chart:
                story.append(coverage_chart)
                story.append(Spacer(1, 0.3 * inch))

        # Visualizations from Research
        if include_visualizations and research_result.get('visualizations'):
            story.extend(self._create_visualizations_section(research_result))
            story.append(Spacer(1, 0.3 * inch))

        # Supporting Details
        story.extend(self._create_supporting_details(research_result))
        story.append(Spacer(1, 0.3 * inch))

        # Follow-up Questions
        if research_result.get('follow_up_questions'):
            story.extend(self._create_follow_ups(research_result))
            story.append(Spacer(1, 0.3 * inch))

        # Footer with metadata
        story.extend(self._create_footer(research_result))

        # Build PDF
        doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)

        # Get PDF bytes and encode
        pdf_bytes = buffer.getvalue()
        buffer.close()

        encoded = base64.b64encode(pdf_bytes).decode('utf-8')

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"research_infographic_{timestamp}.pdf"

        return {
            'data': encoded,
            'format': 'pdf',
            'filename': filename,
            'size_bytes': len(pdf_bytes)
        }

    def _create_styles(self):
        """Create custom paragraph styles"""
        styles = getSampleStyleSheet()

        # Title style
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            textColor=self.template.colors['primary'],
            spaceAfter=12,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))

        # Heading style
        styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=self.template.colors['secondary'],
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

        # Subheading style
        styles.add(ParagraphStyle(
            name='CustomSubheading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=self.template.colors['text'],
            spaceAfter=6,
            fontName='Helvetica-Bold'
        ))

        # Body style
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            textColor=self.template.colors['text'],
            alignment=TA_JUSTIFY,
            spaceAfter=6
        ))

        # Bullet style
        styles.add(ParagraphStyle(
            name='CustomBullet',
            parent=styles['BodyText'],
            fontSize=10,
            textColor=self.template.colors['text'],
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=4
        ))

        return styles

    def _create_header(self, research_result: Dict[str, Any]) -> List:
        """Create document header"""
        elements = []

        # Title
        title = Paragraph(
            "Deep Research Analysis",
            self.styles['CustomTitle']
        )
        elements.append(title)

        # Main question
        question = Paragraph(
            f"<b>Question:</b> {research_result.get('main_question', 'N/A')}",
            self.styles['CustomBody']
        )
        elements.append(question)

        # Metadata table
        metadata = [
            ['Generated:', datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')],
            ['Sub-questions Analyzed:', str(research_result.get('sub_questions_count', 0))],
            ['Execution Time:', f"{research_result.get('execution_time_seconds', 0):.2f} seconds"],
            ['Stages Completed:', str(len(research_result.get('stages_completed', [])))]
        ]

        metadata_table = Table(metadata, colWidths=[2*inch, 3*inch])
        metadata_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.template.colors['text']),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(metadata_table)

        # Divider
        elements.append(self._create_divider())

        return elements

    def _create_executive_summary(self, research_result: Dict[str, Any]) -> List:
        """Create executive summary section"""
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles['CustomHeading']))

        direct_answer = research_result.get('direct_answer', 'No summary available')

        # Highlight box for direct answer
        answer_para = Paragraph(direct_answer, self.styles['CustomBody'])

        answer_table = Table([[answer_para]], colWidths=[self.template.content_width])
        answer_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.template.colors['background']),
            ('BOX', (0, 0), (-1, -1), 2, self.template.colors['secondary']),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))

        elements.append(answer_table)

        return elements

    def _create_key_findings(self, research_result: Dict[str, Any]) -> List:
        """Create key findings section with bullets"""
        elements = []

        elements.append(Paragraph("Key Findings", self.styles['CustomHeading']))

        findings = research_result.get('key_findings', [])

        if not findings:
            elements.append(Paragraph("No key findings available", self.styles['CustomBody']))
            return elements

        # Create findings table with bullets
        findings_data = []
        for i, finding in enumerate(findings, 1):
            bullet = f"<bullet>\u2022</bullet>"
            finding_para = Paragraph(f"{bullet} {finding}", self.styles['CustomBullet'])
            findings_data.append([finding_para])

        findings_table = Table(findings_data, colWidths=[self.template.content_width])
        findings_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        elements.append(findings_table)

        return elements

    def _create_coverage_chart(self, research_result: Dict[str, Any]) -> Optional[Drawing]:
        """Create data coverage visualization using reportlab charts"""

        coverage = research_result.get('data_coverage', {})

        questions_answered = coverage.get('questions_answered', 0)
        total_questions = coverage.get('total_questions', 0)

        if total_questions == 0:
            return None

        # Create pie chart
        drawing = Drawing(400, 200)

        pie = Pie()
        pie.x = 150
        pie.y = 50
        pie.width = 120
        pie.height = 120

        answered = questions_answered
        unanswered = total_questions - questions_answered

        pie.data = [answered, unanswered]
        pie.labels = [f'Answered: {answered}', f'Unanswered: {unanswered}']
        pie.slices[0].fillColor = self.template.colors['success']
        pie.slices[1].fillColor = self.template.colors['light_gray']

        drawing.add(pie)

        # Add title
        title = String(200, 180, 'Data Coverage', textAnchor='middle', fontSize=12,
                      fillColor=self.template.colors['text'])
        drawing.add(title)

        return drawing

    def _create_visualizations_section(self, research_result: Dict[str, Any]) -> List:
        """Include visualizations from research results"""
        elements = []

        elements.append(Paragraph("Visualizations", self.styles['CustomHeading']))

        visualizations = research_result.get('visualizations', [])

        for viz in visualizations[:5]:  # Limit to 5 visualizations
            try:
                # Decode base64 image
                img_data = base64.b64decode(viz.get('data', ''))
                img_buffer = io.BytesIO(img_data)

                # Add to PDF
                img = Image(img_buffer, width=5*inch, height=3*inch)
                elements.append(img)

                # Add caption
                caption = Paragraph(
                    f"<i>{viz.get('caption', 'Visualization')}</i>",
                    self.styles['CustomBody']
                )
                elements.append(caption)
                elements.append(Spacer(1, 0.2*inch))

            except Exception as e:
                print(f"Error adding visualization: {e}")
                continue

        return elements

    def _create_supporting_details(self, research_result: Dict[str, Any]) -> List:
        """Create supporting details section"""
        elements = []

        elements.append(Paragraph("Supporting Analysis", self.styles['CustomHeading']))

        details = research_result.get('supporting_details', {})

        if isinstance(details, list):
            for detail in details[:10]:  # Limit to 10 details
                if detail.get('success'):
                    question = detail.get('question', 'N/A')
                    method = detail.get('method', 'N/A')

                    detail_text = f"<b>{question}</b><br/><i>Method: {method}</i>"
                    elements.append(Paragraph(detail_text, self.styles['CustomBody']))
                    elements.append(Spacer(1, 0.1*inch))

        return elements

    def _create_follow_ups(self, research_result: Dict[str, Any]) -> List:
        """Create follow-up questions section"""
        elements = []

        elements.append(Paragraph("Recommended Next Steps", self.styles['CustomHeading']))

        follow_ups = research_result.get('follow_up_questions', [])

        for i, question in enumerate(follow_ups, 1):
            bullet = f"<bullet>{i}.</bullet>"
            q_para = Paragraph(f"{bullet} {question}", self.styles['CustomBullet'])
            elements.append(q_para)

        return elements

    def _create_footer(self, research_result: Dict[str, Any]) -> List:
        """Create document footer with metadata"""
        elements = []

        elements.append(Spacer(1, 0.5*inch))
        elements.append(self._create_divider())

        footer_text = (
            f"Generated by AI Analytics Platform | "
            f"Research ID: {research_result.get('research_id', 'N/A')} | "
            f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )

        footer = Paragraph(
            f"<font size=8 color='gray'>{footer_text}</font>",
            self.styles['CustomBody']
        )
        elements.append(footer)

        return elements

    def _create_divider(self) -> Table:
        """Create horizontal divider line"""
        divider = Table([['_' * 100]], colWidths=[self.template.content_width])
        divider.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, -1), 1, self.template.colors['light_gray']),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        return divider

    def _add_page_number(self, canvas_obj, doc):
        """Add page numbers to each page"""
        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.setFillColor(colors.gray)
        canvas_obj.drawRightString(
            doc.pagesize[0] - self.template.margin,
            self.template.margin / 2,
            text
        )

    def _generate_png_infographic(self, research_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate single-page PNG infographic"""

        # Create figure
        fig = Figure(figsize=(11, 8.5), dpi=150)
        fig.patch.set_facecolor('white')

        # Create matplotlib-based infographic
        # This is a simplified version - you can enhance with more visuals

        ax = fig.add_subplot(111)
        ax.axis('off')

        # Convert reportlab colors to matplotlib hex colors
        primary_color = '#2C3E50'
        secondary_color = '#3498DB'

        # Title
        fig.text(0.5, 0.95, 'Deep Research Analysis',
                ha='center', fontsize=20, fontweight='bold',
                color=primary_color)

        # Question
        question = research_result.get('main_question', 'N/A')
        fig.text(0.5, 0.90, f"Question: {question}",
                ha='center', fontsize=12, style='italic', wrap=True)

        # Direct Answer
        answer = research_result.get('direct_answer', 'No answer available')
        fig.text(0.1, 0.80, answer, fontsize=11, wrap=True,
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

        # Key Findings
        findings = research_result.get('key_findings', [])
        y_pos = 0.65
        fig.text(0.1, y_pos, 'Key Findings:', fontsize=14, fontweight='bold')
        y_pos -= 0.05

        for finding in findings[:5]:
            fig.text(0.12, y_pos, f"• {finding}", fontsize=10)
            y_pos -= 0.04

        # Save to buffer
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
        buffer.seek(0)

        # Encode
        png_bytes = buffer.getvalue()
        buffer.close()

        encoded = base64.b64encode(png_bytes).decode('utf-8')

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"research_infographic_{timestamp}.png"

        return {
            'data': encoded,
            'format': 'png',
            'filename': filename,
            'size_bytes': len(png_bytes)
        }

    def _generate_ai_infographic(self, research_result: Dict[str, Any], format: str) -> Dict[str, Any]:
        """
        Generate AI-powered infographic using Gemini Nano Banana Pro via OpenRouter

        This method creates professional infographic images using Google's state-of-the-art
        image generation model. The model excels at creating accurate, data-rich infographics
        with proper text rendering and visual hierarchy.

        Args:
            research_result: Deep research results to visualize
            format: 'pdf' or 'png' (AI generates PNG, optionally converts to PDF)

        Returns:
            Dict with base64 encoded infographic data
        """
        import httpx

        # Get API key
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")

        # Prepare research summary for prompt
        main_question = research_result.get('main_question', 'Research Analysis')
        direct_answer = research_result.get('direct_answer', '')
        key_findings = research_result.get('key_findings', [])
        supporting_details = research_result.get('supporting_details', [])

        # Build detailed prompt for infographic generation
        findings_text = "\n".join([f"• {f}" for f in key_findings[:8]])  # Top 8 findings

        prompt = f"""Create a professional, elegant infographic summarizing this research analysis.

RESEARCH QUESTION: {main_question}

KEY ANSWER: {direct_answer}

KEY FINDINGS:
{findings_text}

DESIGN REQUIREMENTS:
- Clean, modern, professional layout
- Use data visualization (charts, icons, diagrams) where appropriate
- Include clear section headers
- Use a cohesive color scheme (blues, grays, or corporate colors)
- Make text legible and well-organized
- Include summary statistics or metrics if applicable
- 2-page infographic layout that elegantly presents all information
- Emphasize the most important insights visually

The infographic should be suitable for business/enterprise presentations."""

        # Call OpenRouter API with Gemini Nano Banana Pro
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/felix",
            "X-Title": "Felix AI Analytics Platform"
        }

        payload = {
            "model": "google/gemini-3-pro-image-preview",
            "prompt": prompt,
            "max_tokens": 1024,
            "temperature": 0.7,
            "aspect_ratio": "portrait",  # Good for infographics
            "num_images": 1
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    "https://openrouter.ai/api/v1/images/generate",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

            # Extract image data
            if 'data' in result and len(result['data']) > 0:
                image_data = result['data'][0]

                # Handle different response formats
                if 'b64_json' in image_data:
                    image_base64 = image_data['b64_json']
                elif 'url' in image_data:
                    # Download from URL
                    with httpx.Client() as client:
                        img_response = client.get(image_data['url'])
                        img_response.raise_for_status()
                        image_base64 = base64.b64encode(img_response.content).decode('utf-8')
                else:
                    raise ValueError("No image data found in API response")

                # If PDF requested, convert PNG to PDF
                if format == 'pdf':
                    image_base64 = self._convert_png_to_pdf(image_base64)
                    file_format = 'pdf'
                else:
                    file_format = 'png'

                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f"research_infographic_ai_{timestamp}.{file_format}"

                # Calculate size
                size_bytes = len(base64.b64decode(image_base64))

                return {
                    'data': image_base64,
                    'format': file_format,
                    'filename': filename,
                    'size_bytes': size_bytes,
                    'generation_method': 'ai',
                    'model': 'google/gemini-3-pro-image-preview'
                }
            else:
                raise ValueError("No image generated by API")

        except httpx.HTTPError as e:
            raise Exception(f"API request failed: {str(e)}")
        except Exception as e:
            raise Exception(f"AI infographic generation failed: {str(e)}")

    def _convert_png_to_pdf(self, png_base64: str) -> str:
        """Convert PNG image to PDF format"""
        from reportlab.pdfgen import canvas
        from PIL import Image as PILImage

        # Decode PNG
        png_bytes = base64.b64decode(png_base64)
        img = PILImage.open(io.BytesIO(png_bytes))

        # Create PDF
        buffer = io.BytesIO()

        # Get image dimensions
        img_width, img_height = img.size

        # Calculate PDF page size to fit image (maintain aspect ratio)
        max_width = 8.5 * inch  # Letter width
        max_height = 11 * inch  # Letter height

        scale = min(max_width / img_width, max_height / img_height)
        pdf_width = img_width * scale
        pdf_height = img_height * scale

        # Create canvas
        c = canvas.Canvas(buffer, pagesize=(pdf_width, pdf_height))

        # Save image to temp buffer
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)

        # Draw image on PDF
        c.drawImage(
            ImageReader(img_buffer),
            0, 0,
            width=pdf_width,
            height=pdf_height
        )

        c.save()
        buffer.seek(0)

        # Encode to base64
        pdf_bytes = buffer.getvalue()
        return base64.b64encode(pdf_bytes).decode('utf-8')
