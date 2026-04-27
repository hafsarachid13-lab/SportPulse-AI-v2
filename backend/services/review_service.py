import logging
import datetime
import uuid
from typing import Dict, List, Any

from services.scraper_service import fetch_articles

logger = logging.getLogger(__name__)


class ReviewService:
    def __init__(self):
        self._latest_review: Dict[str, Any] = None

    def select_top_articles(self, articles: List[Dict[str, Any]], limit: int = 20) -> List[Dict[str, Any]]:
        """Select top articles by importance score."""
        for article in articles:
            if "importance_score" not in article:
                article["importance_score"] = 0.5

        sorted_articles = sorted(
            articles,
            key=lambda x: x.get("importance_score", 0),
            reverse=True,
        )
        return sorted_articles[:limit]

    def format_review(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format review data from enriched/scraped articles."""
        formatted_articles = []
        categories = {}
        top_headlines = []

        for idx, art in enumerate(articles):
            # Use the pre-classified sport from the scraper, with fallback
            sport = art.get("sport", "General")

            formatted_art = {
                "id": str(uuid.uuid4()),
                "title": art.get("title", "Untitled"),
                "url": art.get("url", "#"),
                "source": art.get("source", "Unknown"),
                "published_date": art.get("published_date", datetime.date.today().isoformat()),
                "sport": sport,
                "summary": art.get("summary", art.get("text", ""))[:500],
                "keywords": art.get("keywords", [sport.lower()]),
                "importance_score": art.get("importance_score", 0.0),
            }
            formatted_articles.append(formatted_art)

            if sport not in categories:
                categories[sport] = []
            categories[sport].append(formatted_art)

            if idx < 5:
                top_headlines.append(formatted_art["title"])

        review_data = {
            "title": f"Daily Sports Review — {datetime.date.today().strftime('%B %d, %Y')}",
            "date": datetime.datetime.now().isoformat(),
            "generated_at": datetime.datetime.now().isoformat(),
            "highlights": top_headlines,
            "top_headlines": top_headlines,
            "categories": categories,
            "articles": formatted_articles,
            "metadata": {
                "total_articles": len(formatted_articles),
                "sources_count": len(set(a.get("source", "") for a in formatted_articles)),
                "categories_count": len(categories),
            },
            "pdf_path": "daily_sports_review.pdf",
        }
        return review_data

    def generate_review(self) -> Dict[str, Any]:
        """Generate structured review from REAL scraped data."""
        logger.info("=" * 50)
        logger.info("📰 STARTING REVIEW GENERATION PIPELINE")
        logger.info("=" * 50)

        logger.info("Step 1/3 — Fetching articles from live sources...")
        raw_articles = fetch_articles(fetch_full_text=True)

        if not raw_articles:
            logger.error("No articles fetched from any source.")
            return {}

        logger.info(f"Step 2/3 — Selecting top articles from {len(raw_articles)} scraped...")
        top_articles = self.select_top_articles(raw_articles, limit=20)

        logger.info(f"Step 3/3 — Formatting review with {len(top_articles)} articles...")
        self._latest_review = self.format_review(top_articles)

        total = self._latest_review.get("metadata", {}).get("total_articles", 0)
        cats = len(self._latest_review.get("categories", {}))
        logger.info(f"✅ Review ready: {total} articles across {cats} categories")
        logger.info("=" * 50)

        return self._latest_review

    def get_latest_review(self) -> Dict[str, Any]:
        return self._latest_review
