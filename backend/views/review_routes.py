from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import datetime
from typing import Dict, Any, List

from backend.services.scraper_service import fetch_articles, get_sources_with_credibility
from backend.services.export_service import ExportService
from backend.services.review_service import ReviewService

export_service_instance = ExportService()
review_service = ReviewService()

router = APIRouter()

# ── In-memory storage ──────────────────────────────
_latest_review: Dict[str, Any] = {}
_processed_articles: List[Dict[str, Any]] = []

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATIC_PDF_DIR = os.path.join(BASE_DIR, "static_pdfs")
os.makedirs(STATIC_PDF_DIR, exist_ok=True)

# ──────────────────────────────────────────────────
# ✅ GENERATE REVIEW
# ──────────────────────────────────────────────────
@router.post("/generate-review")
async def generate_review_endpoint():
    try:
        review = review_service.generate_review()
        if not review:
            raise HTTPException(status_code=404, detail="No articles found to generate review")

        return {
            "status": "success",
            "message": "Review generated successfully",
            "review": review
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────
# ✅ GET REVIEW
# ──────────────────────────────────────────────────
@router.get("/review")
async def get_review_endpoint():
    from backend.core.scheduler import news_scheduler
    review = review_service.get_latest_review()
    if not review:
        # Tenter une génération forcée si rien n'est trouvé
        review = review_service.generate_review()
        
    if not review:
        raise HTTPException(status_code=404, detail="No review generated yet")
    
    # Ajouter le temps du prochain passage du scheduler dans la réponse
    if isinstance(review, dict):
        if "metadata" not in review:
            review["metadata"] = {}
        review["metadata"]["next_scrape"] = news_scheduler.get_next_run_time()
        
    return review


# ──────────────────────────────────────────────────
# ✅ GET NEWS
# ──────────────────────────────────────────────────
@router.get("/news")
async def get_news_endpoint():
    return {
        "count": len(_processed_articles),
        "articles": _processed_articles
    }


# ──────────────────────────────────────────────────
# ✅ GET SOURCES
# ──────────────────────────────────────────────────
@router.get("/review/sources")
async def get_sources_endpoint():
    try:
        sources = get_sources_with_credibility()
        return {"sources": sources}
    except Exception:
        return {
            "sources": [
                {"name": "ESPN", "credibility_score": 0.95},
                {"name": "Sky Sports", "credibility_score": 0.92}
            ]
        }


# ──────────────────────────────────────────────────
# ✅ DOWNLOAD PDF
# ──────────────────────────────────────────────────
@router.get("/review/pdf")
async def download_pdf():
    pdf_path = os.path.join(STATIC_PDF_DIR, "review.pdf")

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="review.pdf"
    )


# ──────────────────────────────────────────────────
# ✅ COMPATIBILITY ROUTES (IMPORTANT)
# ──────────────────────────────────────────────────
@router.get("/review/latest")
async def review_latest():
    return await get_review_endpoint()


@router.post("/review/generate")
async def review_generate():
    return await generate_review_endpoint()
