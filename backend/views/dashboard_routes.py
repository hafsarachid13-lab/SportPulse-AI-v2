"""
Dashboard Routes — Person 5 Module (Upgraded)
Consolidated FastAPI endpoints for:
  • Dashboard KPIs, analytics, charts, and filtering
  • Review generation & retrieval (via shared singleton)
  • Multi-format export (PDF, Excel, CSV, JSON, ZIP)
  • Export history & downloadable reports archive
"""

import logging
import os
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional

from backend.services.review_service import ReviewService
from backend.services.dashboard_service import DashboardService
from backend.services.export_service import ExportService
from backend.schemas.dashboard_schema import (
    DashboardResponse,
    DashboardFilterParams,
    KPICard,
    QuickStats,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Dashboard"])

# ── Singleton services (shared state with controller) ──
review_service = ReviewService()
dashboard_service = DashboardService()
export_service = ExportService()


# ──────────────────────────────────────────────────────────
# DASHBOARD DATA ENDPOINTS
# ──────────────────────────────────────────────────────────

@router.get(
    "/stats",
    response_model=QuickStats,
    summary="Get quick statistics",
    description="Returns high-level statistics for the landing page.",
)
async def get_stats():
    """Get quick stats for the frontend homepage."""
    try:
        # Tenter de récupérer la dernière revue
        review = review_service.get_latest_review()
        
        # Si pas de revue, on essaie d'en générer une rapide ou on renvoie des zéros
        if not review:
            logger.info("No cached review for stats, returning empty metrics.")
            return QuickStats(
                total_articles=0,
                active_sources=0,
                average_ai_score=85,
                covered_sports=0,
                today_count=0
            )

        articles = review.get("articles", [])
        kpis = dashboard_service.get_kpi_cards(articles)
        
        return QuickStats(
            total_articles=kpis.get("total_articles", 0),
            active_sources=kpis.get("active_sources", 0),
            average_ai_score=int(kpis.get("avg_credibility", 0.85) * 100),
            covered_sports=kpis.get("categories_count", 0),
            today_count=kpis.get("total_articles", 0)
        )

    except Exception as e:
        logger.error(f"Error in get_stats: {e}", exc_info=True)
        return QuickStats(
            total_articles=0,
            active_sources=0,
            average_ai_score=85,
            covered_sports=0,
            today_count=0
        )


@router.get(
    "/dashboard-data",
    response_model=DashboardResponse,
    summary="Get complete dashboard data",
    description="Returns all KPIs, charts, analytics, and filter options for the dashboard.",
)
async def get_dashboard_data():
    """Get complete dashboard analytics and KPI data."""
    try:
        review = review_service.get_latest_review()

        if not review:
            logger.info("No cached review, generating new one...")
            review = review_service.generate_review()

        if not review or not review.get("articles"):
            raise HTTPException(
                status_code=404,
                detail="No review available. Please generate a review first.",
            )

        logger.info(
            f"Generating dashboard data from {len(review.get('articles', []))} articles..."
        )
        dashboard_data = dashboard_service.get_dashboard_data(review)
        return dashboard_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating dashboard data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate dashboard data: {str(e)}",
        )


@router.get(
    "/dashboard-data/filtered",
    response_model=DashboardResponse,
    summary="Get filtered dashboard data",
    description="Returns dashboard data filtered by source, sport, credibility, or importance.",
)
async def get_filtered_dashboard_data(
    source: Optional[str] = Query(None, description="Filter by article source"),
    sport: Optional[str] = Query(None, description="Filter by sport category"),
    min_credibility: float = Query(
        0.0, ge=0, le=1, description="Minimum credibility score"
    ),
    min_importance: float = Query(
        0.0, ge=0, le=1, description="Minimum importance score"
    ),
):
    """Get dashboard data with applied filters."""
    try:
        review = review_service.get_latest_review()
        if not review:
            raise HTTPException(
                status_code=404,
                detail="No review available. Please generate a review first.",
            )

        articles = review.get("articles", [])

        # Apply filters
        filtered_articles = dashboard_service.filter_articles(
            articles,
            source=source,
            sport=sport,
            min_credibility=min_credibility,
            min_importance=min_importance,
        )

        if not filtered_articles:
            raise HTTPException(
                status_code=404,
                detail="No articles match the specified filters.",
            )

        # Create filtered review
        filtered_review = review.copy()
        filtered_review["articles"] = filtered_articles

        dashboard_data = dashboard_service.get_dashboard_data(filtered_review)
        return dashboard_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating filtered dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to filter dashboard: {str(e)}",
        )


