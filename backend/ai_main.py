from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field


#Temporairement
from .ai_agent.pipeline import run_scraping_pipeline
from .services.translate_service import translate_text
from .database.db import SessionLocal
from .database.models import Article, RevueDePresse
from fastapi import BackgroundTasks


def main():
    articles = run_scraping_pipeline()

    for i, article in enumerate(articles[:5], start=1):
        print("=" * 80)
        print(f"Article {i}")
        print("SOURCE :", article.get("source"))
        print("TITLE  :", article.get("title"))
        print("URL    :", article.get("article_url"))
        print("DATE   :", article.get("published_at"))
        print("TEXT   :", article.get("content", "")[:500])
        print("=" * 80)


if __name__ == "__main__":
    main()
#Temporairement



router = APIRouter(tags=["ai"])


class NewsArticle(BaseModel):
	id: str
	title: str
	source: str
	url: str
	summary: Optional[str] = None
	image_url: Optional[str] = None
	importance_score: int = 0
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


class TranslationRequest(BaseModel):
    text: str
    target_lang: str = Field(..., pattern="^(ar|fr|en)$")


class TranslationResponse(BaseModel):
    translated_text: str
    target_lang: str


class AIPipeline:
	"""Orchestrateur relié au pipeline de production IA."""

	def collect_news(self, topic: Optional[str], limit: int) -> List[NewsArticle]:
		"""
		Récupère les articles depuis la base de données (cache).
		"""
		db = SessionLocal()
		try:
			query = db.query(Article).order_by(Article.published_at.desc())
			
			if topic:
				# Recherche simple dans le titre ou la catégorie
				query = query.filter(
					(Article.title.ilike(f"%{topic}%")) | 
					(Article.sport_category.ilike(f"%{topic}%"))
				)
			
			articles_db = query.limit(limit).all()
			
			news_articles = []
			for a in articles_db:
				news_articles.append(NewsArticle(
					id=f"news-{a.id}",
					title=a.title,
					source=a.source.name if a.source else "Inconnue",
					url=a.url,
					summary=a.content[:200] + "..." if a.content else "Résumé non disponible",
					image_url=a.image_url,
					importance_score=int(a.importance_score * 100) if a.importance_score else 0,
					published_at=a.published_at or datetime.now(timezone.utc),
					category=a.sport_category or "Sport",
				))
			
			return news_articles
		finally:
			db.close()

	def run(self, topic: str, limit: int) -> ReviewResponse:
		"""
		Récupère la dernière revue de presse ou lance le pipeline.
		"""
		db = SessionLocal()
		try:
			# Essayer de trouver la revue d'aujourd'hui
			from datetime import date
			today_review = db.query(RevueDePresse).filter(RevueDePresse.date == date.today()).first()
			
			if today_review:
				return ReviewResponse(
					topic=topic,
					article_count=today_review.nb_articles,
					summary=today_review.title,
					review=today_review.contenu_texte,
					generated_at=today_review.generated_at,
				)
			
			# Si pas de revue, on prévient qu'il faut lancer la collecte
			return ReviewResponse(
				topic=topic,
				article_count=0,
				summary="Aucune revue disponible pour aujourd'hui.",
				review="Veuillez lancer une collecte de news pour générer la revue.",
				generated_at=datetime.now(timezone.utc),
			)
		finally:
			db.close()


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


@router.post("/collect")
def trigger_collection(background_tasks: BackgroundTasks):
	"""
	Lance le pipeline de collecte en arrière-plan.
	"""
	background_tasks.add_task(run_scraping_pipeline)
	return {"status": "started", "message": "Le pipeline de collecte a été lancé en arrière-plan."}


@router.post("/review", response_model=ReviewResponse)
def generate_review(
	payload: ReviewRequest,
	background_tasks: BackgroundTasks,
	pipeline: AIPipeline = Depends(get_pipeline),
) -> ReviewResponse:
	# On lance la mise à jour en arrière-plan et on retourne ce qu'on a
	background_tasks.add_task(run_scraping_pipeline)
	return pipeline.run(topic=payload.topic, limit=payload.limit)


@router.post("/translate", response_model=TranslationResponse)
def translate(payload: TranslationRequest):
    """
    Endpoint pour traduire un résumé d'article.
    """
    result = translate_text(payload.text, payload.target_lang)
    return TranslationResponse(
        translated_text=result,
        target_lang=payload.target_lang
    )
