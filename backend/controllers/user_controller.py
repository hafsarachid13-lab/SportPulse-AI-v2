from sqlalchemy.orm import Session

from backend.schemas.user_schema import (
	UserActionResult,
	UserCreateRequest,
	UserImportResult,
	UserPasswordUpdateRequest,
	UserResponse,
	UserStatusUpdateRequest,
)
from backend.services.user_service import UserService


class UserController:
	def __init__(self, service: UserService | None = None) -> None:
		self.service = service or UserService()

	def list_users(self, db: Session) -> list[UserResponse]:
		return self.service.list_users(db)

	def create_user(self, db: Session, payload: UserCreateRequest) -> UserResponse:
		return self.service.create_user(db, payload)

	def delete_user(self, db: Session, user_id: int) -> UserActionResult:
		return self.service.delete_user(db, user_id)

	def update_user_password(self, db: Session, user_id: int, payload: UserPasswordUpdateRequest) -> UserActionResult:
		return self.service.update_user_password(db, user_id, payload)

	def update_user_status(self, db: Session, user_id: int, payload: UserStatusUpdateRequest) -> UserActionResult:
		return self.service.update_user_status(db, user_id, payload)

	def import_users_from_excel(self, db: Session, file_bytes: bytes, filename: str) -> UserImportResult:
		return self.service.import_users_from_excel(db, file_bytes, filename)

