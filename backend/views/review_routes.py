from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import datetime
from typing import Dict, Any, List

from services.scraper_service import fetch_articles, get_sources_with_credibility
from services.export_service import ExportService

export_service_instance = ExportService()

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
    global _latest_review, _processed_articles

    try:
        # 1. Fetch articles (real scraping)
        raw_articles = fetch_articles()
        if not raw_articles:
            raise HTTPException(status_code=404, detail="No articles found")

        _processed_articles = raw_articles

        # 2. Categorization
        categories: Dict[str, list] = {}
        for art in raw_articles[:20]:
            sport = art.get("sport", "General")
            categories.setdefault(sport, []).append(art)

        # 3. Build review
        _latest_review = {
            "title": f"Daily Sports Press Review - {datetime.date.today()}",
            "date": datetime.datetime.now().isoformat(),
            "top_headlines": [a["title"] for a in raw_articles[:5]],
            "categories": categories,
            "articles": raw_articles[:20]
        }

        # 4. Generate PDF
        export_service_instance.generate_pdf(_latest_review, "review.pdf")

        return {
            "status": "success",
            "message": "Review generated successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────────
# ✅ GET REVIEW
# ──────────────────────────────────────────────────
@router.get("/review")
async def get_review_endpoint():
    if not _latest_review:
        raise HTTPException(status_code=404, detail="No review generated yet")
    return _latest_review


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
@router.get("/sources")
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
