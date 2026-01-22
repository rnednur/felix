"""
Theming API Endpoints

Provides endpoints for color extraction and theme management.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import logging
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User, Workspace
from app.schemas.theming import (
    ColorExtractionRequest,
    ColorExtractionResponse,
    ExtractedColorSchema,
    ApplyThemeRequest,
    ThemePalette,
    WorkspaceTheme
)
from app.services.color_extraction_service import get_color_extraction_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/theming", tags=["theming"])


@router.post("/extract-colors", response_model=ColorExtractionResponse)
async def extract_colors(
    request: ColorExtractionRequest,
    current_user: User = Depends(get_current_user)
) -> ColorExtractionResponse:
    """
    Extract dominant colors from an uploaded image using LLM vision.

    Accepts a base64-encoded image and returns the extracted colors
    along with a suggested theme palette. Uses Gemini vision for
    intelligent brand color analysis with fallback to algorithmic extraction.
    """
    try:
        service = get_color_extraction_service()
        service.num_colors = request.num_colors

        # Use async LLM-powered extraction
        colors = await service.extract_from_base64_async(request.image_data)
        palette = service.generate_theme_palette(colors)

        return ColorExtractionResponse(
            success=True,
            colors=[
                ExtractedColorSchema(
                    rgb=c.rgb,
                    hex=c.hex,
                    hsl=c.hsl,
                    hsl_css=c.hsl_css,
                    frequency=c.frequency
                )
                for c in colors
            ],
            palette=palette
        )

    except ValueError as e:
        logger.error(f"Color extraction validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Color extraction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Color extraction failed: {str(e)}")


@router.post("/extract-colors/upload")
async def extract_colors_from_upload(
    file: UploadFile = File(...),
    num_colors: int = 5,
    current_user: User = Depends(get_current_user)
) -> ColorExtractionResponse:
    """
    Extract dominant colors from an uploaded image file using LLM vision.

    Accepts PNG, JPEG, GIF, or WebP images. Uses Gemini vision for
    intelligent brand color analysis with fallback to algorithmic extraction.
    """
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )

    try:
        image_bytes = await file.read()

        # Convert to base64 for LLM vision
        import base64
        base64_data = base64.b64encode(image_bytes).decode('utf-8')
        mime_type = file.content_type or 'image/png'
        base64_with_prefix = f"data:{mime_type};base64,{base64_data}"

        service = get_color_extraction_service()
        service.num_colors = num_colors

        # Use async LLM-powered extraction
        colors = await service.extract_from_base64_async(base64_with_prefix)
        palette = service.generate_theme_palette(colors)

        return ColorExtractionResponse(
            success=True,
            colors=[
                ExtractedColorSchema(
                    rgb=c.rgb,
                    hex=c.hex,
                    hsl=c.hsl,
                    hsl_css=c.hsl_css,
                    frequency=c.frequency
                )
                for c in colors
            ],
            palette=palette
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Color extraction from upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspaces/{workspace_id}/theme")
async def apply_theme_to_workspace(
    workspace_id: str,
    palette: ThemePalette,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Apply a theme palette to a workspace.

    The palette is stored in the workspace's metadata field.
    """
    # Validate workspace
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.deleted_at.is_(None)
    ).first()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Store theme in workspace metadata
        metadata = workspace.metadata or {}
        metadata["theme"] = {
            "primary": palette.primary,
            "secondary": palette.secondary,
            "accent": palette.accent,
            "background": palette.background,
            "text": palette.text,
            "css_variables": palette.css_variables,
            "colors": [c.dict() for c in palette.colors] if palette.colors else []
        }

        workspace.metadata = metadata
        db.commit()

        return {
            "success": True,
            "workspace_id": workspace_id,
            "message": "Theme applied successfully"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to apply theme: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces/{workspace_id}/theme")
async def get_workspace_theme(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get the current theme for a workspace.
    """
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.deleted_at.is_(None)
    ).first()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    metadata = workspace.metadata or {}
    theme = metadata.get("theme")

    return {
        "workspace_id": workspace_id,
        "has_theme": theme is not None,
        "theme": theme
    }


@router.delete("/workspaces/{workspace_id}/theme")
async def remove_workspace_theme(
    workspace_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Remove the custom theme from a workspace (revert to default).
    """
    workspace = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.deleted_at.is_(None)
    ).first()

    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if workspace.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        metadata = workspace.metadata or {}
        if "theme" in metadata:
            del metadata["theme"]
            workspace.metadata = metadata
            db.commit()

        return {
            "success": True,
            "workspace_id": workspace_id,
            "message": "Theme removed successfully"
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to remove theme: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
