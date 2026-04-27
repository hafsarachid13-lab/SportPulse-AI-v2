"""
News Schemas — Person 5 Module
Pydantic models for /news and /sources endpoints.
"""

from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime


class ArticleResponse(BaseModel):
    id: int
    title: str
    source: Optional[str] = None
    category: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[str] = None

    class Config:
        from_attributes = True  # Pydantic v2 (use orm_mode=True for v1)


class SourceResponse(BaseModel):
    id: int
    name: str
    url: Optional[str] = None
    category: Optional[str] = None
    active: bool = True

    class Config:
        from_attributes = True