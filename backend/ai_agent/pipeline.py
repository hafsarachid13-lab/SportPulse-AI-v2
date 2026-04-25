import logging
from datetime import datetime
from .collector import collect_articles
from .preprocessing import preprocess_articles
from .summarizer import summarize_article
from .classifier import classify_sport
from .ranking import score_importance
from .credibility import check_credibility
from .review_generator import generate_press_review
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
            # Vérifier si l'article existe déjà (par URL)
            existing = db.query(Article).filter(Article.url == data.get("url")).first()
            if existing:
                continue

            # Gérer la Source
            source_name = data.get("source", "Source Inconnue")
            source = db.query(Source).filter(Source.name == source_name).first()
            if not source:
                source = Source(name=source_name, url=data.get("url", ""), type="rss")
                db.add(source)
                db.flush() # Pour obtenir l'ID

            # Gérer le Sport
            sport_name = data.get("sport_category", "Sport")
            sport_id = sports_map.get(sport_name.lower())
            
            # Créer l'article
            new_article = Article(
                title=data.get("title", "Sans titre"),
                content=data.get("content", ""),
                url=data.get("url", ""),
                published_at=datetime.now(), # Idéalement utiliser la date du flux
                sport_category=sport_name,
                sport_id=sport_id,
                importance_score=data.get("importance_score", 0.0),
                langue=data.get("language", "fr"),
                image_url=data.get("image_url"),
                source_id=source.id,
                status=ArticleStatus.PENDING.value
            )
            db.add(new_article)
            saved_count += 1
        
        db.commit()
        print(f"[DATABASE] {saved_count} nouveaux articles enregistrés en base.")
    except Exception as e:
        db.rollback()
        print(f"[DATABASE] Erreur lors de la sauvegarde : {e}")
    finally:
        db.close()

def run_pipeline():
    """
    Exécute le pipeline complet de veille sportive et persiste les résultats.
    """
    print("[PIPELINE] Lancement...")

    # 1. Collecte
    raw_articles = collect_articles()
    if not raw_articles:
        print("[PIPELINE] Aucun article collecté.")
        return []

    # 2. Nettoyage
    clean_articles = preprocess_articles(raw_articles)

    # 3. Traitement NLP & Enrichissement
    processed_articles = []
    for article in clean_articles:
        content = article.get("content", "")
        
        # Détection langue
        article["language"] = detect_language(content)
        
        # Résumé automatique
        article["summary"] = summarize_article(content)
        
        # Mots-clés
        article["keywords"] = extract_keywords(content)
        
        # Classification Sport
        article["sport_category"] = classify_sport(content)
        
        # Score d'importance
        article["importance_score"] = score_importance(article)
        
        # Crédibilité
        article["credibility_score"] = check_credibility(article)
        
        processed_articles.append(article)

    # 4. Sauvegarde des Articles en Base de Données
    save_articles_to_db(processed_articles)

    # 5. Génération de la revue de presse
    review_content = generate_press_review(processed_articles)
    
    # 6. Persistance de la Revue de Presse en Base
    save_review_to_db(processed_articles, review_content)

    print(f"[PIPELINE] Terminé. {len(processed_articles)} articles traités et revue sauvegardée.")
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
            print("[PIPELINE] Une revue existe déjà pour aujourd'hui. Mise à jour...")
            existing.contenu_texte = review_text
            db.commit()
            return

        # 2. Trouver un utilisateur (Admin) pour porter la revue
        admin = db.query(User).first()
        if not admin:
            print("[PIPELINE] Erreur : Aucun utilisateur trouvé pour créer la revue.")
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
        print("[PIPELINE] Revue de presse enregistrée avec succès.")
    except Exception as e:
        db.rollback()
        print(f"[PIPELINE] Erreur lors de la sauvegarde de la revue : {e}")
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