from ..services.scraper_service import fetch_articles
from typing import List, Dict

def collect_articles() -> List[Dict]:
    """
    Lance la collecte globale des articles sportifs.
    Limit_per_source est fixé à 3 pour éviter les temps de traitement trop longs en démo.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info("[COLLECTOR] Début de la collecte multi-sources...")
    articles = fetch_articles(limit_per_source=3)
    logger.info(f"[COLLECTOR] Fin de la collecte. {len(articles)} articles récupérés.")
    return articles