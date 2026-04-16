from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.core.security import decode_access_token
from backend.services.auth_service import AuthService

try:
    from backend.database.db import get_db as db_dependency
except ImportError:
    # Fallback dependency to keep imports valid until DB wiring is implemented.
    def db_dependency():
        raise RuntimeError("Database dependency backend.database.db.get_db is not configured.")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    db: Session = Depends(db_dependency),
    token: str = Depends(oauth2_scheme),
):
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    service = AuthService()
    return service.me(db, token)
