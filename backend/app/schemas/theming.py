"""
Theming Schemas

Pydantic models for color extraction and theme management.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple, Any


class ExtractedColorSchema(BaseModel):
    """Schema for an extracted color."""
    rgb: Tuple[int, int, int] = Field(..., description="RGB values (0-255)")
    hex: str = Field(..., description="Hex color string (#RRGGBB)")
    hsl: Tuple[float, float, float] = Field(..., description="HSL values (H: 0-360, S: 0-100, L: 0-100)")
    hsl_css: str = Field(..., description="CSS HSL value string")
    frequency: float = Field(..., description="Frequency in image (0-1)")


class ColorExtractionRequest(BaseModel):
    """Request to extract colors from an image."""
    image_data: str = Field(..., description="Base64 encoded image data (with or without data URL prefix)")
    num_colors: int = Field(default=5, ge=1, le=10, description="Number of colors to extract")


class ColorExtractionResponse(BaseModel):
    """Response with extracted colors."""
    success: bool
    colors: List[ExtractedColorSchema]
    palette: Dict[str, Any] = Field(default_factory=dict, description="Generated theme palette")


class ThemePalette(BaseModel):
    """A complete theme palette."""
    primary: str = Field(..., description="Primary color (hex)")
    secondary: Optional[str] = Field(None, description="Secondary color (hex)")
    accent: Optional[str] = Field(None, description="Accent color (hex)")
    background: Optional[str] = Field(None, description="Background color")
    text: Optional[str] = Field(None, description="Text color")
    colors: List[ExtractedColorSchema] = Field(default_factory=list, description="All extracted colors")
    css_variables: Dict[str, str] = Field(default_factory=dict, description="CSS custom properties")


class ApplyThemeRequest(BaseModel):
    """Request to apply a theme to a workspace."""
    workspace_id: str = Field(..., description="Workspace ID to apply theme to")
    palette: ThemePalette = Field(..., description="Theme palette to apply")


class WorkspaceTheme(BaseModel):
    """Theme settings for a workspace."""
    workspace_id: str
    palette: Optional[ThemePalette] = None
    custom_css: Optional[str] = None
    source_image_name: Optional[str] = None
