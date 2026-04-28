from ..services.scraper_service import collect_all_articles
from typing import List, Dict

def collect_articles() -> List[Dict]:
    """
    Lance la collecte globale des articles sportifs.
    Limit_per_source est fixé à 3 pour éviter les temps de traitement trop longs en démo.
    """
    print("[COLLECTOR] Début de la collecte multi-sources...")
    articles = collect_all_articles(limit_per_source=3)
    print(f"[COLLECTOR] Fin de la collecte. {len(articles)} articles récupérés.")
    return articles