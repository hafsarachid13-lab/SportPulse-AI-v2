from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field


router = APIRouter(tags=["ai"])


class NewsArticle(BaseModel):
	id: str
	title: str
	source: str
	url: str
	published_at: datetime
	category: str


class NewsResponse(BaseModel):
	topic: Optional[str] = None
	total: int
	items: List[NewsArticle]


class ReviewRequest(BaseModel):
	topic: str = Field(default="general", min_length=2, max_length=80)
	limit: int = Field(default=5, ge=1, le=20)


class ReviewResponse(BaseModel):
	topic: str
	article_count: int
	summary: str
	review: str
	generated_at: datetime


class AIPipeline:
	"""Simple orchestrator with stubs for the future production AI pipeline."""

	def collect_news(self, topic: Optional[str], limit: int) -> List[NewsArticle]:
		now = datetime.now(timezone.utc)
		catalog = [
			NewsArticle(
				id="news-001",
				title="Local startup launches new climate sensor",
				source="Tech Daily",
				url="https://example.com/news/1",
				published_at=now,
				category="technology",
			),
			NewsArticle(
				id="news-002",
				title="Public transport upgrades announced for 2027",
				source="City Journal",
				url="https://example.com/news/2",
				published_at=now,
				category="society",
			),
			NewsArticle(
				id="news-003",
				title="University team publishes AI ethics framework",
				source="Education Wire",
				url="https://example.com/news/3",
				published_at=now,
				category="ai",
			),
		]
		if topic:
			filtered = [item for item in catalog if topic.lower() in item.title.lower()]
			if filtered:
				return filtered[:limit]
		return catalog[:limit]

	def preprocess(self, articles: List[NewsArticle]) -> List[dict]:
		# TODO(team): replace this with normalization, deduplication, and language handling.
		return [
			{
				"id": article.id,
				"title": article.title,
				"token_count": len(article.title.split()),
				"source": article.source,
			}
			for article in articles
		]

	def summarize(self, processed_items: List[dict]) -> str:
		# TODO(team): connect to an LLM summarizer and prompt templates.
		if not processed_items:
			return "No relevant articles were found for this topic."
		titles = "; ".join(item["title"] for item in processed_items)
		return f"Trending points from today's feed: {titles}."

	def generate_review_text(self, topic: str, summary: str) -> str:
		# TODO(team): integrate credibility and ranking stages before final generation.
		return (
			f"Daily review for '{topic}': {summary} "
			"This is a mock response prepared for frontend and API integration."
		)

	def run(self, topic: str, limit: int) -> ReviewResponse:
		articles = self.collect_news(topic=topic, limit=limit)
		processed = self.preprocess(articles)
		summary = self.summarize(processed)
		review = self.generate_review_text(topic=topic, summary=summary)
		return ReviewResponse(
			topic=topic,
			article_count=len(articles),
			summary=summary,
			review=review,
			generated_at=datetime.now(timezone.utc),
		)


def get_pipeline() -> AIPipeline:
	return AIPipeline()


@router.get("/news", response_model=NewsResponse)
def get_news(
	topic: Optional[str] = Query(default=None, min_length=2, max_length=80),
	limit: int = Query(default=5, ge=1, le=20),
	pipeline: AIPipeline = Depends(get_pipeline),
) -> NewsResponse:
	items = pipeline.collect_news(topic=topic, limit=limit)
	return NewsResponse(topic=topic, total=len(items), items=items)


@router.get("/review", response_model=ReviewResponse)
def get_review(
	topic: str = Query(default="general", min_length=2, max_length=80),
	limit: int = Query(default=5, ge=1, le=20),
	pipeline: AIPipeline = Depends(get_pipeline),
) -> ReviewResponse:
	return pipeline.run(topic=topic, limit=limit)


@router.post("/review", response_model=ReviewResponse)
def generate_review(
	payload: ReviewRequest,
	pipeline: AIPipeline = Depends(get_pipeline),
) -> ReviewResponse:
	return pipeline.run(topic=payload.topic, limit=payload.limit)
