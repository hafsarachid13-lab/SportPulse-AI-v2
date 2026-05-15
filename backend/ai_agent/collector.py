from ..services.scraper_service import process_source
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def collect_articles() -> List[Dict]:
    """
    Lance la collecte globale des articles sportifs depuis les sources en DB.
    """
    from ..database.db import SessionLocal
    from ..database.models import Source, CollectJob
    from datetime import datetime

    logger.info("[COLLECTOR] Début de la collecte multi-sources via DB...")
    db = SessionLocal()
    all_articles = []
    
    try:
        # Récupérer uniquement les sources actives
        sources = db.query(Source).filter(Source.is_active == True).all()
        
        if not sources:
            logger.warning("[COLLECTOR] Aucune source active trouvée en base de données.")
            return []

        for source in sources:
            # 1. Créer le CollectJob
            job = CollectJob(source_id=source.id, status="running")
            db.add(job)
            db.commit()

            try:
                # 2. Préparer le dictionnaire source attendu par process_source
                source_dict = {
                    "name": source.name,
                    "url": source.url,
                    "type": source.type,
                    "lang": "fr", # Défaut
                    "credibility": (source.fiability_score or 0.75) * 100
                }
                
                # 3. Collecter les articles
                articles_found = process_source(source_dict, limit_per_source=3)
                
                # Ajouter l'ID de la source et la langue pour le pipeline
                for art in articles_found:
                    art["source_id"] = source.id
                    art["language"] = source_dict["lang"]
                    
                all_articles.extend(articles_found)
                
                # 4. Mettre à jour le CollectJob avec succès
                job.status = "success"
                job.articles_collected = len(articles_found)
                
            except Exception as e:
                logger.error(f"[COLLECTOR] Erreur lors de la collecte pour {source.name}: {e}")
                # 4. Mettre à jour le CollectJob avec échec
                job.status = "failed"
                job.error_message = str(e)[:250]
            
            job.finished_at = datetime.now()
            db.commit()
            
    finally:
        db.close()
        
    logger.info(f"[COLLECTOR] Fin de la collecte. {len(all_articles)} articles récupérés au total.")
    return all_articles