from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.ai_main import router as ai_router
from backend.config import get_settings
from backend.views.auth_routes import router as auth_router
from backend.views.user_routes import router as user_router
from backend.views.article_routes import router as article_router
from backend.views.review_routes import router as review_router
from backend.views.source_routes import router as source_router


def create_app() -> FastAPI:
	settings = get_settings()

	app = FastAPI(
		title=settings.app_name,
		version=settings.app_version,
		description="FastAPI backend for AI-assisted news review.",
	)

	app.add_middleware(
		CORSMiddleware,
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	app.include_router(ai_router, prefix=settings.api_prefix)
	app.include_router(auth_router, prefix=settings.api_prefix)
	app.include_router(user_router, prefix=settings.api_prefix)
	app.include_router(article_router, prefix=settings.api_prefix)
	app.include_router(review_router, prefix=settings.api_prefix)
	app.include_router(source_router, prefix=settings.api_prefix)

	@app.get("/", tags=["meta"])
	def root() -> dict:
		return {
			"name": settings.app_name,
			"version": settings.app_version,
			"environment": settings.environment,
			"docs": "/docs",
		}

	@app.get("/health", tags=["meta"])
	def health() -> dict:
		return {"status": "ok"}

	return app


app = create_app()
