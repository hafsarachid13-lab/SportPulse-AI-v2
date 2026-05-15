import logging
from datetime import datetime
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

logger = logging.getLogger(__name__)

def save_articles_to_db(articles_data):
    """
    Sauvegarde une liste d'articles enrichis dans la base de données MySQL.
    """
    db = SessionLocal()
    try:
        # 1. Préparer un mapping des sports pour éviter les requêtes répétées
        sports_map = {s.nom.lower(): s.id for s in db.query(Sport).all()}
        
        saved_count = 0
        for data in articles_data:
            # Normalisation URL
            url = data.get("url", "").split('?')[0].split('#')[0]
            
            # Vérification doublon
            existing = db.query(Article).filter(Article.url == url).first()
            if existing:
                continue

            # Gestion de la date
            pub_date = data.get("published_at")
            if not pub_date:
                pub_date = datetime.now()

            # Gestion de la Source
            source_id = data.get("source_id")
            if not source_id:
                source_name = data.get("source", "Source Inconnue")
                source = db.query(Source).filter(Source.name == source_name).first()
                if not source:
                    source = Source(name=source_name, url=url or "http://inconnu.com", type="scraping")
                    db.add(source)
                    db.flush()
                source_id = source.id

            # Création de l'article
            new_article = Article(
                title=data.get("title", "Sans titre")[:250],
                content=data.get("content", ""),
                summary=data.get("summary", ""),
                url=url,
                published_at=pub_date,
                collected_at=datetime.now(),
                sport_category=data.get("sport_category", "Général"),
                sport_id=sports_map.get(data.get("sport_category", "").lower()),
                importance_score=float(data.get("importance_score", 0.0)),
                credibility_score=float(data.get("credibility_score", 0.75)),
                langue=data.get("language", "fr"),
                image_url=data.get("image_url"),
                source_id=source_id,
                status=ArticleStatus.PENDING.value
            )
            db.add(new_article)
            saved_count += 1
        
        db.commit()
        logger.info(f"[DATABASE] {saved_count} nouveaux articles enregistrés avec succès.")
    except Exception as e:
        db.rollback()
        logger.error(f"[DATABASE] Erreur critique lors de la sauvegarde : {str(e)}")
    finally:
        db.close()


def run_pipeline():
    """
    Exécute le pipeline complet de veille sportive et persiste les résultats.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[PIPELINE] Lancement de la collecte à {now}...")

    # 1. Collecte
    raw_articles = collect_articles()
    if not raw_articles:
        logger.info("[PIPELINE] Aucun article collecté.")
        return []

    # 2. Nettoyage
    clean_articles = preprocess_articles(raw_articles)

    # 3. Traitement NLP & Enrichissement
    processed_articles = []
    EXCLUDED_KEYWORDS = ["snooker", "billiards", "cnooker"]
    
    db = SessionLocal()
    try:
        for article in clean_articles:
            url = article.get("url", "").split('?')[0].split('#')[0]
            
            # OPTIMISATION : Vérifier si l'article existe déjà AVANT le traitement lourd
            existing = db.query(Article).filter(Article.url == url).first()
            if existing:
                logger.info(f"[PIPELINE] Article déjà en base, skip traitement IA : {article.get('title', '')[:50]}...")
                # On peut quand même l'ajouter à processed_articles si on veut qu'il apparaisse dans la revue du jour
                # mais ici on cherche à optimiser la collecte de nouveaux contenus.
                continue

            content = article.get("content", "").lower()
            title = article.get("title", "").lower()
            full_text = f"{title} {content}"
            
            # Filtre de sécurité : Snooker et autres sports exclus
            if any(word in full_text for word in EXCLUDED_KEYWORDS):
                logger.info(f"[PIPELINE] Article ignoré (Catégorie bannie détectée)")
                continue
                
            # Détection langue (Déléguée au service NLP avec forçage source)
            article["language"] = detect_language(content, source=article.get("source"))
            
            # Résumé automatique (C'est ici que c'est lent !)
            article["summary"] = summarize_article(content)
            
            # Mots-clés
            article["keywords"] = extract_keywords(content)
            
            # Classification Sport (Forçage Football pour Hesport)
            if article.get("source") == "Hesport":
                sport = "Football"
            else:
                sport = classify_sport(content)
            
            # Au lieu de supprimer, on classe en "Général" si non reconnu
            if sport == "Autre":
                sport = "Général"
                
            article["sport_category"] = sport
            
            # Score d'importance
            article["importance_score"] = score_importance(article)
            
            # Crédibilité
            article["credibility_score"] = check_credibility(article)
            
            processed_articles.append(article)
    finally:
        db.close()

    # 4. Sauvegarde des Articles en Base de Données
    if processed_articles:
        save_articles_to_db(processed_articles)
    else:
        logger.info("[PIPELINE] Aucun nouvel article à sauvegarder.")

    # 5. Génération de la revue de presse (On récupère les articles du jour pour la revue)
    # Si on veut une revue complète, il vaut mieux fetch les articles récents en base
    review_content = generate_press_review(processed_articles)
    
    # 6. Persistance de la Revue de Presse en Base
    save_review_to_db(processed_articles, review_content)
    
    logger.info(f"[PIPELINE] Terminé. {len(processed_articles)} nouveaux articles traités.")
    return processed_articles

def save_review_to_db(articles, review_text):
    """Sauvegarde la revue générée dans MySQL."""
    from ..database.models import RevueDePresse, RevueItem, User
    db = SessionLocal()
    try:
        from datetime import date
        today = date.today()
        
        # 1. Vérifier si une revue existe déjà pour aujourd'hui
        existing = db.query(RevueDePresse).filter(RevueDePresse.date == today).first()
        if existing:
            logger.info("[PIPELINE] Une revue existe déjà pour aujourd'hui. Mise à jour...")
            existing.contenu_texte = review_text
            db.commit()
            return

        # 2. Trouver un utilisateur (Admin) pour porter la revue
        admin = db.query(User).first()
        if not admin:
            logger.error("[PIPELINE] Erreur : Aucun utilisateur trouvé pour créer la revue.")
            return

        # 3. Création de la revue
        new_review = RevueDePresse(
            date=today,
            title=f"Revue de Presse du {today.strftime('%d/%m/%Y')}",
            contenu_texte=review_text,
            nb_articles=len(articles),
            user_id=admin.id,
            status="published"
        )
        db.add(new_review)
        db.flush()

        # 4. Ajouter les articles liés dans RevueItem
        for i, art_data in enumerate(articles[:10]):
            from ..database.models import Article
            db_art = db.query(Article).filter(Article.url == art_data.get("url")).first()
            if db_art:
                item = RevueItem(
                    revue_id=new_review.id,
                    article_id=db_art.id,
                    rank=i,
                    sport_section=art_data.get("sport_category", "Général")
                )
                db.add(item)
        
        db.commit()
        logger.info("[PIPELINE] Revue de presse enregistrée avec succès.")
    except Exception as e:
        db.rollback()
        logger.error(f"[PIPELINE] Erreur lors de la sauvegarde de la revue : {e}")
    finally:
        db.close()

def generate_full_review():
    articles = run_pipeline()
    return generate_press_review(articles)

def run_scraping_pipeline():
    return run_pipeline()

if __name__ == "__main__":
    articles = run_pipeline()
    for a in articles[:3]:
        print(f"--- {a['title']} ---")
        print(f"Cat: {a['sport_category']} | Score: {a['importance_score']}")
        print(f"Summary: {a['summary']}\n")