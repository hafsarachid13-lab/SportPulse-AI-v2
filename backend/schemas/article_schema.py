from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class ArticleBase(BaseModel):
    title: str
    content: Optional[str] = None
    url: str
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    sport_category: Optional[str] = None
    importance_score: float = 0.0
    langue: str = "fr"
    image_url: Optional[str] = None
    status: str = "pending"

class ArticleCreate(ArticleBase):
    source_id: int

class ArticleSchema(ArticleBase):
    id: int
    collected_at: datetime
    source_id: int

    class Config:
        from_attributes = True
