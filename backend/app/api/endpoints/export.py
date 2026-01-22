"""
Export API Endpoints

Provides endpoints for exporting dashboards to PDF format.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.schemas.export import PDFExportRequest, ExportResponse
from app.services.dashboard_export_service import get_export_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/pdf")
async def export_to_pdf(
    request: PDFExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Response:
    """
    Generate a PDF from a dashboard image.

    Accepts a base64-encoded PNG image and returns a PDF document.

    The image_data should be a data URL (e.g., data:image/png;base64,...)
    or just the base64-encoded image data.
    """
    try:
        export_service = get_export_service()

        pdf_bytes = export_service.generate_pdf_from_image(
            image_data=request.image_data,
            filename=request.filename,
            width=request.width,
            height=request.height,
            title=request.title,
            include_metadata=request.include_metadata
        )

        # Return PDF as downloadable file
        filename = f"{request.filename}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(pdf_bytes))
            }
        )

    except ValueError as e:
        logger.error(f"PDF export validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"PDF export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/formats")
async def get_export_formats(
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Get available export formats.

    Returns a list of supported export formats with descriptions.
    """
    return {
        "formats": [
            {
                "format": "png",
                "description": "High-resolution PNG image",
                "client_side": True
            },
            {
                "format": "pdf",
                "description": "PDF document suitable for printing",
                "client_side": False
            }
        ]
    }
