from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.controllers.review_controller import ReviewController
from backend.database.db import get_db

router = APIRouter(prefix="/review", tags=["review"])
controller = ReviewController()


@router.get("/today")
def get_today_review(db: Session = Depends(get_db)):
    return controller.get_today_review(db)
