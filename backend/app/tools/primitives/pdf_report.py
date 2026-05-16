"""
PDF Report Tool - generates professional PDF analytical reports
"""
import io
import base64
from typing import Dict, Any, List
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage

from app.tools.base_tool import BaseTool
from app.schemas.tool import (
    ToolSchema,
    ToolParameter,
    ToolParameterType,
    ToolResult,
    ToolCapability
)


class PDFReportTool(BaseTool):
    """
    PDF report generation tool

    Creates professional PDF analytical reports with:
    - Multi-page layouts
    - Embedded visualizations
    - Data tables
    - Executive summaries
    - Professional styling
    """

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name="pdf_report",
            description="Generate professional PDF analytical reports",
            category="export",
            parameters=[
                ToolParameter(
                    name="title",
                    type=ToolParameterType.STRING,
                    description="Report title",
                    required=True
                ),
                ToolParameter(
                    name="summary",
                    type=ToolParameterType.STRING,
                    description="Executive summary",
                    required=False
                ),
                ToolParameter(
                    name="sections",
                    type=ToolParameterType.ARRAY,
                    description="Report sections with content",
                    required=True
                ),
                ToolParameter(
                    name="visualizations",
                    type=ToolParameterType.ARRAY,
                    description="Base64 encoded images to embed",
                    required=False
                ),
                ToolParameter(
                    name="tables",
                    type=ToolParameterType.ARRAY,
                    description="Data tables to include",
                    required=False
                ),
                ToolParameter(
                    name="insights",
                    type=ToolParameterType.ARRAY,
                    description="Key insights/findings",
                    required=False
                ),
                ToolParameter(
                    name="metadata",
                    type=ToolParameterType.OBJECT,
                    description="Report metadata",
                    required=False
                ),
                ToolParameter(
                    name="theme",
                    type=ToolParameterType.STRING,
                    description="Report theme",
                    required=False,
                    enum=["professional", "modern", "corporate"],
                    default="professional"
                ),
                ToolParameter(
                    name="page_size",
                    type=ToolParameterType.STRING,
                    description="Page size",
                    required=False,
                    enum=["letter", "a4"],
                    default="letter"
                )
            ],
            returns={
                "type": "object",
                "properties": {
                    "pdf": {"type": "string", "description": "Base64 encoded PDF"},
                    "filename": {"type": "string"},
                    "size_bytes": {"type": "number"}
                }
            },
            examples=[
                {
                    "parameters": {
                        "title": "Q4 Sales Analysis",
                        "summary": "Comprehensive analysis of sales data",
                        "sections": [{"heading": "Overview", "content": "..."}]
                    }
                }
            ],
            requires_approval=False,
            is_destructive=False,
            estimated_duration_ms=1000
        )

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="PDF Report Generation",
            description="Create professional PDF analytical reports",
            use_cases=[
                "Generate executive reports for stakeholders",
                "Create printable analysis documentation",
                "Export findings in portable format",
                "Build multi-page analytical reports",
                "Share analysis results offline"
            ],
            limitations=[
                "Static PDF (not editable)",
                "File size increases with images",
                "Complex layouts may take time"
            ]
        )

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute PDF report generation"""
        title = parameters["title"]
        sections = parameters["sections"]
        theme = parameters.get("theme", "professional")
        page_size = letter if parameters.get("page_size", "letter") == "letter" else A4

        try:
            # Generate PDF
            pdf_bytes = self._generate_pdf(
                title=title,
                summary=parameters.get("summary", ""),
                sections=sections,
                visualizations=parameters.get("visualizations", []),
                tables=parameters.get("tables", []),
                insights=parameters.get("insights", []),
                metadata=parameters.get("metadata", {}),
                theme=theme,
                page_size=page_size
            )

            # Encode to base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

            # Generate filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"report_{timestamp}.pdf"

            return ToolResult(
                tool_name="pdf_report",
                success=True,
                data={
                    "pdf": pdf_base64,
                    "filename": filename,
                    "size_bytes": len(pdf_bytes),
                    "theme": theme
                },
                metadata={
                    "num_sections": len(sections),
                    "num_visualizations": len(parameters.get("visualizations", [])),
                    "num_tables": len(parameters.get("tables", []))
                }
            )

        except Exception as e:
            return ToolResult(
                tool_name="pdf_report",
                success=False,
                data={},
                error=f"PDF report generation failed: {str(e)}"
            )

    def _generate_pdf(
        self,
        title: str,
        summary: str,
        sections: List[Dict[str, Any]],
        visualizations: List[Dict[str, Any]],
        tables: List[Dict[str, Any]],
        insights: List[str],
        metadata: Dict[str, Any],
        theme: str,
        page_size: tuple
    ) -> bytes:
        """Generate PDF document"""

        # Create buffer
        buffer = io.BytesIO()

        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            title=title
        )

        # Get theme colors
        colors_dict = self._get_theme_colors(theme)

        # Create styles
        styles = self._create_styles(colors_dict)

        # Build story
        story = []

        # Title page
        story.extend(self._create_title_page(title, metadata, styles))
        story.append(PageBreak())

        # Executive summary
        if summary:
            story.extend(self._create_summary(summary, styles))
            story.append(Spacer(1, 0.3*inch))

        # Key insights
        if insights:
            story.extend(self._create_insights(insights, styles, colors_dict))
            story.append(Spacer(1, 0.3*inch))

        # Sections
        for idx, section in enumerate(sections):
            story.extend(self._create_section(section, styles, colors_dict))

            # Add page break between major sections (except last)
            if idx < len(sections) - 1:
                story.append(PageBreak())

        # Additional visualizations
        if visualizations:
            story.append(PageBreak())
            story.append(Paragraph("Visualizations", styles['Heading1']))
            story.append(Spacer(1, 0.2*inch))
            for viz in visualizations:
                story.extend(self._create_visualization(viz, styles))

        # Additional tables
        if tables:
            story.append(PageBreak())
            story.append(Paragraph("Data Tables", styles['Heading1']))
            story.append(Spacer(1, 0.2*inch))
            for table in tables:
                story.extend(self._create_table(table, styles, colors_dict))

        # Footer
        story.append(Spacer(1, 0.5*inch))
        story.extend(self._create_footer(metadata, styles))

        # Build PDF
        doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)

        # Get bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def _create_styles(self, colors_dict: Dict[str, Any]) -> Dict[str, ParagraphStyle]:
        """Create paragraph styles"""
        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=28,
            textColor=colors_dict['primary'],
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        styles.add(ParagraphStyle(
            name='Heading1',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors_dict['primary'],
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

        styles.add(ParagraphStyle(
            name='Heading2',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors_dict['secondary'],
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))

        styles.add(ParagraphStyle(
            name='Body',
            parent=styles['BodyText'],
            fontSize=11,
            textColor=colors_dict['text'],
            alignment=TA_JUSTIFY,
            spaceAfter=10,
            leading=16
        ))

        styles.add(ParagraphStyle(
            name='Bullet',
            parent=styles['BodyText'],
            fontSize=10,
            textColor=colors_dict['text'],
            leftIndent=25,
            bulletIndent=10,
            spaceAfter=6
        ))

        styles.add(ParagraphStyle(
            name='Caption',
            parent=styles['BodyText'],
            fontSize=9,
            textColor=colors_dict['text_light'],
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica-Oblique'
        ))

        return styles

    def _create_title_page(self, title: str, metadata: Dict[str, Any], styles):
        """Create title page"""
        elements = []

        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph(title, styles['CustomTitle']))
        elements.append(Spacer(1, 0.5*inch))

        if metadata.get('subtitle'):
            elements.append(Paragraph(metadata['subtitle'], styles['Heading2']))
            elements.append(Spacer(1, 0.5*inch))

        # Metadata table
        meta_data = []
        if metadata.get('author'):
            meta_data.append(['Author:', metadata['author']])
        meta_data.append(['Generated:', datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')])
        if metadata.get('dataset'):
            meta_data.append(['Dataset:', metadata['dataset']])
        if metadata.get('rows'):
            meta_data.append(['Data Points:', f"{metadata['rows']:,}"])

        if meta_data:
            meta_table = Table(meta_data, colWidths=[2*inch, 3*inch])
            meta_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(meta_table)

        return elements

    def _create_summary(self, summary: str, styles):
        """Create executive summary"""
        elements = []

        elements.append(Paragraph("Executive Summary", styles['Heading1']))
        elements.append(Spacer(1, 0.1*inch))

        summary_para = Paragraph(summary, styles['Body'])
        summary_table = Table([[summary_para]], colWidths=[6.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EBF5FB')),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#3498DB')),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))

        elements.append(summary_table)

        return elements

    def _create_insights(self, insights: List[str], styles, colors_dict):
        """Create key insights section"""
        elements = []

        elements.append(Paragraph("Key Insights", styles['Heading1']))
        elements.append(Spacer(1, 0.1*inch))

        insights_data = []
        for insight in insights:
            bullet = "<bullet>\u2022</bullet>"
            insight_para = Paragraph(f"{bullet} {insight}", styles['Bullet'])
            insights_data.append([insight_para])

        insights_table = Table(insights_data, colWidths=[6.5*inch])
        insights_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E8F5E9')),
            ('BOX', (0, 0), (-1, -1), 2, colors_dict['success']),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        elements.append(insights_table)

        return elements

    def _create_section(self, section: Dict[str, Any], styles, colors_dict):
        """Create content section"""
        elements = []

        elements.append(Paragraph(section['heading'], styles['Heading1']))
        elements.append(Spacer(1, 0.15*inch))

        if section.get('subheading'):
            elements.append(Paragraph(section['subheading'], styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))

        if section.get('content'):
            elements.append(Paragraph(section['content'], styles['Body']))
            elements.append(Spacer(1, 0.2*inch))

        # Section visualizations
        if section.get('visualizations'):
            for viz in section['visualizations']:
                elements.extend(self._create_visualization(viz, styles))

        # Section tables
        if section.get('tables'):
            for table in section['tables']:
                elements.extend(self._create_table(table, styles, colors_dict))

        return elements

    def _create_visualization(self, viz: Dict[str, Any], styles):
        """Create visualization element"""
        elements = []

        try:
            # Decode base64 image
            img_data = base64.b64decode(viz.get('image', ''))
            img_buffer = io.BytesIO(img_data)

            # Create image
            img = Image(img_buffer, width=6*inch, height=4*inch)
            elements.append(img)

            # Add caption
            if viz.get('caption'):
                elements.append(Spacer(1, 0.1*inch))
                elements.append(Paragraph(viz['caption'], styles['Caption']))

            elements.append(Spacer(1, 0.3*inch))

        except Exception as e:
            # Skip if image can't be loaded
            pass

        return elements

    def _create_table(self, table: Dict[str, Any], styles, colors_dict):
        """Create data table"""
        elements = []

        if table.get('title'):
            elements.append(Paragraph(table['title'], styles['Heading2']))
            elements.append(Spacer(1, 0.1*inch))

        # Build table data
        table_data = []
        if table.get('headers'):
            table_data.append(table['headers'])

        if table.get('rows'):
            table_data.extend(table['rows'][:50])  # Limit to 50 rows

        if table_data:
            # Calculate column widths
            num_cols = len(table_data[0])
            col_width = 6.5 * inch / num_cols

            data_table = Table(table_data, colWidths=[col_width] * num_cols)
            data_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors_dict['primary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ]))

            elements.append(data_table)
            elements.append(Spacer(1, 0.3*inch))

        return elements

    def _create_footer(self, metadata: Dict[str, Any], styles):
        """Create footer"""
        elements = []

        divider = Table([['_' * 100]], colWidths=[6.5*inch])
        divider.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(divider)

        footer_text = (
            f"Generated by AI Analytics Platform | "
            f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )

        if metadata.get('footer_note'):
            footer_text += f" | {metadata['footer_note']}"

        footer = Paragraph(
            f"<font size=8 color='gray'>{footer_text}</font>",
            styles['Body']
        )
        elements.append(footer)

        return elements

    def _add_page_number(self, canvas_obj, doc):
        """Add page numbers"""
        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.setFillColor(colors.gray)
        canvas_obj.drawRightString(
            doc.pagesize[0] - 0.75*inch,
            0.5*inch,
            text
        )

    def _get_theme_colors(self, theme: str) -> Dict[str, Any]:
        """Get theme colors"""
        themes = {
            "professional": {
                "primary": colors.HexColor('#2C3E50'),
                "secondary": colors.HexColor('#3498DB'),
                "accent": colors.HexColor('#E74C3C'),
                "success": colors.HexColor('#27AE60'),
                "text": colors.HexColor('#2C3E50'),
                "text_light": colors.HexColor('#7F8C8D')
            },
            "modern": {
                "primary": colors.HexColor('#1A1A2E'),
                "secondary": colors.HexColor('#16213E'),
                "accent": colors.HexColor('#E94560'),
                "success": colors.HexColor('#0F3460'),
                "text": colors.HexColor('#1A1A2E'),
                "text_light": colors.HexColor('#616161')
            },
            "corporate": {
                "primary": colors.HexColor('#003366'),
                "secondary": colors.HexColor('#0066CC'),
                "accent": colors.HexColor('#FF6B35'),
                "success": colors.HexColor('#4CAF50'),
                "text": colors.HexColor('#212529'),
                "text_light": colors.HexColor('#6C757D')
            }
        }

        return themes.get(theme, themes["professional"])
