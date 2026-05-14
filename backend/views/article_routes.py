from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.controllers.article_controller import ArticleController
from backend.database.db import get_db

router = APIRouter(prefix="/articles", tags=["articles"])
controller = ArticleController()


@router.get("")
def get_articles(today: bool = False, db: Session = Depends(get_db)):
    return {"articles": controller.list_articles(db, today=today)}