@router.get(
    "/dashboard-kpis",
    response_model=KPICard,
    summary="Get KPI cards only",
    description="Quick endpoint for just the KPI cards data.",
)
async def get_kpi_cards():
    """Get just the KPI cards for quick dashboard load."""
    try:
        review = review_service.get_latest_review()
        if not review:
            review = review_service.generate_review()

        articles = review.get("articles", []) if review else []
        kpis = dashboard_service.get_kpi_cards(articles)
        return kpis

    except Exception as e:
        logger.error(f"Error generating KPIs: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate KPIs: {str(e)}"
        )


@router.get(
    "/dashboard/analytics",
    summary="Get dashboard analytics with date range",
    description="Returns full analytics with optional date_from/date_to filtering.",
)
async def get_dashboard_analytics(
    sport: Optional[str] = Query(None, description="Filter by sport category"),
    source: Optional[str] = Query(None, description="Filter by article source"),
    min_credibility: float = Query(0.0, ge=0, le=1, description="Minimum credibility score"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Full analytics endpoint with date range and multi-filter support."""
    try:
        # Le Dashboard Analytics récupère toujours les 7 derniers jours indépendamment de la revue quotidienne
        from backend.database.db import SessionLocal
        from backend.database.models import Article
        from datetime import datetime, timedelta
        
        db = SessionLocal()
        try:
            last_week_start = datetime.now() - timedelta(days=7)
            logger.info("Fetching articles from the last 7 days for the dashboard...")
            
            # On récupère tous les articles de la semaine
            db_articles = db.query(Article).filter(Article.collected_at >= last_week_start).order_by(Article.published_at.desc()).all()
            
            if not db_articles:
                # Fallback si aucun article dans les 7 jours: on prend les 100 derniers globaux
                db_articles = db.query(Article).order_by(Article.collected_at.desc()).limit(100).all()
                
            articles = review_service._convert_articles_to_dict(db_articles)
            
            # On crée une fausse revue uniquement pour le dashboard_service (qui attend ce format)
            review = {
                "date": datetime.now().isoformat(),
                "articles": articles,
                "sections": {}
            }
        finally:
            db.close()

        if not articles:
            raise HTTPException(
                status_code=404,
                detail="Aucun article trouvé en base de données pour générer les statistiques.",
            )

        # Apply filters
        filtered = dashboard_service.filter_articles(
            articles,
            source=source,
            sport=sport,
            min_credibility=min_credibility,
        )

        # Date range filter
        if date_from or date_to:
            date_filtered = []
            for a in filtered:
                pub = a.get("published_at", "")
                if not pub:
                    continue
                # Gérer datetime ou string
                if hasattr(pub, "isoformat"):
                    pub_date = pub.date().isoformat()
                else:
                    pub_date = str(pub).split(" ")[0].split("T")[0]
                    
                if date_from and pub_date < date_from:
                    continue
                if date_to and pub_date > date_to:
                    continue
                date_filtered.append(a)
            filtered = date_filtered

        filtered_review = review.copy()
        filtered_review["articles"] = filtered

        dashboard_data = dashboard_service.get_dashboard_data(filtered_review)

        # Add executive summary from review sections
        exec_summary = review.get("sections", {}).get("executive_summary", {})
        dashboard_data["executive_summary"] = exec_summary

        return dashboard_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in dashboard analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load analytics: {str(e)}",
        )


@router.get(
    "/news",
    summary="Get all collected news articles",
    description="Returns all articles from the latest review.",
)
async def get_news():
    """Get all collected articles."""
    review = review_service.get_latest_review()
    articles = review.get("articles", []) if review else []
    return {
        "count": len(articles),
        "articles": articles,
    }


@router.get(
    "/dashboard/sources",
    summary="Get source list with credibility",
    description="Returns unique sources with their credibility metrics.",
)
async def get_sources():
    """Get sources with credibility from latest review."""
    review = review_service.get_latest_review()
    articles = review.get("articles", []) if review else []

    sources_map = {}
    for a in articles:
        src = a.get("source", "Unknown")
        if src not in sources_map:
            sources_map[src] = {"name": src, "credibility_score": a.get("credibility_score", 0.75), "count": 0}
        sources_map[src]["count"] += 1

    return {"sources": list(sources_map.values())}


@router.get(
    "/sports",
    summary="Get list of all 15 sports categories",
    description="Returns the full list of 15 sport categories supported by the NLP engine.",
)
async def get_sports():
    """Get the full list of 15 sports from the NLP service."""
    # Liste complète des 15 catégories définies dans nlp_service.py
    sports = [
        "Football", "Tennis", "Basketball", "Rugby", "Cyclisme", 
        "Athlétisme", "Natation", "Handball", "Volleyball", 
        "Sports Mécaniques", "Combat", "Golf", "Hockey", 
        "Équitation", "Ski"
    ]
    return {"sports": sorted(sports), "total_categories": len(sports)}


# ──────────────────────────────────────────────────────────
# REVIEW GENERATION & MANAGEMENT
# ──────────────────────────────────────────────────────────

@router.post(
    "/generate-review",
    summary="Generate new press review",
    description="Fetches articles, generates structured review, and caches it for dashboard.",
)
async def generate_review():
    """Generate a new press review and cache it for dashboard."""
    try:
        logger.info("Generating new press review...")
        review = review_service.generate_review()

        if not review:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate review. No articles available.",
            )

        # Also generate PDF
        pdf_url = None
        try:
            pdf_filename = export_service.generate_pdf(
                review,
                filename=f"review_{review.get('date', 'latest')}.pdf",
            )
            pdf_url = f"/api/v1/export/download/{pdf_filename}"
        except Exception as e:
            logger.warning(f"PDF generation failed: {e}")

        return {
            "status": "success",
            "message": (
                f"Review generated with "
                f"{review.get('metadata', {}).get('total_articles', 0)} articles"
            ),
            "review_id": review.get("id"),
            "review_date": review.get("date"),
            "total_articles": review.get("metadata", {}).get("total_articles", 0),
            "total_sources": review.get("metadata", {}).get("sources_count", 0),
            "total_sports": review.get("metadata", {}).get("categories_count", 0),
            "pdf_url": pdf_url,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating review: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate review: {str(e)}",
        )


@router.get(
    "/review",
    summary="Get latest review (alias)",
    description="Returns the cached latest press review in full detail.",
)
async def get_review():
    """Get the latest cached review."""
    try:
        review = review_service.get_latest_review()
        if not review:
            raise HTTPException(
                status_code=404,
                detail="No review has been generated yet. Please generate one first.",
            )
        return review

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving review: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve review: {str(e)}"
        )


@router.get(
    "/review/latest",
    summary="Get latest review",
    description="Returns the cached latest press review in full detail.",
)
async def get_latest_review():
    """Get the latest cached review."""
    return await get_review()


@router.get(
    "/review/history",
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
# EXPORT ENDPOINTS
# ──────────────────────────────────────────────────────────

def _require_review():
    """Helper: get current review or generate one if missing."""
    review = review_service.get_latest_review()
    if not review:
        logger.info("No review found for export, generating one now...")
        review = review_service.generate_review()
        
    if not review:
        raise HTTPException(
            status_code=404, detail="No review available to export and generation failed."
        )
    return review


@router.get(
    "/export/pdf",
    summary="Export review as PDF",
    description="Generate and download review as PDF.",
)
async def export_pdf():
    """Export latest review to PDF."""
    review = _require_review()
    # Sanitize date for filename (Windows doesn't like ':')
    date_str = review.get('date', 'latest').replace(':', '-')
    try:
        filename = export_service.generate_pdf(
            review,
            filename=f"review_{date_str}.pdf",
        )
        return {
            "status": "success",
            "format": "pdf",
            "filename": filename,
            "download_url": f"/api/v1/export/download/{filename}",
        }
    except Exception as e:
        logger.error(f"PDF export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"PDF export failed: {str(e)}"
        )


@router.get(
    "/export/excel",
    summary="Export review as Excel",
    description="Generate and download review as Excel (.xlsx).",
)
async def export_excel():
    """Export latest review to Excel."""
    review = _require_review()
    date_str = review.get('date', 'latest').replace(':', '-')
    try:
        filename = export_service.generate_excel(
            review,
            filename=f"review_{date_str}.xlsx",
        )
        return {
            "status": "success",
            "format": "excel",
            "filename": filename,
            "download_url": f"/api/v1/export/download/{filename}",
        }
    except Exception as e:
        logger.error(f"Excel export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Excel export failed: {str(e)}"
        )


@router.get(
    "/export/csv",
    summary="Export review as CSV",
    description="Generate and download review as CSV.",
)
async def export_csv():
    """Export latest review to CSV."""
    review = _require_review()
    date_str = review.get('date', 'latest').replace(':', '-')
    try:
        filename = export_service.generate_csv(
            review,
            filename=f"review_{date_str}.csv",
        )
        return {
            "status": "success",
            "format": "csv",
            "filename": filename,
            "download_url": f"/api/v1/export/download/{filename}",
        }
    except Exception as e:
        logger.error(f"CSV export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"CSV export failed: {str(e)}"
        )


@router.get(
    "/export/json",
    summary="Export review as JSON",
    description="Generate and download review as JSON.",
)
async def export_json():
    """Export latest review to JSON."""
    review = _require_review()
    date_str = review.get('date', 'latest').replace(':', '-')
    try:
        filename = export_service.generate_json(
            review,
            filename=f"review_{date_str}.json",
        )
        return {
            "status": "success",
            "format": "json",
            "filename": filename,
            "download_url": f"/api/v1/export/download/{filename}",
        }
    except Exception as e:
        logger.error(f"JSON export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"JSON export failed: {str(e)}"
        )


@router.get(
    "/export/all",
    summary="Export review in all formats",
    description="Generate ZIP with all format exports (PDF, Excel, CSV, JSON).",
)
async def export_all():
    """Export review in all formats (ZIP)."""
    review = _require_review()
    date_str = review.get('date', 'latest').replace(':', '-')
    try:
        filename = export_service.generate_zip(
            review,
            filename=f"review_bundle_{date_str}.zip",
        )
        return {
            "status": "success",
            "format": "zip",
            "filename": filename,
            "download_url": f"/api/v1/export/download/{filename}",
            "formats_included": ["pdf", "excel", "csv", "json"],
        }
    except Exception as e:
        logger.error(f"ZIP export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"ZIP export failed: {str(e)}"
        )


# ──────────────────────────────────────────────────────────
# DOWNLOAD & HISTORY ENDPOINTS
# ──────────────────────────────────────────────────────────

@router.get(
    "/export/download/{filename}",
    summary="Download exported file",
    description="Download a generated export file (PDF, Excel, CSV, JSON, etc.).",
)
async def download_export(filename: str):
    """Download a previously generated export file."""
    try:
        # Security: prevent path traversal attacks
        if "/" in filename or "\\" in filename or ".." in filename:
            raise HTTPException(status_code=400, detail="Invalid filename.")

        file_path = export_service.get_export_path(filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found.")

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Download failed: {str(e)}"
        )


@router.get(
    "/export/history",
    summary="Get export history",
    description="Returns a list of all exports with metadata.",
)
async def get_export_history():
    """Get export history and stats."""
    history = export_service.get_export_history()
    stats = export_service.get_export_stats()
    available = export_service.list_available_files()
    return {
        "total_exports": len(history),
        "exports": history,
        "stats": stats,
        "available_files": available,
    }


@router.get(
    "/export/files",
    summary="List available export files",
    description="Lists all downloadable files in the exports directory.",
)
async def list_export_files():
    """List all files in the exports directory."""
    files = export_service.list_available_files()
    return {
        "total_files": len(files),
        "files": files,
    }
