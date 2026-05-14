"""
Dashboard Schemas — Pydantic models for dashboard API responses
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


# KPI Cards
class KPICard(BaseModel):
    total_articles: int
    active_sources: int
    avg_credibility: float = Field(ge=0, le=1)
    avg_importance: float = Field(ge=0, le=1)
    top_sport: str
    high_importance_count: int = 0
    categories_count: int = 0


# Article Volume Stats
class SourceVolume(BaseModel):
    name: str
    count: int


class ArticleVolumeStats(BaseModel):
    total: int
    by_source: Dict[str, int]
    by_hour: Dict[str, int]
    time_window: str
    trend: str


# Source Distribution
class SourceMetric(BaseModel):
    name: str
    article_count: int
    avg_credibility: float = Field(ge=0, le=1)
    avg_importance: float = Field(ge=0, le=1)
    percentage: float


class SourceDistribution(BaseModel):
    total_sources: int
    sources: List[SourceMetric]
    avg_articles_per_source: float


# Trending Topics
class TrendingKeyword(BaseModel):
    keyword: str
    frequency: int


class TrendingEntity(BaseModel):
    entity: str
    mentions: int


class TrendingTopics(BaseModel):
    trending_keywords: List[TrendingKeyword]
    trending_entities: List[TrendingEntity]
    total_unique_keywords: int


# Sport Analytics
class SportMetric(BaseModel):
    sport: str
    article_count: int
    percentage: float
    avg_importance: float = Field(ge=0, le=1)
    top_sources: List[Any]


class SportAnalytics(BaseModel):
    total_sports: int
    sports: List[SportMetric]
    distribution: Dict[str, int]


# Credibility Metrics
class CredibilityDistribution(BaseModel):
    high: int
    medium: int
    low: int


class SourceCredibility(BaseModel):
    source: str
    avg_credibility: float = Field(ge=0, le=1)
    article_count: int


class CredibilityMetrics(BaseModel):
    avg_credibility: float = Field(ge=0, le=1)
    distribution: CredibilityDistribution
    sources_by_credibility: List[SourceCredibility]


# Importance Metrics
class ImportanceDistribution(BaseModel):
    high: int
    medium: int
    low: int


class ImportanceRange(BaseModel):
    min: float = Field(ge=0, le=1)
    max: float = Field(ge=0, le=1)


class ImportanceMetrics(BaseModel):
    avg_importance: float = Field(ge=0, le=1)
    distribution: ImportanceDistribution
    range: ImportanceRange


# Filters
class FilterData(BaseModel):
    available_sources: List[str]
    available_sports: List[str]
    date_range: Dict[str, str]
    credibility_range: Dict[str, float]


# Dashboard Summary
class DashboardSummary(BaseModel):
    generated_date: str
    total_sources: int
    total_categories: int


# Complete Dashboard Response
class DashboardResponse(BaseModel):
    timestamp: str
    article_count: int
    kpis: KPICard
    article_volume: ArticleVolumeStats
    source_distribution: SourceDistribution
    sport_analytics: SportAnalytics
    trending: TrendingTopics
    credibility: CredibilityMetrics
    importance: ImportanceMetrics
    filters: FilterData
    summary: DashboardSummary


# Dashboard with Filters
class DashboardFilterParams(BaseModel):
    source: Optional[str] = None
    sport: Optional[str] = None
    min_credibility: float = Field(0.0, ge=0, le=1)
    min_importance: float = Field(0.0, ge=0, le=1)
    date_from: Optional[str] = None
    date_to: Optional[str] = None


# Export History
class ExportRecord(BaseModel):
    id: str
    format: str
    filename: str
    generated_at: str
    file_size: int
    user_id: Optional[int] = None


class ExportHistory(BaseModel):
    total_exports: int
    exports: List[ExportRecord]
    formats: Dict[str, int]  # count by format


# Dashboard State
class DashboardState(BaseModel):
    review_id: str
    review_date: str
    data: DashboardResponse
    filters_applied: Optional[DashboardFilterParams] = None
    last_updated: str


class QuickStats(BaseModel):
    total_articles: int
    active_sources: int
    average_ai_score: int
    covered_sports: int
    today_count: Optional[int] = None
