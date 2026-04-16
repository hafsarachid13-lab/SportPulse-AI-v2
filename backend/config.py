from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel, Field


def _parse_csv(value: Optional[str]) -> List[str]:
	if not value:
		return []
	return [item.strip() for item in value.split(",") if item.strip()]


def _parse_bool(value: Optional[str], default: bool) -> bool:
	if value is None:
		return default
	return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
	app_name: str = "AI News Review API"
	app_version: str = "0.1.0"
	environment: str = "development"
	api_prefix: str = ""

	react_dev_origin: str = "http://localhost:3000"
	react_vite_origin: str = "http://localhost:5173"

	cors_allow_origins: List[str] = Field(default_factory=list)
	cors_allow_credentials: bool = True
	cors_allow_methods: List[str] = Field(default_factory=lambda: ["*"])
	cors_allow_headers: List[str] = Field(default_factory=lambda: ["*"])


@lru_cache(maxsize=1)
def get_settings() -> Settings:
	react_dev_origin = os.getenv("REACT_DEV_ORIGIN", "http://localhost:3000")
	react_vite_origin = os.getenv("REACT_VITE_ORIGIN", "http://localhost:5173")

	cors_origins = _parse_csv(os.getenv("CORS_ALLOW_ORIGINS"))
	if not cors_origins:
		cors_origins = [react_dev_origin, react_vite_origin]

	cors_methods = _parse_csv(os.getenv("CORS_ALLOW_METHODS")) or ["*"]
	cors_headers = _parse_csv(os.getenv("CORS_ALLOW_HEADERS")) or ["*"]

	return Settings(
		app_name=os.getenv("APP_NAME", "AI News Review API"),
		app_version=os.getenv("APP_VERSION", "0.1.0"),
		environment=os.getenv("ENVIRONMENT", "development"),
		api_prefix=os.getenv("API_PREFIX", ""),
		react_dev_origin=react_dev_origin,
		react_vite_origin=react_vite_origin,
		cors_allow_origins=cors_origins,
		cors_allow_credentials=_parse_bool(os.getenv("CORS_ALLOW_CREDENTIALS"), True),
		cors_allow_methods=cors_methods,
		cors_allow_headers=cors_headers,
	)
