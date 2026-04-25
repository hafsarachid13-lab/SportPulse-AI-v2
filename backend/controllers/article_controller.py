from sqlalchemy.orm import Session
from backend.database.models import Article

class ArticleController:
    def __init__(self):
        pass

    def list_articles(self, db: Session):
        """Récupère la liste de tous les articles de la base de données."""
        return db.query(Article).order_by(Article.collected_at.desc()).all()

    def get_article(self, db: Session, article_id: int):
        """Récupère un article spécifique par son ID."""
        return db.query(Article).filter(Article.id == article_id).first()
