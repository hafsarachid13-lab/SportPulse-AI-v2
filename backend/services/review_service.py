import logging
import threading
import time
from datetime import datetime, timedelta
from typing import List, Dict

from backend.ai_agent.collector import collect_articles
from backend.ai_agent.preprocessing import preprocess_articles
from backend.ai_agent.summarizer import summarize_article
from backend.ai_agent.classifier import classify_sport
from backend.ai_agent.ranking import score_importance
from backend.ai_agent.credibility import check_credibility
from backend.ai_agent.review_generator import generate_press_review
from ..services.nlp_service import detect_language, extract_keywords
from ..database.db import SessionLocal
from ..database.models import Article, Source, Sport, ArticleStatus
from backend.ai_agent.pipeline import run_pipeline, save_review_to_db, save_articles_to_db

logger = logging.getLogger(__name__)

class ReviewService:
    """Service pour gérer la génération et la récupération des revues de presse."""
    
    _instance = None
    _latest_review = None
    _history = []
    _is_generating = False
    _last_run_time = 0 # Timestamp du dernier lancement réussi
    _gen_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        self._initialized = True

    def generate_review(self, background=False) -> dict:
        """Exécute le pipeline avec protection contre les lancements multiples."""
        with self._gen_lock:
            # 1. Protection contre les tâches concurrentes
            if self._is_generating:
                logger.info("[REVIEW_SERVICE] Une tâche est déjà en cours. Skip.")
                return {"status": "processing", "message": "Déjà en cours..."}
            
            # 2. Anti-spam : ne pas relancer si fait il y a moins de 10 minutes
            current_time = time.time()
            if current_time - self._last_run_time < 600: # 600 secondes = 10 mins
                logger.info(f"[REVIEW_SERVICE] Trop tôt pour relancer ({int(current_time - self._last_run_time)}s depuis le dernier).")
                return {"status": "too_soon", "message": "Dernière mise à jour trop récente."}
            
            # On marque comme en cours AVANT de lancer le thread pour bloquer les appels suivants immédiats
            self._is_generating = True
            self._last_run_time = current_time

        if background:
            thread = threading.Thread(target=self._run_generation_task)
            thread.daemon = True
            thread.start()
            return {"status": "processing", "message": "Génération lancée en arrière-plan"}
        
        return self._run_generation_task()

    def _run_generation_task(self):
        """La tâche lourde de génération (Scraping + IA)."""
        try:
            logger.info("[REVIEW_SERVICE] === DEBUT DU PIPELINE IA (Scraping + Summarization) ===")
            # 1. Exécution du pipeline lourd et récupération directe des résultats
            processed_articles = run_pipeline()
            
            # 2. Récupération et structuration des résultats
            db = SessionLocal()
            try:
                from datetime import date, datetime, time as dt_time, timedelta
                today_start = datetime.combine(date.today(), dt_time.min)
                
                # On cherche les articles collectés aujourd'hui
                articles_db = db.query(Article).filter(
                    Article.collected_at >= today_start
                ).order_by(Article.published_at.desc()).all()
                
                # Si rien trouvé (ex: problème de fuseau horaire), on prend les 20 derniers articles
                if not articles_db:
                    logger.warning("[REVIEW_SERVICE] Filtre 'Aujourd'hui' vide, récupération des 20 derniers articles globaux.")
                    articles_db = db.query(Article).order_by(Article.collected_at.desc()).limit(20).all()
                
                articles = self._convert_articles_to_dict(articles_db)
                
                if articles:
                    review_content = generate_press_review(articles)
                    review = self._build_review_object(articles, review_content)
                    self._latest_review = review
                    self._persist_review_to_db(review, articles)
                    logger.info(f"[REVIEW_SERVICE] === PIPELINE RÉUSSI : {len(articles)} articles dans la revue ===")
                else:
                    logger.error("[REVIEW_SERVICE] Toujours aucun article trouvé, même en élargissant la recherche.")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[REVIEW_SERVICE] Échec critique du pipeline : {e}", exc_info=True)
        finally:
            self._is_generating = False


    def _build_review_object(self, articles, review_content, is_temp=False):
        """Construit l'objet structuré de la revue."""
        from datetime import datetime
        status_prefix = "[TEMP] " if is_temp else ""
        
        return {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "title": f"{status_prefix}Revue de Presse du {datetime.now().strftime('%d/%m/%Y')}",
            "date": datetime.now().isoformat(),
            "articles": articles,
            "is_processing": self._is_generating,
            "metadata": {
                "total_articles": len(articles),
                "sources_count": len(set(a.get("source") for a in articles)),
                "categories_count": len(set(a.get("sport_category") for a in articles)),
                "avg_importance": sum(a.get("importance_score", 0) for a in articles) / len(articles) if articles else 0,
                "avg_credibility": sum(a.get("credibility_score", 0) for a in articles) / len(articles) if articles else 0,
            },
            "sections": {
                "executive_summary": {
                    "title": "Résumé Exécutif",
                    "text": review_content,
                    "stats": {"avg_credibility": 0}
                },
                "top_sources": {"sources": self._get_top_sources(articles)}
            },
            "categories": self._group_by_category(articles)
        }

    def _persist_review_to_db(self, review, articles):
        db = SessionLocal()
        try:
            from ..database.models import RevueDePresse, RevueStatus
            from datetime import date
            today_date = date.today()
            existing = db.query(RevueDePresse).filter(RevueDePresse.date == today_date).first()
            if existing:
                existing.content_json = review
                existing.nb_articles = len(articles)
                existing.generated_at = datetime.now()
            else:
                new_revue = RevueDePresse(
                    date=today_date, title=review["title"],
                    content_json=review, nb_articles=len(articles),
                    status=RevueStatus.DRAFT.value, user_id=1
                )
                db.add(new_revue)
            db.commit()
        except Exception as e:
            logger.error(f"Error persisting: {e}")
            db.rollback()
        finally:
            db.close()

    def get_latest_review(self) -> dict:
        """Retourne la revue d'aujourd'hui intelligemment (strictement quotidienne)."""
        from datetime import date, datetime, time as dt_time
        from ..database.models import RevueDePresse
        
        db = SessionLocal()
        try:
            today_date = date.today()
            today_start = datetime.combine(today_date, dt_time.min)
            
            # 1. Revue finale déjà en base pour aujourd'hui ?
            last_revue = db.query(RevueDePresse).filter(RevueDePresse.date == today_date).first()
            
            # 2. Articles collectés STRICTEMENT aujourd'hui
            articles_db = db.query(Article).filter(
                Article.collected_at >= today_start
            ).order_by(Article.published_at.desc()).all()
                
            articles_dict = self._convert_articles_to_dict(articles_db)

            # Cas A : Revue finale prête
            if last_revue and last_revue.content_json:
                res = last_revue.content_json
                # Mise à jour si nouveaux articles aujourd'hui
                if len(articles_dict) > res.get("metadata", {}).get("total_articles", 0):
                    res["articles"] = articles_dict
                    res["metadata"]["total_articles"] = len(articles_dict)
                    res["categories"] = self._group_by_category(articles_dict)
                return res
            
            # Cas B : Pas de revue finale mais des articles existent pour aujourd'hui
            if articles_dict:
                self.generate_review(background=True)
                return self._build_review_object(articles_dict, "Analyse des articles du jour en cours...", is_temp=True)

            # Cas C : Rien pour aujourd'hui (on lance le scraping mais on n'affiche pas les articles d'hier)
            self.generate_review(background=True)
            return self._build_review_object([], "En attente de nouveaux articles pour aujourd'hui...", is_temp=True)



        except Exception as e:
            logger.error(f"Error: {e}")
            return {}
        finally:
            db.close()

    def _convert_articles_to_dict(self, articles_db):
        articles = []
        for a in articles_db:
            articles.append({
                "id": a.id, "title": a.title, "content": a.content,
                "summary": a.summary or "Résumé en cours...", "url": a.url,
                "published_at": a.published_at.isoformat() if a.published_at else None,
                "sport_category": a.sport_category or "Général",
                "importance_score": a.importance_score or 0.5,
                "credibility_score": getattr(a, "credibility_score", 0.75) or 0.75,
                "source": a.source.name if a.source else "Inconnue",
                "image_url": a.image_url,
            })
        return self._deduplicate_articles(articles)

    def _deduplicate_articles(self, articles_dict: List[Dict]) -> List[Dict]:
        from difflib import SequenceMatcher
        unique = []
        for art in articles_dict:
            is_dup = False
            for ex in unique:
                if SequenceMatcher(None, art["title"].lower(), ex["title"].lower()).ratio() > 0.7:
                    if art["source"] not in ex["source"]:
                        ex["source"] = f"{ex['source']}, {art['source']}"
                    is_dup = True
                    break
            if not is_dup: unique.append(art)
        return unique

    def get_review_history(self) -> list:
        return self._history

    def get_generation_stats(self) -> dict:
        return {
            "is_generating": self._is_generating,
            "last_run_seconds_ago": int(time.time() - self._last_run_time) if self._last_run_time > 0 else None
        }

    def _group_by_category(self, articles):
        categories = {}
        for art in articles:
            cat = art.get("sport_category", "Général")
            if cat not in categories: categories[cat] = []
            categories[cat].append(art)
        return categories

    def _get_top_sources(self, articles):
        from collections import Counter
        sources_count = Counter(a.get("source", "Inconnu") for a in articles)
        return [{"source": s, "article_count": c} for s, c in sources_count.most_common(5)]
