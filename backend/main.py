from __future__ import annotations

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from backend.config import get_settings
from backend.ai_main import router as ai_router
from backend.views.auth_routes import router as auth_router
from backend.views.user_routes import router as user_router

from backend.controllers.review_controller import router as review_router
from backend.views.review_routes import router as legacy_routes

# ── Logging ─────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="FastAPI backend for AI-assisted news review.",
    )

    # ── CORS FIX ────────────────────────────────────────
    # Keeping settings from config but ensuring frontend compatibility
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins or ["*"],
        allow_origin_regex=settings.cors_allow_origin_regex,
        allow_credentials=settings.cors_allow_credentials if settings.cors_allow_credentials is not None else True,
        allow_methods=settings.cors_allow_methods or ["*"],
        allow_headers=settings.cors_allow_headers or ["*"],
    )

    # ── Static folder for PDFs ─────────────────────────
    BASE_DIR = os.path.dirname(__file__)
    STATIC_PDF_DIR = os.path.join(BASE_DIR, "static_pdfs")
    os.makedirs(STATIC_PDF_DIR, exist_ok=True)
    app.mount("/static", StaticFiles(directory=STATIC_PDF_DIR), name="static")

    # ── Include new routes ─────────────────────────────
    app.include_router(ai_router, prefix=settings.api_prefix)
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(user_router, prefix=settings.api_prefix)

    # ── Include old routes ─────────────────────────────
    app.include_router(review_router)  # Handles /review/*
    app.include_router(legacy_routes)  # Fallback for /news and /sources

    # ── Root route ─────────────────────────────────────
    @app.get("/", tags=["meta"])
    def root() -> dict:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "docs": "/docs",
        }

    # ── Health check ───────────────────────────────────
    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok"}

    # ── Dashboard ──────────────────────────────────────
    @app.get("/dashboard", response_class=HTMLResponse, tags=["meta"])
    async def dashboard():
        html_path = os.path.join(BASE_DIR, "views", "index.html")
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse("<h1>Dashboard not found</h1>")

    return app


app = create_app()

# ── Run server ─────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
