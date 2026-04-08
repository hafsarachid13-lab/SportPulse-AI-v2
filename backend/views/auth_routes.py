from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/roles")
def list_roles():
    return {
        "roles": ["Super Admin", "Admin", "Journalist", "Student"],
    }
