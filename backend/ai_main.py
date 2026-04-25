from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field


#Temporairement
from .ai_agent.pipeline import run_scraping_pipeline
from .services.translate_service import translate_text


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
		Appelle le pipeline de scraping réel et filtre par sujet si nécessaire.
		"""
		# Lancement du pipeline réel
		articles_data = run_scraping_pipeline()
		
		# Conversion en modèles Pydantic NewsArticle
		news_articles = []
		for i, a in enumerate(articles_data):
			# Filtrage par topic simple sur le titre ou la catégorie
			if topic and topic.lower() not in a.get("title", "").lower() and topic.lower() not in a.get("sport_category", "").lower():
				continue
				
			news_articles.append(NewsArticle(
				id=f"news-{i:03d}",
				title=a.get("title", "Sans titre"),
				source=a.get("source", "Inconnue"),
				url=a.get("url", ""),
				summary=a.get("summary", "Résumé non disponible"),
				image_url=a.get("image_url"),
				importance_score=a.get("importance_score", 0),
				published_at=datetime.now(timezone.utc), # Simplification pour la démo
				category=a.get("sport_category", "Sport"),
			))
		
		return news_articles[:limit]

	def run(self, topic: str, limit: int) -> ReviewResponse:
		"""
		Exécute le pipeline complet et génère une revue de presse.
		"""
		articles = self.collect_news(topic=topic, limit=limit)
		
		if not articles:
			summary = f"Aucun article trouvé pour le sujet : {topic}"
			review_text = "La revue de presse n'a pas pu être générée."
		else:
			summary = f"Analyse de {len(articles)} articles récents sur {topic}."
			# On pourrait appeler generate_press_review ici aussi
			titles = " | ".join([a.title for a in articles])
			review_text = f"Revue du jour ({topic}) : {titles}. Contenu généré par l'agent IA."

		return ReviewResponse(
			topic=topic,
			article_count=len(articles),
			summary=summary,
			review=review_text,
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


@router.post("/ai/translate", response_model=TranslationResponse)
def translate(payload: TranslationRequest):
    """
    Endpoint pour traduire un résumé d'article.
    """
    result = translate_text(payload.text, payload.target_lang)
    return TranslationResponse(
        translated_text=result,
        target_lang=payload.target_lang
    )
