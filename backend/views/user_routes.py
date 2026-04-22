from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from backend.controllers.user_controller import UserController
from backend.database.db import get_db
from backend.schemas.user_schema import (
	UserActionResult,
	UserCreateRequest,
	UserImportResult,
	UserPasswordUpdateRequest,
	UserResponse,
	UserStatusUpdateRequest,
)


router = APIRouter(prefix="/users", tags=["users"])
controller = UserController()


@router.get("", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
	return controller.list_users(db)


@router.post("", response_model=UserResponse)
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db)):
	return controller.create_user(db, payload)


@router.delete("/{user_id}", response_model=UserActionResult)
def delete_user(user_id: int, db: Session = Depends(get_db)):
	return controller.delete_user(db, user_id)


@router.patch("/{user_id}/password", response_model=UserActionResult)
def update_user_password(user_id: int, payload: UserPasswordUpdateRequest, db: Session = Depends(get_db)):
	return controller.update_user_password(db, user_id, payload)


@router.patch("/{user_id}/status", response_model=UserActionResult)
def update_user_status(user_id: int, payload: UserStatusUpdateRequest, db: Session = Depends(get_db)):
	return controller.update_user_status(db, user_id, payload)


@router.post("/import-excel", response_model=UserImportResult)
async def import_users_from_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
	file_bytes = await file.read()
	return controller.import_users_from_excel(db, file_bytes, file.filename or "users.xlsx")

