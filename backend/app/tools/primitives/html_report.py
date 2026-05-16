"""
HTML Report Tool - generates rich analytical HTML reports
"""
import io
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime
from jinja2 import Template
from app.tools.base_tool import BaseTool
from app.schemas.tool import (
    ToolSchema,
    ToolParameter,
    ToolParameterType,
    ToolResult,
    ToolCapability
)


class HTMLReportTool(BaseTool):
    """
    HTML report generation tool

    Creates professional, responsive HTML reports with:
    - Executive summaries
    - Embedded visualizations
    - Data tables
    - Statistical insights
    - Custom branding
    """

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name="html_report",
            description="Generate professional HTML analytical reports",
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
                    description="Report metadata (author, date, etc.)",
                    required=False
                ),
                ToolParameter(
                    name="theme",
                    type=ToolParameterType.STRING,
                    description="Report theme/style",
                    required=False,
                    enum=["professional", "modern", "minimal", "corporate"],
                    default="professional"
                )
            ],
            returns={
                "type": "object",
                "properties": {
                    "html": {"type": "string"},
                    "filename": {"type": "string"},
                    "size_bytes": {"type": "number"}
                }
            },
            examples=[
                {
                    "parameters": {
                        "title": "Sales Analysis Report",
                        "summary": "Comprehensive analysis of Q4 sales data",
                        "sections": [
                            {"heading": "Overview", "content": "..."},
                            {"heading": "Findings", "content": "..."}
                        ]
                    }
                }
            ],
            requires_approval=False,
            is_destructive=False,
            estimated_duration_ms=500
        )

    def get_capability(self) -> ToolCapability:
        return ToolCapability(
            name="HTML Report Generation",
            description="Create professional, shareable HTML analytical reports",
            use_cases=[
                "Generate executive summaries with visualizations",
                "Create comprehensive data analysis reports",
                "Build interactive HTML dashboards",
                "Export findings in web-viewable format",
                "Share analysis results with stakeholders"
            ],
            limitations=[
                "Static HTML (not dynamically updating)",
                "Requires browser to view",
                "Large reports may be slow to load"
            ]
        )

    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """Execute HTML report generation"""
        title = parameters["title"]
        sections = parameters["sections"]
        theme = parameters.get("theme", "professional")

        try:
            # Build HTML content
            html_content = self._generate_html(
                title=title,
                summary=parameters.get("summary", ""),
                sections=sections,
                visualizations=parameters.get("visualizations", []),
                tables=parameters.get("tables", []),
                insights=parameters.get("insights", []),
                metadata=parameters.get("metadata", {}),
                theme=theme
            )

            # Generate filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"report_{timestamp}.html"

            # Calculate size
            size_bytes = len(html_content.encode('utf-8'))

            return ToolResult(
                tool_name="html_report",
                success=True,
                data={
                    "html": html_content,
                    "filename": filename,
                    "size_bytes": size_bytes,
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
                tool_name="html_report",
                success=False,
                data={},
                error=f"HTML report generation failed: {str(e)}"
            )

    def _generate_html(
        self,
        title: str,
        summary: str,
        sections: List[Dict[str, Any]],
        visualizations: List[Dict[str, Any]],
        tables: List[Dict[str, Any]],
        insights: List[str],
        metadata: Dict[str, Any],
        theme: str
    ) -> str:
        """Generate complete HTML document"""

        # Get theme colors
        theme_colors = self._get_theme_colors(theme)

        # Build HTML template
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: {{ colors.text }};
            background: {{ colors.background }};
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }

        .header {
            background: {{ colors.primary }};
            color: white;
            padding: 40px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }

        .header .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }

        .metadata {
            background: {{ colors.secondary_light }};
            padding: 15px 40px;
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 20px;
            border-bottom: 1px solid {{ colors.border }};
        }

        .metadata-item {
            display: flex;
            flex-direction: column;
        }

        .metadata-label {
            font-size: 0.85rem;
            color: {{ colors.text_light }};
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .metadata-value {
            font-size: 1rem;
            font-weight: 600;
            color: {{ colors.text }};
        }

        .content {
            padding: 40px;
        }

        .summary-box {
            background: {{ colors.accent_light }};
            border-left: 4px solid {{ colors.accent }};
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 4px;
        }

        .summary-box h2 {
            color: {{ colors.primary }};
            margin-bottom: 15px;
            font-size: 1.5rem;
        }

        .summary-box p {
            font-size: 1.05rem;
            line-height: 1.7;
        }

        .insights {
            background: {{ colors.success_light }};
            border-left: 4px solid {{ colors.success }};
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 4px;
        }

        .insights h3 {
            color: {{ colors.success }};
            margin-bottom: 15px;
            font-size: 1.3rem;
        }

        .insights ul {
            list-style: none;
            padding: 0;
        }

        .insights li {
            padding: 8px 0;
            padding-left: 25px;
            position: relative;
        }

        .insights li:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: {{ colors.success }};
            font-weight: bold;
        }

        .section {
            margin-bottom: 40px;
        }

        .section h2 {
            color: {{ colors.primary }};
            font-size: 1.8rem;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid {{ colors.primary }};
        }

        .section h3 {
            color: {{ colors.secondary }};
            font-size: 1.4rem;
            margin-top: 25px;
            margin-bottom: 15px;
        }

        .section p {
            margin-bottom: 15px;
            text-align: justify;
        }

        .visualization {
            margin: 30px 0;
            text-align: center;
        }

        .visualization img {
            max-width: 100%;
            height: auto;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .visualization-caption {
            margin-top: 10px;
            font-style: italic;
            color: {{ colors.text_light }};
            font-size: 0.95rem;
        }

        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            overflow-x: auto;
            display: block;
        }

        .data-table table {
            width: 100%;
            border-collapse: collapse;
        }

        .data-table th {
            background: {{ colors.primary }};
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }

        .data-table td {
            padding: 10px 12px;
            border-bottom: 1px solid {{ colors.border }};
        }

        .data-table tr:hover {
            background: {{ colors.secondary_light }};
        }

        .data-table tr:nth-child(even) {
            background: #f9f9f9;
        }

        .footer {
            background: {{ colors.secondary_light }};
            padding: 20px 40px;
            text-align: center;
            color: {{ colors.text_light }};
            font-size: 0.9rem;
            border-top: 1px solid {{ colors.border }};
        }

        @media print {
            body {
                padding: 0;
            }
            .container {
                box-shadow: none;
                border-radius: 0;
            }
            .visualization img {
                max-width: 100%;
                page-break-inside: avoid;
            }
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8rem;
            }
            .content {
                padding: 20px;
            }
            .metadata {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>{{ title }}</h1>
            {% if metadata.subtitle %}
            <div class="subtitle">{{ metadata.subtitle }}</div>
            {% endif %}
        </div>

        <!-- Metadata -->
        <div class="metadata">
            <div class="metadata-item">
                <span class="metadata-label">Generated</span>
                <span class="metadata-value">{{ metadata.generated_at or current_date }}</span>
            </div>
            {% if metadata.author %}
            <div class="metadata-item">
                <span class="metadata-label">Author</span>
                <span class="metadata-value">{{ metadata.author }}</span>
            </div>
            {% endif %}
            {% if metadata.dataset %}
            <div class="metadata-item">
                <span class="metadata-label">Dataset</span>
                <span class="metadata-value">{{ metadata.dataset }}</span>
            </div>
            {% endif %}
            {% if metadata.rows %}
            <div class="metadata-item">
                <span class="metadata-label">Data Points</span>
                <span class="metadata-value">{{ metadata.rows | number_format }}</span>
            </div>
            {% endif %}
        </div>

        <!-- Content -->
        <div class="content">
            <!-- Summary -->
            {% if summary %}
            <div class="summary-box">
                <h2>Executive Summary</h2>
                <p>{{ summary }}</p>
            </div>
            {% endif %}

            <!-- Key Insights -->
            {% if insights %}
            <div class="insights">
                <h3>Key Insights</h3>
                <ul>
                    {% for insight in insights %}
                    <li>{{ insight }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}

            <!-- Sections -->
            {% for section in sections %}
            <div class="section">
                <h2>{{ section.heading }}</h2>
                {% if section.subheading %}
                <h3>{{ section.subheading }}</h3>
                {% endif %}
                <p>{{ section.content }}</p>

                <!-- Section visualizations -->
                {% if section.visualizations %}
                {% for viz in section.visualizations %}
                <div class="visualization">
                    <img src="data:image/png;base64,{{ viz.image }}" alt="{{ viz.caption or 'Visualization' }}">
                    {% if viz.caption %}
                    <div class="visualization-caption">{{ viz.caption }}</div>
                    {% endif %}
                </div>
                {% endfor %}
                {% endif %}

                <!-- Section tables -->
                {% if section.tables %}
                {% for table in section.tables %}
                <div class="data-table">
                    <table>
                        <thead>
                            <tr>
                                {% for header in table.headers %}
                                <th>{{ header }}</th>
                                {% endfor %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in table.rows %}
                            <tr>
                                {% for cell in row %}
                                <td>{{ cell }}</td>
                                {% endfor %}
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endfor %}
                {% endif %}
            </div>
            {% endfor %}

            <!-- Additional visualizations -->
            {% if visualizations %}
            <div class="section">
                <h2>Visualizations</h2>
                {% for viz in visualizations %}
                <div class="visualization">
                    <img src="data:image/png;base64,{{ viz.image }}" alt="{{ viz.caption or 'Visualization' }}">
                    {% if viz.caption %}
                    <div class="visualization-caption">{{ viz.caption }}</div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <!-- Additional tables -->
            {% if tables %}
            <div class="section">
                <h2>Data Tables</h2>
                {% for table in tables %}
                <div class="data-table">
                    {% if table.title %}
                    <h3>{{ table.title }}</h3>
                    {% endif %}
                    <table>
                        <thead>
                            <tr>
                                {% for header in table.headers %}
                                <th>{{ header }}</th>
                                {% endfor %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in table.rows %}
                            <tr>
                                {% for cell in row %}
                                <td>{{ cell }}</td>
                                {% endfor %}
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endfor %}
            </div>
            {% endif %}
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>Generated by AI Analytics Platform | {{ current_date }}</p>
            {% if metadata.footer_note %}
            <p>{{ metadata.footer_note }}</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

        # Prepare template context
        context = {
            "title": title,
            "summary": summary,
            "sections": sections,
            "visualizations": visualizations,
            "tables": tables,
            "insights": insights,
            "metadata": metadata,
            "colors": theme_colors,
            "current_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "number_format": lambda x: f"{x:,}"
        }

        # Render template
        template = Template(template_str)
        html = template.render(**context)

        return html

    def _get_theme_colors(self, theme: str) -> Dict[str, str]:
        """Get color scheme for theme"""
        themes = {
            "professional": {
                "primary": "#2C3E50",
                "secondary": "#3498DB",
                "secondary_light": "#EBF5FB",
                "accent": "#E74C3C",
                "accent_light": "#FADBD8",
                "success": "#27AE60",
                "success_light": "#D5F4E6",
                "background": "#ECF0F1",
                "text": "#2C3E50",
                "text_light": "#7F8C8D",
                "border": "#BDC3C7"
            },
            "modern": {
                "primary": "#1A1A2E",
                "secondary": "#16213E",
                "secondary_light": "#F0F3F4",
                "accent": "#E94560",
                "accent_light": "#FCE4EC",
                "success": "#0F3460",
                "success_light": "#E8EAF6",
                "background": "#F5F5F5",
                "text": "#1A1A2E",
                "text_light": "#616161",
                "border": "#D1D5DB"
            },
            "minimal": {
                "primary": "#000000",
                "secondary": "#333333",
                "secondary_light": "#F8F9FA",
                "accent": "#666666",
                "accent_light": "#F5F5F5",
                "success": "#000000",
                "success_light": "#F0F0F0",
                "background": "#FFFFFF",
                "text": "#000000",
                "text_light": "#666666",
                "border": "#E0E0E0"
            },
            "corporate": {
                "primary": "#003366",
                "secondary": "#0066CC",
                "secondary_light": "#E3F2FD",
                "accent": "#FF6B35",
                "accent_light": "#FFE5D9",
                "success": "#4CAF50",
                "success_light": "#E8F5E9",
                "background": "#F8F9FA",
                "text": "#212529",
                "text_light": "#6C757D",
                "border": "#CED4DA"
            }
        }

        return themes.get(theme, themes["professional"])
