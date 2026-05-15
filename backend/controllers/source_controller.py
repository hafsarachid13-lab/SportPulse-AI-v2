from sqlalchemy.orm import Session
from backend.database.models import Source, CollectJob, SourceType
from backend.services.scraper_service import validate_source_url
from pydantic import BaseModel
from fastapi import HTTPException
from typing import Optional

class SourceCreateRequest(BaseModel):
    name: str
    url: str
    sport: Optional[str] = None
    type: Optional[str] = "scraping"

class SourceValidateRequest(BaseModel):
    url: str

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
                "sport": "Football" # Par défaut
            })
        return results

    def add_source(self, data: SourceCreateRequest, db: Session):
        new_source = Source(
            name=data.name,
            url=data.url,
            type=SourceType.RSS.value if data.type and data.type.lower() == 'rss' else SourceType.SCRAPING.value,
            fiability_score=0.75, # Valeur par défaut
            is_active=True
        )
        db.add(new_source)
        db.commit()
        db.refresh(new_source)
        return {"message": "Source ajoutée avec succès", "id": new_source.id}

    def delete_source(self, source_id: int, db: Session):
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="Source introuvable")
        db.delete(source)
        db.commit()
        return {"message": "Source supprimée"}

    def toggle_source(self, source_id: int, db: Session):
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            raise HTTPException(status_code=404, detail="Source introuvable")
        source.is_active = not source.is_active
        db.commit()
        return {"message": "Statut de la source mis à jour", "is_active": source.is_active}

    def validate_source(self, data: SourceValidateRequest):
        return validate_source_url(data.url)
