"""
Dashboard Analytics Service — Person 5 Module (Upgraded)
Provides KPI metrics, charts data, trending analysis, filtering capabilities,
review timeline, and export history analytics for the press review dashboard.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


class DashboardService:
    """Aggregates analytics and KPI data from reviews and articles."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._cached_stats = {}
        self._cache_timestamp = None
        self._cache_ttl_seconds = 300  # 5 minute cache
        self._initialized = True

    def _is_cache_valid(self) -> bool:
        """Check if cached data is still valid."""
        if not self._cache_timestamp:
            return False
        age = (datetime.now() - self._cache_timestamp).total_seconds()
        return age < self._cache_ttl_seconds

    # ──────────────────────────────────────────────────────
    # KPI CARDS
    # ──────────────────────────────────────────────────────

    def get_kpi_cards(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate KPI card data for dashboard display."""
        if not articles:
            return {
                "total_articles": 0,
                "active_sources": 0,
                "avg_credibility": 0.0,
                "avg_importance": 0.0,
                "top_sport": "N/A",
                "high_importance_count": 0,
                "categories_count": 0,
            }

        sources = set(a.get("source", "Unknown") for a in articles)
        sports = Counter(a.get("sport", "General") for a in articles)
        importance_scores = [a.get("importance_score", 0.5) for a in articles]
        credibility_scores = [a.get("credibility", 0.75) for a in articles]

        return {
            "total_articles": len(articles),
            "active_sources": len(sources),
            "avg_credibility": round(
                sum(credibility_scores) / len(credibility_scores), 3
            ),
            "avg_importance": round(
                sum(importance_scores) / len(importance_scores), 3
            ),
            "top_sport": sports.most_common(1)[0][0] if sports else "General",
            "high_importance_count": len(
                [s for s in importance_scores if s >= 0.7]
            ),
            "categories_count": len(sports),
        }

    # ──────────────────────────────────────────────────────
    # ARTICLE VOLUME STATS
    # ──────────────────────────────────────────────────────

    def get_article_volume_stats(
        self,
        articles: List[Dict[str, Any]],
        time_window: str = "today",
    ) -> Dict[str, Any]:
        """Generate article volume statistics over time."""
        if not articles:
            return {
                "total": 0,
                "by_hour": {},
                "by_source": {},
                "trend": "stable",
            }

        by_source = Counter(a.get("source", "Unknown") for a in articles)

        by_hour: Dict[str, int] = defaultdict(int)
        for article in articles:
            try:
                pub_date = article.get("published_date", "")
                if pub_date:
                    day = pub_date.split("T")[0] if "T" in pub_date else pub_date
                    by_hour[day] += 1
            except Exception:
                pass

        return {
            "total": len(articles),
            "by_source": dict(by_source.most_common(10)),
            "by_hour": dict(sorted(by_hour.items())),
            "time_window": time_window,
            "trend": "increasing" if len(articles) > 5 else "stable",
        }

    # ──────────────────────────────────────────────────────
    # SOURCE DISTRIBUTION
    # ──────────────────────────────────────────────────────

    def get_source_distribution(
        self, articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate source distribution analytics for charts."""
        if not articles:
            return {
                "total_sources": 0,
                "sources": [],
                "avg_articles_per_source": 0,
            }

        sources_count = Counter(a.get("source", "Unknown") for a in articles)

        sources_data = []
        for source, count in sources_count.most_common(15):
            source_articles = [a for a in articles if a.get("source") == source]
            avg_cred = (
                sum(a.get("credibility", 0.75) for a in source_articles)
                / len(source_articles)
            )
            avg_imp = (
                sum(a.get("importance_score", 0.5) for a in source_articles)
                / len(source_articles)
            )

            sources_data.append({
                "name": source,
                "article_count": count,
                "avg_credibility": round(avg_cred, 3),
                "avg_importance": round(avg_imp, 3),
                "percentage": round((count / len(articles)) * 100, 1),
            })

        return {
            "total_sources": len(sources_count),
            "sources": sources_data,
            "avg_articles_per_source": (
                round(len(articles) / len(sources_count), 1) if sources_count else 0
            ),
        }

    # ──────────────────────────────────────────────────────
    # TRENDING TOPICS
    # ──────────────────────────────────────────────────────

    def get_trending_topics(
        self, articles: List[Dict[str, Any]], top_k: int = 15
    ) -> Dict[str, Any]:
        """Extract trending topics and keywords from articles."""
        if not articles:
            return {
                "trending_keywords": [],
                "trending_entities": [],
                "total_unique_keywords": 0,
            }

        keyword_freq: Counter = Counter()
        entities: Counter = Counter()

        for article in articles:
            # Use pre-extracted keywords from NLP (Person 3)
            keywords = article.get("keywords", [])
            if isinstance(keywords, list):
                for kw in keywords:
                    if isinstance(kw, str) and len(kw) > 2:
                        keyword_freq[kw.lower()] += 1

            # Extract from title (entities)
            title = article.get("title", "").lower()
            words = title.split()
            for word in words:
                clean_word = word.strip(".,;:!?\"'()")
                if len(clean_word) > 4 and clean_word not in {
                    "sports", "today", "match", "game", "news",
                    "about", "their", "after", "which", "could",
                }:
                    entities[clean_word] += 1

        trending_keywords = [
            {"keyword": k, "frequency": v}
            for k, v in keyword_freq.most_common(top_k)
        ]

        trending_entities = [
            {"entity": e, "mentions": v}
            for e, v in entities.most_common(top_k)
        ]

        return {
            "trending_keywords": trending_keywords,
            "trending_entities": trending_entities,
            "total_unique_keywords": len(keyword_freq),
        }

    # ──────────────────────────────────────────────────────
    # SPORT ANALYTICS
    # ──────────────────────────────────────────────────────

    def get_sport_analytics(
        self, articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate sport category analytics."""
        if not articles:
            return {"total_sports": 0, "sports": [], "distribution": {}}

        sports_count = Counter(a.get("sport", "General") for a in articles)

        sports_data = []
        for sport, count in sports_count.most_common():
            sport_articles = [a for a in articles if a.get("sport") == sport]
            avg_importance = (
                sum(a.get("importance_score", 0.5) for a in sport_articles)
                / len(sport_articles)
            )

            sports_data.append({
                "sport": sport,
                "article_count": count,
                "percentage": round((count / len(articles)) * 100, 1),
                "avg_importance": round(avg_importance, 3),
                "top_sources": [
                    list(item)
                    for item in Counter(
                        a.get("source", "Unknown") for a in sport_articles
                    ).most_common(3)
                ],
            })

        return {
            "total_sports": len(sports_count),
            "sports": sports_data,
            "distribution": dict(sports_count),
        }

    # ──────────────────────────────────────────────────────
    # CREDIBILITY METRICS
    # ──────────────────────────────────────────────────────

    def get_credibility_metrics(
        self, articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate credibility and quality metrics."""
        if not articles:
            return {
                "avg_credibility": 0.0,
                "distribution": {"high": 0, "medium": 0, "low": 0},
                "sources_by_credibility": [],
            }

        credibility_scores = [a.get("credibility", 0.75) for a in articles]
        avg_cred = sum(credibility_scores) / len(credibility_scores)

        distribution = {
            "high": len([s for s in credibility_scores if s >= 0.8]),
            "medium": len([s for s in credibility_scores if 0.5 <= s < 0.8]),
            "low": len([s for s in credibility_scores if s < 0.5]),
        }

        sources: Dict[str, Dict] = defaultdict(
            lambda: {"count": 0, "avg_credibility": 0}
        )
        for article in articles:
            source = article.get("source", "Unknown")
            sources[source]["count"] += 1
            sources[source]["avg_credibility"] += article.get("credibility", 0.75)

        sources_by_credibility = [
            {
                "source": s,
                "avg_credibility": round(
                    data["avg_credibility"] / data["count"], 3
                ),
                "article_count": data["count"],
            }
            for s, data in sorted(
                sources.items(),
                key=lambda x: x[1]["avg_credibility"] / x[1]["count"],
                reverse=True,
            )
        ]

        return {
            "avg_credibility": round(avg_cred, 3),
            "distribution": distribution,
            "sources_by_credibility": sources_by_credibility[:10],
        }

    # ──────────────────────────────────────────────────────
    # IMPORTANCE METRICS
    # ──────────────────────────────────────────────────────

    def get_importance_metrics(
        self, articles: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate importance score analytics."""
        if not articles:
            return {
                "avg_importance": 0.0,
                "distribution": {"high": 0, "medium": 0, "low": 0},
                "range": {"min": 0, "max": 0},
            }

        importance_scores = [a.get("importance_score", 0.5) for a in articles]
        avg_imp = sum(importance_scores) / len(importance_scores)

        distribution = {
            "high": len([s for s in importance_scores if s >= 0.7]),
            "medium": len([s for s in importance_scores if 0.4 <= s < 0.7]),
            "low": len([s for s in importance_scores if s < 0.4]),
        }

        return {
            "avg_importance": round(avg_imp, 3),
            "distribution": distribution,
            "range": {
                "min": round(min(importance_scores), 3) if importance_scores else 0,
                "max": round(max(importance_scores), 3) if importance_scores else 1,
            },
        }

    # ──────────────────────────────────────────────────────
    # FILTERS DATA
    # ──────────────────────────────────────────────────────

    def get_filters_data(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get available filter options."""
        if not articles:
            return {
                "available_sources": [],
                "available_sports": [],
                "date_range": {"min": "", "max": ""},
                "credibility_range": {"min": 0, "max": 1},
            }

        sources = sorted(set(a.get("source", "Unknown") for a in articles))
        sports = sorted(set(a.get("sport", "General") for a in articles))

        dates: List[str] = []
        for article in articles:
            date = article.get("published_date", "")
            if date:
                dates.append(date.split("T")[0] if "T" in date else date)
        dates = sorted(set(dates))

        credibility_scores = [a.get("credibility", 0.75) for a in articles]

        return {
            "available_sources": sources,
            "available_sports": sports,
            "date_range": {
                "min": dates[0] if dates else "",
                "max": dates[-1] if dates else "",
            },
            "credibility_range": {
                "min": round(min(credibility_scores), 3) if credibility_scores else 0,
                "max": round(max(credibility_scores), 3) if credibility_scores else 1,
            },
        }

    # ──────────────────────────────────────────────────────
    # COMPLETE DASHBOARD DATA
    # ──────────────────────────────────────────────────────

    def get_dashboard_data(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete dashboard data from a review."""
        articles = review_data.get("articles", [])

        logger.info(
            f"Generating dashboard data for {len(articles)} articles..."
        )

        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "article_count": len(articles),
            # KPI Cards
            "kpis": self.get_kpi_cards(articles),
            # Charts data
            "article_volume": self.get_article_volume_stats(articles),
            "source_distribution": self.get_source_distribution(articles),
            "sport_analytics": self.get_sport_analytics(articles),
            # Analytics
            "trending": self.get_trending_topics(articles),
            "credibility": self.get_credibility_metrics(articles),
            "importance": self.get_importance_metrics(articles),
            # Filters
            "filters": self.get_filters_data(articles),
            # Summary
            "summary": {
                "generated_date": review_data.get("date", ""),
                "total_sources": review_data.get("metadata", {}).get(
                    "sources_count", 0
                ),
                "total_categories": review_data.get("metadata", {}).get(
                    "categories_count", 0
                ),
            },
        }

        return dashboard_data

    # ──────────────────────────────────────────────────────
    # FILTER ARTICLES
    # ──────────────────────────────────────────────────────

    def filter_articles(
        self,
        articles: List[Dict[str, Any]],
        source: Optional[str] = None,
        sport: Optional[str] = None,
        min_credibility: float = 0.0,
        min_importance: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Filter articles by multiple criteria."""
        filtered = articles

        if source:
            filtered = [a for a in filtered if a.get("source") == source]

        if sport:
            filtered = [a for a in filtered if a.get("sport") == sport]

        if min_credibility > 0:
            filtered = [
                a for a in filtered
                if a.get("credibility", 0.75) >= min_credibility
            ]

        if min_importance > 0:
            filtered = [
                a for a in filtered
                if a.get("importance_score", 0.5) >= min_importance
            ]

        return filtered
