from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.core.security import create_access_token, hash_password, verify_password
from backend.repositories.user_repo import UserRepository
from backend.schemas.auth import AuthUser, LoginRequest, RegisterRequest, TokenResponse


class AuthService:
	def __init__(self, user_repo: UserRepository | None = None) -> None:
		self.user_repo = user_repo or UserRepository()

	def register(self, db: Session, payload: RegisterRequest) -> AuthUser:
		existing = self.user_repo.get_by_email(db, payload.email)
		if existing is not None:
			raise HTTPException(
				status_code=status.HTTP_409_CONFLICT,
				detail="Email already registered",
			)

		user = self.user_repo.create(
			db,
			email=payload.email,
			password_hash=hash_password(payload.password),
			full_name=payload.full_name,
			role=payload.role,
		)
		return self._to_auth_user(user)

	def login(self, db: Session, payload: LoginRequest) -> TokenResponse:
		user = self.user_repo.get_by_email(db, payload.email)
		if user is None or not verify_password(payload.password, user.password_hash):
			raise HTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED,
				detail="Invalid email or password",
			)

		token = create_access_token(subject=str(user.id))
		return TokenResponse(access_token=token)

	def me(self, db: Session, token: str) -> AuthUser:
		from backend.core.security import decode_access_token

		payload = decode_access_token(token)
		if payload is None or "sub" not in payload:
			raise HTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED,
				detail="Invalid or expired token",
			)

		user_id = int(payload["sub"])
		user = self.user_repo.get_by_id(db, user_id)
		if user is None:
			raise HTTPException(
				status_code=status.HTTP_404_NOT_FOUND,
				detail="User not found",
			)

		return self._to_auth_user(user)

	@staticmethod
	def _to_auth_user(user) -> AuthUser:
		return AuthUser(
			id=user.id,
			email=user.email,
			full_name=user.full_name,
			role=user.role,
			is_active=user.is_active,
		)

