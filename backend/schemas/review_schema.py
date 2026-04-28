"""
Review Schemas — Pydantic models for press review API responses
"""

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
    credibility: float = Field(default=0.75, ge=0.0, le=1.0)


class HeadlineSection(BaseModel):
    """Top headlines section of review."""
    title: str
    description: str
    articles: List[Dict[str, Any]]


class SummaryItem(BaseModel):
    """A single article summary entry."""
    title: str
    source: str
    sport: str
    summary: str
    importance: float = 0.0


class SummariesSection(BaseModel):
    """Article summaries section."""
    title: str
    description: str
    items: List[SummaryItem] = []


class TrendSection(BaseModel):
    """Trends and insights section."""
    title: str
    trending_sports: List[Dict[str, Any]]
    trending_sources: List[Dict[str, Any]]
    top_keywords: List[Dict[str, Any]]
    importance_distribution: Dict[str, int]
    average_importance: float


class SourcesSection(BaseModel):
    """Top sources section."""
    title: str
    description: str
    sources: List[Dict[str, Any]]


class KeywordsSection(BaseModel):
    """Keywords insights section."""
    title: str
    description: str
    keywords: List[Dict[str, Any]]


class ReviewMetadata(BaseModel):
    """Review metadata and statistics."""
    total_articles: int
    sources_count: int
    categories_count: int
    avg_importance: float
    avg_credibility: float


class ReviewSections(BaseModel):
    """Structured sections of a review."""
    headlines: HeadlineSection
    summaries: Optional[SummariesSection] = None
    by_sport: Dict[str, List[ArticleSchema]]
    trends: TrendSection
    top_sources: SourcesSection
    keywords: KeywordsSection


class ReviewResponse(BaseModel):
    """Response for GET /review/latest — STRUCTURED format."""
    id: str
    title: str
    date: str
    generated_at: Optional[str] = None
    sections: ReviewSections
    articles: List[ArticleSchema]

    # Legacy fields for backward compatibility
    highlights: Optional[List[str]] = []
    top_headlines: List[str] = []
    categories: Optional[Dict[str, List[ArticleSchema]]] = None

    metadata: Optional[ReviewMetadata] = None
    pdf_path: Optional[str] = None


class GenerateReviewResponse(BaseModel):
    """Response for POST /review/generate."""
    review: Dict[str, Any]  # Relaxed to avoid validation failures on real data
    pdf_url: str = Field(..., description="Relative URL to download PDF")


class ReviewListResponse(BaseModel):
    """Response for listing reviews."""
    total: int
    reviews: List[Dict[str, Any]]
    date_range: Optional[Dict[str, str]] = None


class ReviewHistoryEntry(BaseModel):
    """A single review history record."""
    id: str
    title: str
    date: str
    generated_at: str
    total_articles: int
    sources_count: int
    categories_count: int


class ReviewHistoryResponse(BaseModel):
    """Response for review generation history."""
    total: int
    history: List[ReviewHistoryEntry]
    generation_stats: Dict[str, Any]