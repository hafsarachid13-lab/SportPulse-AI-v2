from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.controllers.auth_controller import AuthController
from backend.schemas.auth import AuthUser, LoginRequest, RegisterRequest, TokenResponse

try:
    from backend.database.db import get_db
except ImportError:
    def get_db():
        raise RuntimeError("Database dependency backend.database.db.get_db is not configured.")


router = APIRouter(prefix="/auth", tags=["auth"])
controller = AuthController()


@router.get("/roles")
def list_roles():
    return {
        "roles": ["Super Admin", "Admin", "Journalist", "Student"],
    }


@router.post("/register", response_model=AuthUser)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    return controller.register(db, payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return controller.login(db, payload)
