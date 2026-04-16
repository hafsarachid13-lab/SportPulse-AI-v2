from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.ai_main import router as ai_router
from backend.config import get_settings


def create_app() -> FastAPI:
	settings = get_settings()

	app = FastAPI(
		title=settings.app_name,
		version=settings.app_version,
		description="FastAPI backend for AI-assisted news review.",
	)

	app.add_middleware(
		CORSMiddleware,
		allow_origins=settings.cors_allow_origins,
		allow_credentials=settings.cors_allow_credentials,
		allow_methods=settings.cors_allow_methods,
		allow_headers=settings.cors_allow_headers,
	)

	app.include_router(ai_router, prefix=settings.api_prefix)

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
