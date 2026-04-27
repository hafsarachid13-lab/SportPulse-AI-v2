from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.database.db import get_db as db_dependency
from backend.core.security import decode_access_token
from backend.services.auth_service import AuthService
from backend.services.token_blacklist_service import TokenBlacklistService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _extract_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "").strip()
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    x_access_token = request.headers.get("X-Access-Token", "").strip()
    if x_access_token:
        return x_access_token

    cookie_token = request.cookies.get("access_token", "").strip()
    if cookie_token.lower().startswith("bearer "):
        return cookie_token[7:].strip()
    if cookie_token:
        return cookie_token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication token",
    )


def get_bearer_token(request: Request) -> str:
    return _extract_token(request)


def get_optional_bearer_token(request: Request) -> str | None:
    try:
        return _extract_token(request)
    except HTTPException:
        return None


def get_current_user(
    db: Session = Depends(db_dependency),
    token: str = Depends(get_bearer_token),
):
    if TokenBlacklistService.is_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    service = AuthService()
    return service.me(db, token)
