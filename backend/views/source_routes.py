from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.controllers.source_controller import SourceController
from backend.database.db import get_db

router = APIRouter(prefix="/sources", tags=["sources"])
controller = SourceController()


@router.get("")
def get_sources(db: Session = Depends(get_db)):
    return {"sources": controller.list_sources(db)}
