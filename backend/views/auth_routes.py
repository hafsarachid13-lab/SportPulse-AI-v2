from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.dependencies import get_current_user, get_optional_bearer_token
from backend.controllers.auth_controller import AuthController
from backend.database.db import get_db
from backend.schemas.auth import AuthUser, LoginRequest, RegisterRequest, TokenResponse


router = APIRouter(prefix="/auth", tags=["auth"])
controller = AuthController()


@router.get("/roles")
def list_roles():
    return {
        "roles": ["admin", "journaliste"],
    }


@router.post("/register", response_model=AuthUser)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    return controller.register(db, payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return controller.login(db, payload)


@router.get("/me", response_model=AuthUser)
def me(current_user: AuthUser = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(token: str | None = Depends(get_optional_bearer_token)):
    if not token:
        return {"message": "Logout successful"}
    return controller.logout(token)
