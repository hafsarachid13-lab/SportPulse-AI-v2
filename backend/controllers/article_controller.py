from sqlalchemy.orm import Session
from backend.database.models import Article

class ArticleController:
    def __init__(self):
        pass

    def list_articles(self, db: Session, today: bool = False):
        """Récupère la liste des articles avec leurs sources, strictement filtrée pour aujourd'hui si demandé."""
        from sqlalchemy.orm import joinedload
        from datetime import date, datetime, time
        
        query = db.query(Article).options(joinedload(Article.source))
        
        if today:
            # On définit le début de la journée d'aujourd'hui (00:00:00)
            today_start = datetime.combine(date.today(), time.min)
            # On prend les articles collectés aujourd'hui qui sont soit publiés aujourd'hui, soit sans date
            query = query.filter(Article.collected_at >= today_start).filter(
                (Article.published_at >= today_start) | (Article.published_at == None)
            )
            
        return query.order_by(Article.published_at.desc(), Article.collected_at.desc()).all()

    def get_article(self, db: Session, article_id: int):
        """Récupère un article spécifique par son ID."""
        return db.query(Article).filter(Article.id == article_id).first()
