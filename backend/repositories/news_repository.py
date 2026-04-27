"""
News Repository — Person 5 Module
Data access layer for articles and sources.

Convention: plug in your actual DB session where marked.
The mock data provides a realistic fallback for development.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mock data — replace with real DB models once your ORM is wired up
# ---------------------------------------------------------------------------

def _today_offset(days: int) -> str:
    dt = datetime.now() - timedelta(days=days)
    return dt.strftime("%Y-%m-%d %H:%M")


_MOCK_SOURCES = [
    {"id": 1, "name": "L'Équipe", "url": "https://lequipe.fr", "category": "Football", "active": True},
    {"id": 2, "name": "RMC Sport", "url": "https://rmcsport.bfmtv.com", "category": "General", "active": True},
    {"id": 3, "name": "Eurosport", "url": "https://eurosport.fr", "category": "General", "active": True},
    {"id": 4, "name": "France Football", "url": "https://francefootball.fr", "category": "Football", "active": True},
    {"id": 5, "name": "Sport24", "url": "https://sport24.lefigaro.fr", "category": "General", "active": True},
]

_MOCK_ARTICLES = [
    {
        "id": 1, "title": "PSG Dominates Ligue 1 with a Record 5-0 Win",
        "source": "L'Équipe", "category": "Football",
        "summary": "Paris Saint-Germain recorded their biggest win of the season last night, "
                   "thrashing Lyon 5-0 at the Parc des Princes. Mbappé scored a hat-trick in a dominant display.",
        "url": "https://lequipe.fr/psg-lyon", "published_at": _today_offset(0),
    },
    {
        "id": 2, "title": "Champions League Draw: French Clubs Face Tough Tests",
        "source": "RMC Sport", "category": "Football",
        "summary": "The Champions League quarter-final draw placed PSG against Real Madrid while Marseille "
                   "will face Bayern Munich. Analysts predict high-intensity encounters.",
        "url": "https://rmcsport.bfmtv.com/cl-draw", "published_at": _today_offset(0),
    },
    {
        "id": 3, "title": "Roland-Garros 2026: Nadal Announces Comeback",
        "source": "Eurosport", "category": "Tennis",
        "summary": "Rafael Nadal has confirmed his participation at Roland-Garros 2026, "
                   "marking a historic comeback on the clay courts where he has won 14 titles.",
        "url": "https://eurosport.fr/nadal-rg2026", "published_at": _today_offset(1),
    },
    {
        "id": 4, "title": "Tour de France Route Unveiled: 21 Demanding Stages",
        "source": "France Football", "category": "Cycling",
        "summary": "The 2026 Tour de France organisers unveiled a route featuring four high-altitude finishes "
                   "in the Alps and three Pyrenean stages, promising an epic battle for the yellow jersey.",
        "url": "https://francefootball.fr/tdf2026", "published_at": _today_offset(0),
    },
    {
        "id": 5, "title": "NBA Finals Preview: Celtics vs. Thunder",
        "source": "Sport24", "category": "Basketball",
        "summary": "The NBA Finals tip off this weekend as the Boston Celtics face the Oklahoma City Thunder. "
                   "Both teams enter on 12-game winning streaks in an era-defining championship clash.",
        "url": "https://sport24.lefigaro.fr/nba-finals", "published_at": _today_offset(0),
    },
    {
        "id": 6, "title": "Formula 1: Verstappen Claims Monaco Pole",
        "source": "Eurosport", "category": "Formula 1",
        "summary": "Max Verstappen secured pole position for the Monaco Grand Prix with a stunning lap, "
                   "0.3 seconds ahead of Ferrari's Leclerc in front of his home crowd.",
        "url": "https://eurosport.fr/f1-monaco", "published_at": _today_offset(1),
    },
]


# Patch forward-reference in mock data
for _a in _MOCK_ARTICLES:
    if callable(_a.get("published_at")):
        _a["published_at"] = _a["published_at"]()  # type: ignore


class _ArticleObj:
    """Thin wrapper to expose dict fields as attributes (mirrors ORM object interface)."""
    __slots__ = ("id", "title", "source", "category", "summary", "description", "url", "published_at")

    def __init__(self, data: dict):
        for key in self.__slots__:
            setattr(self, key, data.get(key))
        self.description = data.get("summary")  # alias


class _SourceObj:
    __slots__ = ("id", "name", "url", "category", "active")

    def __init__(self, data: dict):
        for key in self.__slots__:
            setattr(self, key, data.get(key))


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

class NewsRepository:
    """
    Data access layer for articles and sources.

    ── HOW TO WIRE UP YOUR DB ────────────────────────────────────────────────
    1. Import your SQLAlchemy Session (or AsyncSession) at the top.
    2. Replace each method body with:
         return db.query(Article).filter(...).offset(offset).limit(limit).all()
    3. Remove the mock data block above.
    ─────────────────────────────────────────────────────────────────────────
    """

    def get_articles(
        self,
        limit: int = 20,
        offset: int = 0,
        source: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[_ArticleObj]:
        """Fetch articles with optional filters."""
        # ── REAL DB EXAMPLE ─────────────────────────────────────────
        # query = db.query(Article)
        # if source:
        #     query = query.filter(Article.source == source)
        # if category:
        #     query = query.filter(Article.category == category)
        # return query.order_by(Article.published_at.desc()).offset(offset).limit(limit).all()
        # ────────────────────────────────────────────────────────────

        data = list(_MOCK_ARTICLES)
        if source:
            data = [a for a in data if a.get("source", "").lower() == source.lower()]
        if category:
            data = [a for a in data if a.get("category", "").lower() == category.lower()]

        paginated = data[offset: offset + limit]
        result = [_ArticleObj(a) for a in paginated]
        logger.debug(f"get_articles → {len(result)} rows")
        return result

    def get_sources(self) -> List[_SourceObj]:
        """Fetch all sources."""
        # ── REAL DB EXAMPLE ─────────────────────────────────────────
        # return db.query(Source).filter(Source.active == True).all()
        # ────────────────────────────────────────────────────────────

        result = [_SourceObj(s) for s in _MOCK_SOURCES]
        logger.debug(f"get_sources → {len(result)} rows")
        return result