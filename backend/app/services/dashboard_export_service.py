"""
Dashboard Export Service

Handles PDF generation from dashboard images using ReportLab.
"""
import io
import base64
from datetime import datetime
from typing import Optional
import logging

from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

logger = logging.getLogger(__name__)


class DashboardExportService:
    """Service for exporting dashboards to various formats."""

    def __init__(self):
        self.default_page_size = letter
        self.margin = 0.5 * inch

    def generate_pdf_from_image(
        self,
        image_data: str,
        filename: str,
        width: int,
        height: int,
        title: Optional[str] = None,
        include_metadata: bool = True
    ) -> bytes:
        """
        Generate a PDF document from a base64-encoded image.

        Args:
            image_data: Base64 encoded PNG image (data URL format)
            filename: Name for the PDF (without extension)
            width: Original image width in pixels
            height: Original image height in pixels
            title: Optional title to add to the PDF header
            include_metadata: Whether to include generation timestamp

        Returns:
            PDF file as bytes
        """
        try:
            # Decode base64 image
            if image_data.startswith('data:image'):
                # Remove data URL prefix
                image_data = image_data.split(',')[1]

            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

            # Calculate page orientation based on image aspect ratio
            aspect_ratio = width / height
            if aspect_ratio > 1.2:
                # Landscape for wide images
                page_size = landscape(self.default_page_size)
            else:
                # Portrait for tall or square images
                page_size = self.default_page_size

            page_width, page_height = page_size

            # Calculate available space for image
            available_width = page_width - (2 * self.margin)
            available_height = page_height - (2 * self.margin)

            # Reserve space for header/footer if needed
            header_height = 0
            footer_height = 0

            if title:
                header_height = 0.5 * inch
                available_height -= header_height

            if include_metadata:
                footer_height = 0.4 * inch
                available_height -= footer_height

            # Calculate image dimensions to fit page while maintaining aspect ratio
            scale_x = available_width / width
            scale_y = available_height / height
            scale = min(scale_x, scale_y)

            img_width = width * scale
            img_height = height * scale

            # Center the image horizontally
            x_offset = self.margin + (available_width - img_width) / 2
            y_offset = self.margin + footer_height

            # Create PDF
            pdf_buffer = io.BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=page_size)

            # Add title if provided
            if title:
                c.setFont("Helvetica-Bold", 16)
                title_y = page_height - self.margin - 0.3 * inch
                c.drawString(self.margin, title_y, title)

            # Draw the image
            img_reader = ImageReader(image)
            c.drawImage(
                img_reader,
                x_offset,
                y_offset,
                width=img_width,
                height=img_height,
                preserveAspectRatio=True
            )

            # Add footer with metadata
            if include_metadata:
                c.setFont("Helvetica", 8)
                c.setFillColorRGB(0.5, 0.5, 0.5)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                footer_text = f"Generated on {timestamp}"
                c.drawString(self.margin, self.margin, footer_text)

                # Add page dimensions info
                dims_text = f"Original size: {width}x{height}px"
                c.drawRightString(page_width - self.margin, self.margin, dims_text)

            c.save()

            pdf_buffer.seek(0)
            return pdf_buffer.getvalue()

        except Exception as e:
            logger.error(f"PDF generation failed: {e}", exc_info=True)
            raise ValueError(f"Failed to generate PDF: {str(e)}")

    def generate_multi_page_pdf(
        self,
        images: list[tuple[str, int, int]],
        filename: str,
        title: Optional[str] = None
    ) -> bytes:
        """
        Generate a multi-page PDF from multiple images.

        Args:
            images: List of (image_data, width, height) tuples
            filename: Name for the PDF
            title: Optional title for the first page

        Returns:
            PDF file as bytes
        """
        pdf_buffer = io.BytesIO()
        page_size = self.default_page_size
        page_width, page_height = page_size

        c = canvas.Canvas(pdf_buffer, pagesize=page_size)

        for i, (image_data, width, height) in enumerate(images):
            if i > 0:
                c.showPage()

            # Decode image
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]

            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

            # Calculate dimensions
            available_width = page_width - (2 * self.margin)
            available_height = page_height - (2 * self.margin)

            if i == 0 and title:
                available_height -= 0.5 * inch
                c.setFont("Helvetica-Bold", 16)
                c.drawString(self.margin, page_height - self.margin - 0.3 * inch, title)

            scale = min(available_width / width, available_height / height)
            img_width = width * scale
            img_height = height * scale

            x_offset = self.margin + (available_width - img_width) / 2
            y_offset = self.margin + (available_height - img_height) / 2

            img_reader = ImageReader(image)
            c.drawImage(
                img_reader,
                x_offset,
                y_offset,
                width=img_width,
                height=img_height,
                preserveAspectRatio=True
            )

            # Page number
            c.setFont("Helvetica", 8)
            c.setFillColorRGB(0.5, 0.5, 0.5)
            c.drawCentredString(
                page_width / 2,
                self.margin / 2,
                f"Page {i + 1} of {len(images)}"
            )

        c.save()
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()


# Singleton instance
_export_service: Optional[DashboardExportService] = None


def get_export_service() -> DashboardExportService:
    """Get or create the export service singleton."""
    global _export_service
    if _export_service is None:
        _export_service = DashboardExportService()
    return _export_service
