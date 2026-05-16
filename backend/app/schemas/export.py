"""
Export Schemas

Pydantic models for dashboard export requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class PDFExportRequest(BaseModel):
    """Request to generate PDF from dashboard image."""
    image_data: str = Field(..., description="Base64 encoded PNG image data (data URL)")
    filename: str = Field(default="dashboard", description="Output filename without extension")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    title: Optional[str] = Field(default=None, description="Optional title to add to PDF")
    include_metadata: bool = Field(default=True, description="Include generation metadata")


class ExportResponse(BaseModel):
    """Response after export generation."""
    success: bool
    message: str
    filename: Optional[str] = None


class ExportFormat(BaseModel):
    """Supported export formats."""
    format: Literal["png", "pdf"]
    description: str
