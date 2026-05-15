from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.controllers.source_controller import SourceController, SourceCreateRequest, SourceValidateRequest
from backend.database.db import get_db

router = APIRouter(prefix="/sources", tags=["sources"])
controller = SourceController()


@router.get("")
def get_sources(db: Session = Depends(get_db)):
    return controller.list_sources(db)

@router.post("")
def add_source(data: SourceCreateRequest, db: Session = Depends(get_db)):
    return controller.add_source(data, db)

@router.delete("/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    return controller.delete_source(source_id, db)

@router.patch("/{source_id}/toggle")
def toggle_source(source_id: int, db: Session = Depends(get_db)):
    return controller.toggle_source(source_id, db)

@router.post("/validate")
def validate_source(data: SourceValidateRequest):
    return controller.validate_source(data)
