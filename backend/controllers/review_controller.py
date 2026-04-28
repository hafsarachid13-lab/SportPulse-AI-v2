"""
Review Controller — Person 5 Module (Upgraded)
Handles: POST /review/generate, GET /review/latest, GET /review/download/{filename}
         GET /review/export/{format}, GET /review/history
"""

import logging
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.services.review_service import ReviewService
from backend.services.export_service import ExportService
from backend.schemas.review_schema import (
    ReviewResponse,
    GenerateReviewResponse,
    ArticleSchema,
    ReviewHistoryResponse,
)
from backend.database.models import RevueDePresse

logger = logging.getLogger(__name__)

# ── Router ──
router = APIRouter(prefix="/review", tags=["Press Review"])

# ── Singleton services (shared across all routes) ──
review_service = ReviewService()
export_service = ExportService()


# ──────────────────────────────────────────────────────────
# GENERATE REVIEW
# ──────────────────────────────────────────────────────────

@router.post(
    "/generate",
    response_model=GenerateReviewResponse,
    summary="Generate daily press review",
    description="Fetches articles, builds structured review, generates PDF, returns review + download URL.",
)
async def generate_review():
    """Full pipeline: fetch → process → rank → structure → PDF → return"""
    try:
        logger.info("Starting press review generation...")

        # Step 1 — generate STRUCTURED review
        review_data = review_service.generate_review()
        if not review_data or not review_data.get("articles"):
            raise HTTPException(status_code=404, detail="No articles found.")

        logger.info(f"Review generated: {review_data.get('title')}")

        # Step 2 — generate PDF from structured data
        filename = export_service.generate_pdf(review_data)
        logger.info(f"PDF generated: {filename}")

        # Step 3 — build response
        pdf_url = f"/review/download/{filename}"

        return GenerateReviewResponse(
            review=review_data,
            pdf_url=pdf_url,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Review generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Review generation failed: {str(e)}"
        )


# ──────────────────────────────────────────────────────────
# GET LATEST REVIEW
# ──────────────────────────────────────────────────────────

@router.get(
    "/latest",
    response_model=ReviewResponse,
    summary="Get latest generated review",
    description="Returns the most recently generated structured press review.",
)
async def get_latest_review():
    """Return the latest persisted structured review."""
    try:
        review = review_service.get_latest_review()
        if not review:
            raise HTTPException(
                status_code=404, detail="No review has been generated yet."
            )
        return review
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve latest review: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve review: {str(e)}"
        )


# ──────────────────────────────────────────────────────────
# EXPORT BY FORMAT
# ──────────────────────────────────────────────────────────

@router.get(
    "/export/{format}",
    summary="Export latest review to a specific format",
    description="Formats supported: pdf, excel, csv, json, zip",
)
async def export_review(format: str):
    """Dynamically generate and download the review in the requested format."""
    review_data = review_service.get_latest_review()
    if not review_data:
        raise HTTPException(
            status_code=404,
            detail="No review has been generated yet. Please generate one first.",
        )

    format = format.lower()
    try:
        if format == "pdf":
            filename = export_service.generate_pdf(review_data, "review.pdf")
            media_type = "application/pdf"
        elif format in ("excel", "xlsx"):
            filename = export_service.generate_excel(review_data, "review.xlsx")
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif format == "csv":
            filename = export_service.generate_csv(review_data, "review.csv")
            media_type = "text/csv"
        elif format == "json":
            filename = export_service.generate_json(review_data, "review.json")
            media_type = "application/json"
        elif format == "zip":
            filename = export_service.generate_zip(review_data, "review_exports.zip")
            media_type = "application/zip"
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported format. Supported: pdf, excel, csv, json, zip",
            )

        export_path = export_service.get_export_path(filename)
        return FileResponse(
            path=export_path,
            media_type=media_type,
            filename=filename,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed for format {format}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Export failed: {str(e)}"
        )


# ──────────────────────────────────────────────────────────
# DOWNLOAD FILE
# ──────────────────────────────────────────────────────────

@router.get(
    "/download/{filename}",
    summary="Download a generated file",
    description="Serves the generated file by filename.",
)
async def download_file(filename: str):
    """Serve a generated file by filename with path traversal protection."""
    # Security: prevent path traversal attacks
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    file_path = export_service.get_export_path(filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(
        path=file_path,
        filename=filename,
    )


# ──────────────────────────────────────────────────────────
# REVIEW HISTORY
# ──────────────────────────────────────────────────────────

@router.get(
    "/history",
    summary="Get review generation history",
    description="Returns metadata of all previously generated reviews.",
)
async def get_review_history():
    """Return list of all generated reviews (metadata only)."""
    history = review_service.get_review_history()
    stats = review_service.get_generation_stats()
    return {
        "total": len(history),
        "history": history,
        "generation_stats": stats,
    }


# ──────────────────────────────────────────────────────────
# HAFSA'S DB CONTROLLER (preserved)
# ──────────────────────────────────────────────────────────

class ReviewController:
    def __init__(self):
        pass

    def list_reviews(self, db: Session):
        """Récupère les revues de presse générées."""
        return db.query(RevueDePresse).order_by(RevueDePresse.date.desc()).all()

    def get_today_review(self, db: Session):
        """Récupère la revue de presse la plus récente."""
        from datetime import date
        return (
            db.query(RevueDePresse)
            .filter(RevueDePresse.date == date.today())
            .first()
        )
