"""
News Controller — Person 5 Module
Handles: GET /news, GET /sources
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from repositories.news_repository import NewsRepository
from schemas.news_schema import ArticleResponse, SourceResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["News"])

news_repo = NewsRepository()


@router.get(
    "",
    response_model=List[ArticleResponse],
    summary="Fetch articles",
    description="Returns a paginated list of articles from the database, optionally filtered by source or category.",
)
async def get_articles(
    limit: int = Query(default=20, ge=1, le=100, description="Max number of articles to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    source: Optional[str] = Query(default=None, description="Filter by source name"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
):
    """Fetch articles from the database with optional filters."""
    try:
        articles = news_repo.get_articles(
            limit=limit, offset=offset, source=source, category=category
        )
        logger.info(f"Fetched {len(articles)} articles (limit={limit}, offset={offset})")
        return articles
    except Exception as e:
        logger.error(f"Error fetching articles: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch articles: {str(e)}")


@router.get(
    "/sources",
    response_model=List[SourceResponse],
    summary="List sources",
    description="Returns all registered news sources.",
)
async def get_sources():
    """Return all available news sources."""
    try:
        sources = news_repo.get_sources()
        logger.info(f"Fetched {len(sources)} sources")
        return sources
    except Exception as e:
        logger.error(f"Error fetching sources: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch sources: {str(e)}")