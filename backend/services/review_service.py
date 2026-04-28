"""
Review Service — Person 5 Module (Upgraded)
Intelligent Press Review Generator:
  • Consumes Person 3 (summaries, keywords, classification, importance) and
    Person 4 (credibility, filtering, dedup) outputs as-is.
  • Ranks articles by importance score.
  • Organises by sport category.
  • Builds structured sections: headlines, summaries, trends, top sources, keyword insights.
  • Generates AI executive summary from structured data.
  • Multilingual labels (FR/EN/AR) for review sections.
  • Maintains review history + cache with thread-safe singleton.
"""

import logging
import datetime
import uuid
import threading
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict

from backend.services.scraper_service import fetch_articles

logger = logging.getLogger(__name__)


class ReviewService:
    """Thread-safe singleton review service with history & scheduling support."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._latest_review: Optional[Dict[str, Any]] = None
        self._review_history: List[Dict[str, Any]] = []
        self._review_cache: Dict[str, Dict[str, Any]] = {}
        self._generation_count: int = 0
        self._last_generated_at: Optional[str] = None
        self._initialized = True

    # ──────────────────────────────────────────────────────
    # ARTICLE SELECTION & RANKING
    # ──────────────────────────────────────────────────────

    def select_top_articles(
        self, articles: List[Dict[str, Any]], limit: int = 25
    ) -> List[Dict[str, Any]]:
        """Select and rank top articles by importance score (Person 3 output)."""
        for article in articles:
            if "importance_score" not in article:
                article["importance_score"] = 0.5

        sorted_articles = sorted(
            articles,
            key=lambda x: x.get("importance_score", 0),
            reverse=True,
        )
        return sorted_articles[:limit]

    # ──────────────────────────────────────────────────────
    # SECTION BUILDERS
    # ──────────────────────────────────────────────────────

    def _extract_keywords(
        self, articles: List[Dict[str, Any]], top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Extract top keywords from articles (using Person 3's extracted keywords if available)."""
        keyword_freq: Counter = Counter()

        for article in articles:
            # Use pre-extracted keywords from Person 3
            keywords = article.get("keywords", [])
            if isinstance(keywords, list):
                for kw in keywords:
                    if isinstance(kw, str) and len(kw) > 2:
                        keyword_freq[kw.lower()] += 1

            # Fallback: extract from title and sport
            if not keywords:
                sport = article.get("sport", "").lower()
                title = article.get("title", "").lower()
                if sport:
                    keyword_freq[sport] += 1
                for word in title.split():
                    clean = word.strip(".,;:!?\"'()[]")
                    if len(clean) > 4 and clean not in {
                        "sports", "today", "match", "game", "about",
                        "their", "after", "which", "could", "would",
                    }:
                        keyword_freq[clean] += 1

        return [{"keyword": k, "count": v} for k, v in keyword_freq.most_common(top_k)]

    def _identify_trends(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify trending topics and patterns in articles."""
        sports_trend = Counter(a.get("sport", "General") for a in articles)
        sources_trend = Counter(a.get("source", "Unknown") for a in articles)

        importance_scores = [a.get("importance_score", 0.5) for a in articles]
        avg_importance = (
            sum(importance_scores) / len(importance_scores) if importance_scores else 0
        )

        return {
            "trending_sports": [
                {"sport": s, "count": c} for s, c in sports_trend.most_common(5)
            ],
            "trending_sources": [
                {"source": s, "count": c} for s, c in sources_trend.most_common(5)
            ],
            "avg_importance": round(avg_importance, 3),
            "importance_distribution": {
                "high": len([s for s in importance_scores if s >= 0.7]),
                "medium": len([s for s in importance_scores if 0.4 <= s < 0.7]),
                "low": len([s for s in importance_scores if s < 0.4]),
            },
        }

    def _aggregate_top_sources(
        self, articles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Aggregate metrics by source (credibility, article count, avg importance)."""
        sources: Dict[str, Dict] = defaultdict(
            lambda: {"count": 0, "importance_sum": 0, "credibility_sum": 0, "articles": []}
        )

        for article in articles:
            source = article.get("source", "Unknown")
            sources[source]["count"] += 1
            sources[source]["importance_sum"] += article.get("importance_score", 0.5)
            sources[source]["credibility_sum"] += article.get("credibility", 0.75)
            sources[source]["articles"].append(article.get("title", ""))

        result = []
        for source, data in sources.items():
            cnt = max(data["count"], 1)
            result.append({
                "source": source,
                "article_count": data["count"],
                "avg_importance": round(data["importance_sum"] / cnt, 3),
                "credibility": round(data["credibility_sum"] / cnt, 3),
                "top_articles": data["articles"][:3],
            })

        return sorted(result, key=lambda x: x["article_count"], reverse=True)

    def _build_headlines_section(
        self, articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build headlines section with top stories."""
        top_5 = articles[:5]
        return {
            "title": "Breaking Headlines",
            "description": "Top 5 most important stories of the day",
            "articles": [
                {
                    "rank": i + 1,
                    "title": a.get("title", ""),
                    "source": a.get("source", ""),
                    "importance": a.get("importance_score", 0),
                    "sport": a.get("sport", ""),
                }
                for i, a in enumerate(top_5)
            ],
        }

    def _build_sports_sections(
        self, articles: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict]]:
        """Build organized sections by sport category."""
        categories: Dict[str, List] = defaultdict(list)

        for article in articles:
            sport = article.get("sport", "General")
            categories[sport].append({
                "id": article.get("id", str(uuid.uuid4())),
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "source": article.get("source", ""),
                "published_date": article.get("published_date", ""),
                "summary": article.get("summary", "")[:300],
                "importance_score": article.get("importance_score", 0),
                "keywords": article.get("keywords", []),
            })

        # Sort each category by importance
        for sport in categories:
            categories[sport].sort(
                key=lambda x: x["importance_score"], reverse=True
            )

        return dict(categories)

    def _build_trends_section(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build trends and insights section."""
        trends = self._identify_trends(articles)
        keywords = self._extract_keywords(articles, top_k=15)

        return {
            "title": "Today's Trends",
            "trending_sports": trends["trending_sports"],
            "trending_sources": trends["trending_sources"],
            "top_keywords": keywords,
            "importance_distribution": trends["importance_distribution"],
            "average_importance": trends["avg_importance"],
        }

    def _build_sources_section(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build top sources insights section."""
        sources = self._aggregate_top_sources(articles)
        return {
            "title": "Source Performance",
            "description": "Top performing sources by article volume and credibility",
            "sources": sources[:10],
        }

    def _build_keywords_section(
        self, articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build keywords and insights section."""
        keywords = self._extract_keywords(articles, top_k=20)
        return {
            "title": "Key Topics & Keywords",
            "description": "Most frequently mentioned topics",
            "keywords": keywords,
        }

    def _build_summaries_section(
        self, articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build summaries digest section."""
        summaries = []
        for a in articles[:10]:
            summary_text = a.get("summary", a.get("text", ""))
            if summary_text:
                summaries.append({
                    "title": a.get("title", "Untitled"),
                    "source": a.get("source", "Unknown"),
                    "sport": a.get("sport", "General"),
                    "summary": summary_text[:400],
                    "importance": a.get("importance_score", 0),
                })
        return {
            "title": "Article Summaries",
            "description": "AI-generated summaries of today's most important articles",
            "items": summaries,
        }

    def _build_executive_summary(
        self, articles: List[Dict[str, Any]], lang: str = "en"
    ) -> Dict[str, Any]:
        """Generate an AI-powered executive summary from structured article data."""
        if not articles:
            return {"title": "Executive Summary", "text": "No articles available.", "lang": lang}

        # Multilingual labels
        labels = self._get_labels(lang)

        sports_count = Counter(a.get("sport", "General") for a in articles)
        sources_count = Counter(a.get("source", "Unknown") for a in articles)
        top_sport = sports_count.most_common(1)[0] if sports_count else ("General", 0)
        top_source = sources_count.most_common(1)[0] if sources_count else ("Unknown", 0)

        avg_importance = sum(a.get("importance_score", 0.5) for a in articles) / len(articles)
        avg_credibility = sum(a.get("credibility", 0.75) for a in articles) / len(articles)
        high_imp = len([a for a in articles if a.get("importance_score", 0) >= 0.7])

        # Top headlines for summary
        top_headlines = [a.get("title", "") for a in articles[:3]]
        headlines_text = "; ".join(top_headlines)

        # Build executive summary text
        if lang == "fr":
            text = (
                f"La revue de presse sportive du jour couvre {len(articles)} articles "
                f"provenant de {len(sources_count)} sources différentes, "
                f"répartis sur {len(sports_count)} catégories sportives. "
                f"Le sport dominant est {top_sport[0]} avec {top_sport[1]} articles. "
                f"La source la plus active est {top_source[0]}. "
                f"{high_imp} articles sont classés haute importance. "
                f"Le score moyen de crédibilité est de {avg_credibility:.0%}. "
                f"Parmi les titres majeurs : {headlines_text}."
            )
        elif lang == "ar":
            text = (
                f"تغطي المراجعة الصحفية الرياضية اليوم {len(articles)} مقالة "
                f"من {len(sources_count)} مصادر مختلفة، "
                f"موزعة على {len(sports_count)} فئات رياضية. "
                f"الرياضة الأبرز هي {top_sport[0]} بـ {top_sport[1]} مقالة. "
                f"المصدر الأكثر نشاطًا هو {top_source[0]}. "
                f"{high_imp} مقالات مصنفة عالية الأهمية. "
                f"متوسط درجة المصداقية هو {avg_credibility:.0%}."
            )
        else:  # English default
            text = (
                f"Today's sports press review covers {len(articles)} articles "
                f"from {len(sources_count)} distinct sources, "
                f"spanning {len(sports_count)} sport categories. "
                f"The dominant sport is {top_sport[0]} with {top_sport[1]} articles. "
                f"The most active source is {top_source[0]}. "
                f"{high_imp} articles are rated high importance. "
                f"Average credibility score stands at {avg_credibility:.0%}. "
                f"Key headlines: {headlines_text}."
            )

        return {
            "title": labels.get("executive_summary", "Executive Summary"),
            "text": text,
            "lang": lang,
            "stats": {
                "total_articles": len(articles),
                "total_sources": len(sources_count),
                "total_sports": len(sports_count),
                "dominant_sport": top_sport[0],
                "top_source": top_source[0],
                "avg_importance": round(avg_importance, 3),
                "avg_credibility": round(avg_credibility, 3),
                "high_importance_count": high_imp,
            },
        }

    @staticmethod
    def _get_labels(lang: str = "en") -> Dict[str, str]:
        """Return section labels in the requested language."""
        labels_map = {
            "en": {
                "executive_summary": "Executive Summary",
                "headlines": "Breaking Headlines",
                "summaries": "Article Summaries",
                "trends": "Today's Trends",
                "top_sources": "Source Performance",
                "keywords": "Key Topics & Keywords",
                "by_sport": "Articles by Sport",
            },
            "fr": {
                "executive_summary": "Résumé Exécutif",
                "headlines": "Titres Principaux",
                "summaries": "Résumés des Articles",
                "trends": "Tendances du Jour",
                "top_sources": "Performance des Sources",
                "keywords": "Sujets & Mots-clés",
                "by_sport": "Articles par Sport",
            },
            "ar": {
                "executive_summary": "ملخص تنفيذي",
                "headlines": "العناوين الرئيسية",
                "summaries": "ملخصات المقالات",
                "trends": "اتجاهات اليوم",
                "top_sources": "أداء المصادر",
                "keywords": "المواضيع والكلمات المفتاحية",
                "by_sport": "مقالات حسب الرياضة",
            },
        }
        return labels_map.get(lang, labels_map["en"])

    # ──────────────────────────────────────────────────────
    # REVIEW FORMATTING
    # ──────────────────────────────────────────────────────

    def format_review(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format review data into comprehensive structured sections."""
        formatted_articles = []

        for art in articles:
            sport = art.get("sport", "General")
            formatted_art = {
                "id": str(uuid.uuid4()),
                "title": art.get("title", "Untitled"),
                "url": art.get("url", "#"),
                "source": art.get("source", "Unknown"),
                "published_date": art.get(
                    "published_date", datetime.date.today().isoformat()
                ),
                "sport": sport,
                "summary": art.get("summary", art.get("text", ""))[:500],
                "keywords": art.get("keywords", [sport.lower()]),
                "importance_score": art.get("importance_score", 0.0),
                "credibility": art.get("credibility", 0.75),
            }
            formatted_articles.append(formatted_art)

        today = datetime.date.today()
        review_id = str(uuid.uuid4())
        now_iso = datetime.datetime.now().isoformat()

        review_data = {
            "id": review_id,
            "title": f"Daily Sports Review — {today.strftime('%B %d, %Y')}",
            "date": today.isoformat(),
            "generated_at": now_iso,
            # ── Structured Sections ──
            "sections": {
                "executive_summary": self._build_executive_summary(formatted_articles),
                "headlines": self._build_headlines_section(formatted_articles),
                "summaries": self._build_summaries_section(formatted_articles),
                "by_sport": self._build_sports_sections(formatted_articles),
                "trends": self._build_trends_section(formatted_articles),
                "top_sources": self._build_sources_section(formatted_articles),
                "keywords": self._build_keywords_section(formatted_articles),
            },
            # ── Legacy fields for backward compatibility ──
            "highlights": [a["title"] for a in formatted_articles[:5]],
            "top_headlines": [a["title"] for a in formatted_articles[:5]],
            "categories": self._build_sports_sections(formatted_articles),
            "articles": formatted_articles,
            # ── Metadata & statistics ──
            "metadata": {
                "total_articles": len(formatted_articles),
                "sources_count": len(
                    set(a.get("source", "") for a in formatted_articles)
                ),
                "categories_count": len(
                    set(a.get("sport", "") for a in formatted_articles)
                ),
                "avg_importance": round(
                    sum(a.get("importance_score", 0) for a in formatted_articles)
                    / max(len(formatted_articles), 1),
                    3,
                ),
                "avg_credibility": round(
                    sum(a.get("credibility", 0.75) for a in formatted_articles)
                    / max(len(formatted_articles), 1),
                    3,
                ),
            },
            "pdf_path": f"review_{today.isoformat()}.pdf",
        }
        return review_data

    # ──────────────────────────────────────────────────────
    # GENERATION PIPELINE
    # ──────────────────────────────────────────────────────

    def generate_review(self) -> Dict[str, Any]:
        """Generate structured review from REAL scraped and filtered data."""
        logger.info("=" * 60)
        logger.info("📰 STARTING INTELLIGENT REVIEW GENERATION PIPELINE")
        logger.info("=" * 60)

        logger.info("Step 1/3 — Fetching articles from live sources...")
        raw_articles = fetch_articles(fetch_full_text=True)

        if not raw_articles:
            logger.error("❌ No articles fetched from any source.")
            return {}

        logger.info(f"✅ Fetched {len(raw_articles)} articles")
        logger.info("Step 2/3 — Selecting and ranking top articles...")
        top_articles = self.select_top_articles(raw_articles, limit=25)

        logger.info("Step 3/3 — Structuring review into sections...")
        self._latest_review = self.format_review(top_articles)

        # Track history
        today = datetime.date.today().isoformat()
        self._review_cache[today] = self._latest_review
        self._generation_count += 1
        self._last_generated_at = datetime.datetime.now().isoformat()

        # Add to history (keep last 30)
        history_entry = {
            "id": self._latest_review["id"],
            "title": self._latest_review["title"],
            "date": self._latest_review["date"],
            "generated_at": self._latest_review["generated_at"],
            "total_articles": self._latest_review["metadata"]["total_articles"],
            "sources_count": self._latest_review["metadata"]["sources_count"],
            "categories_count": self._latest_review["metadata"]["categories_count"],
        }
        self._review_history.insert(0, history_entry)
        self._review_history = self._review_history[:30]

        total = self._latest_review.get("metadata", {}).get("total_articles", 0)
        cats = self._latest_review.get("metadata", {}).get("categories_count", 0)
        logger.info(f"✅ Review ready: {total} articles across {cats} categories")
        logger.info("=" * 60)

        return self._latest_review

    # ──────────────────────────────────────────────────────
    # GETTERS
    # ──────────────────────────────────────────────────────

    def get_latest_review(self) -> Optional[Dict[str, Any]]:
        """Get the cached latest review."""
        return self._latest_review

    def get_review_by_date(self, date_str: str) -> Optional[Dict[str, Any]]:
        """Get review for a specific date if cached."""
        return self._review_cache.get(date_str)

    def get_review_history(self) -> List[Dict[str, Any]]:
        """Get list of all generated reviews (metadata only)."""
        return self._review_history

    def get_generation_stats(self) -> Dict[str, Any]:
        """Get review generation statistics."""
        return {
            "total_generations": self._generation_count,
            "last_generated_at": self._last_generated_at,
            "cached_dates": list(self._review_cache.keys()),
            "history_count": len(self._review_history),
        }
