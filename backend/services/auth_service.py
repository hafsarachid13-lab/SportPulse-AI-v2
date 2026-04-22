from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.core.security import create_access_token, hash_password, verify_password
from backend.services.email_service import EmailService
from backend.services.token_blacklist_service import TokenBlacklistService
from backend.repositories.user_repo import UserRepository
from backend.schemas.auth import AuthUser, LoginRequest, RegisterRequest, TokenResponse


class AuthService:
	def __init__(self, user_repo: UserRepository | None = None) -> None:
		self.user_repo = user_repo or UserRepository()
		self.email_service = EmailService()

	def register(self, db: Session, payload: RegisterRequest) -> AuthUser:
		existing = self.user_repo.get_by_email(db, payload.email)
		if existing is not None:
			raise HTTPException(
				status_code=status.HTTP_409_CONFLICT,
				detail="Email already registered",
			)

		if payload.username and self.user_repo.get_by_username(db, payload.username):
			raise HTTPException(
				status_code=status.HTTP_409_CONFLICT,
				detail="Username already taken",
			)

		user = self.user_repo.create(
			db,
			email=payload.email,
			password_hash=hash_password(payload.password),
			username=payload.username,
			role=payload.role,
		)
		self.email_service.send_account_created_email(
			to_email=user.email,
			username=user.username,
			role=user.role,
			plain_password=payload.password,
		)
		return self._to_auth_user(user)

	def login(self, db: Session, payload: LoginRequest) -> TokenResponse:
		identifier = (payload.email or payload.username or payload.login or payload.identifier or "").strip()
		if not identifier:
			raise HTTPException(
				status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
				detail="Provide one of: email, username, login, or identifier",
			)

		if "@" in identifier:
			user = self.user_repo.get_by_email(db, identifier)
		else:
			user = self.user_repo.get_by_username(db, identifier)

		if user is None or not verify_password(payload.password, user.password_hash):
			raise HTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED,
				detail="Invalid credentials",
			)

		if not user.is_active:
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail="Inactive account",
			)

		expires_delta = timedelta(days=30) if payload.remember_me else None
		token = create_access_token(subject=str(user.id), expires_delta=expires_delta)
		return TokenResponse(access_token=token)

	def me(self, db: Session, token: str) -> AuthUser:
		from backend.core.security import decode_access_token

		if TokenBlacklistService.is_revoked(token):
			raise HTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED,
				detail="Token has been revoked",
			)

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

		if not user.is_active:
			raise HTTPException(
				status_code=status.HTTP_403_FORBIDDEN,
				detail="Inactive account",
			)

		return self._to_auth_user(user)

	def logout(self, token: str) -> dict:
		TokenBlacklistService.revoke(token)
		return {"message": "Logout successful"}

	@staticmethod
	def _to_auth_user(user) -> AuthUser:
		return AuthUser(
			id=user.id,
			username=user.username,
			email=user.email,
			role=user.role,
			is_active=user.is_active,
		)

