from __future__ import annotations

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from backend.config import get_settings
from backend.database import init_db

# ── Hafsa's routers (new architecture) ──────────────────
from backend.ai_main import router as ai_router
from backend.views.auth_routes import router as auth_router
from backend.views.user_routes import router as user_router
from backend.views.article_routes import router as article_router
from backend.views.review_routes import router as review_routes
from backend.views.source_routes import router as source_router

# ── Person 5's consolidated routers ─────────────────────
from backend.views.dashboard_routes import router as dashboard_router
from backend.controllers.review_controller import router as review_controller_router
from backend.core.scheduler import news_scheduler

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

    # ── CORS ────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins or ["*"],
        allow_origin_regex=settings.cors_allow_origin_regex,
        allow_credentials=(
            settings.cors_allow_credentials
            if settings.cors_allow_credentials is not None
            else True
        ),
        allow_methods=settings.cors_allow_methods or ["*"],
        allow_headers=settings.cors_allow_headers or ["*"],
    )

    # ── Static folders ──────────────────────────────────
    BASE_DIR = os.path.dirname(__file__)
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    STATIC_PDF_DIR = os.path.join(BASE_DIR, "static_pdfs")
    STATIC_EXPORTS_DIR = os.path.join(BASE_DIR, "..", "static_exports")
    os.makedirs(STATIC_DIR, exist_ok=True)
    os.makedirs(STATIC_PDF_DIR, exist_ok=True)
    os.makedirs(STATIC_EXPORTS_DIR, exist_ok=True)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # ── Include Hafsa's routes ──────────────────────────
    app.include_router(ai_router, prefix=settings.api_prefix + "/ai")
    app.include_router(auth_router, prefix=settings.api_prefix)
    app.include_router(user_router, prefix=settings.api_prefix)
    app.include_router(article_router, prefix=settings.api_prefix)
    app.include_router(review_routes, prefix=settings.api_prefix)
    app.include_router(source_router, prefix=settings.api_prefix)

    # ── Include Person 5's dashboard & API routes ───────
    app.include_router(dashboard_router, prefix=settings.api_prefix)

    # ── Include Person 5's review controller ────────────
    app.include_router(review_controller_router, prefix=settings.api_prefix)

    # ── Dashboard HTML route ────────────────────────────
    @app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
    async def dashboard():
        """Serve the interactive dashboard UI."""
        html_path = os.path.join(BASE_DIR, "views", "dashboard.html")
        if os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse("<h1>Dashboard not found</h1>")

    # ── Root route ──────────────────────────────────────
    @app.get("/", tags=["meta"])
    def root() -> dict:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "docs": "/docs",
            "dashboard": "/dashboard",
        }

    # ── Health check ────────────────────────────────────
    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok"}

    # ── Startup event: Log all registered routes ────────
    @app.on_event("startup")
    def startup_event():
        """Initialize database and log all registered routes at startup."""
        try:
            logger.info("=" * 80)
            logger.info(f"✅ FastAPI Application Started: {settings.app_name}")
            logger.info(f"Environment: {settings.environment} | API Prefix: {settings.api_prefix}")
            logger.info("=" * 80)
            
            # Initialize database
            logger.info("🗄️  Initializing database...")
            init_db()
            logger.info("✅ Database initialized successfully")
            
            logger.info("📋 REGISTERED ROUTES:")
            logger.info("-" * 80)
            
            for route in app.routes:
                if hasattr(route, "path") and hasattr(route, "methods"):
                    methods = ", ".join(route.methods) if route.methods else "N/A"
                    logger.info(f"  {methods:8} {route.path}")
            
            logger.info("-" * 80)
            logger.info("📌 KEY ENDPOINTS FOR FRONTEND:")
            logger.info(f"  GET     {settings.api_prefix}/review")
            logger.info(f"  POST    {settings.api_prefix}/generate-review")
            logger.info(f"  GET     {settings.api_prefix}/news")
            logger.info(f"  GET     {settings.api_prefix}/sources")
            logger.info(f"  GET     {settings.api_prefix}/review/latest")
            logger.info(f"  POST    {settings.api_prefix}/review/generate")
            logger.info("-" * 80)
            
            # Start scheduler
            news_scheduler.start()
            
        except Exception as e:
            logger.error(f"❌ Startup failed: {e}", exc_info=True)
            raise

    @app.on_event("shutdown")
    def shutdown_event():
        """Stop scheduler when application shuts down."""
        news_scheduler.shutdown()
        logger.info("👋 Application shutting down")

    return app


app = create_app()

# ── Run server ─────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
