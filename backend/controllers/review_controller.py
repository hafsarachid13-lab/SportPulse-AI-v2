from sqlalchemy.orm import Session
from backend.database.models import RevueDePresse

class ReviewController:
    def __init__(self):
        pass

    def list_reviews(self, db: Session):
        """Récupère les revues de presse générées."""
        return db.query(RevueDePresse).order_by(RevueDePresse.date.desc()).all()

    def get_today_review(self, db: Session):
        """Récupère la revue de presse la plus récente."""
        from datetime import date
        return db.query(RevueDePresse).filter(RevueDePresse.date == date.today()).first()
