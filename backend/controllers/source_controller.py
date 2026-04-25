from sqlalchemy.orm import Session
from backend.database.models import Source

class SourceController:
    def __init__(self):
        pass

    def list_sources(self, db: Session):
        """Récupère toutes les sources configurées."""
        return db.query(Source).all()
