from sqlalchemy.orm import Session
from backend.database.models import Source, CollectJob

class SourceController:
    def __init__(self):
        pass

    def list_sources(self, db: Session):
        """Récupère toutes les sources configurées avec leurs statistiques."""
        sources = db.query(Source).all()
        results = []
        for s in sources:
            # Compter les articles
            articles_count = len(s.articles)
            
            # Trouver la dernière date de collecte
            last_job = (
                db.query(CollectJob)
                .filter(CollectJob.source_id == s.id)
                .order_by(CollectJob.finished_at.desc())
                .first()
            )
            last_collected = last_job.finished_at.isoformat() if last_job and last_job.finished_at else "Jamais"
            
            results.append({
                "id": s.id,
                "name": s.name,
                "url": s.url,
                "type": s.type,
                "fiability_score": s.fiability_score,
                "is_active": s.is_active,
                "articles_count": articles_count,
                "last_collected_at": last_collected,
                "sport": "Football" # Par défaut ou à extraire si possible
            })
        return results
