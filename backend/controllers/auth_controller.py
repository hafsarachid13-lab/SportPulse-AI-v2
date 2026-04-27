from sqlalchemy.orm import Session

from backend.schemas.auth import AuthUser, LoginRequest, RegisterRequest, TokenResponse
from backend.services.auth_service import AuthService


class AuthController:
    def __init__(self, service: AuthService | None = None) -> None:
        self.service = service or AuthService()

    def register(self, db: Session, payload: RegisterRequest) -> AuthUser:
        return self.service.register(db, payload)

    def login(self, db: Session, payload: LoginRequest) -> TokenResponse:
        return self.service.login(db, payload)

    def me(self, db: Session, token: str) -> AuthUser:
        return self.service.me(db, token)

    def logout(self, token: str) -> dict:
        return self.service.logout(token)
