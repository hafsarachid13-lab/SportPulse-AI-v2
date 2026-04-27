from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any


class ArticleSchema(BaseModel):
    """Schema for a single processed article."""
    id: str
    title: str
    url: str
    source: str
    published_date: Optional[str] = None
    sport: str
    summary: str
    keywords: List[str] = []
    importance_score: float = Field(default=0.0, ge=0.0, le=1.0)


class ReviewResponse(BaseModel):
    """Response for GET /review/latest - STRUCTURED format."""
    title: str
    date: str
    generated_at: Optional[str] = None
    highlights: Optional[List[str]] = []
    top_headlines: List[str] = []
    categories: Dict[str, List[ArticleSchema]]
    articles: List[ArticleSchema]
    metadata: Optional[Dict[str, Any]] = None
    pdf_path: Optional[str] = None


class GenerateReviewResponse(BaseModel):
    """Response for POST /review/generate."""
    review: Dict[str, Any]  # Relaxed to avoid validation failures on real data
    pdf_url: str = Field(..., description="Relative URL to download PDF")