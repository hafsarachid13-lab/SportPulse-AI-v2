import re
from typing import List, Dict

def clean_text(text: str) -> str:
    """
    Nettoyage en profondeur du texte.
    """
    if not text:
        return ""

    # Supprimer les résidus de scripts ou styles
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL)
    
    # Supprimer les balises HTML restantes
    text = re.sub(r'<[^>]+>', '', text)
    
    # Normaliser les caractères spéciaux et espaces
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('&nbsp;', ' ')
    
    return text.strip()

def preprocess_articles(articles: List[Dict]) -> List[Dict]:
    """
    Prétraitement d'une liste d'articles.
    """
    cleaned_articles = []

    for article in articles:
        content = clean_text(article.get("content", ""))
        
        # On ne garde que les articles avec un contenu réel
        if not content or len(content.split()) < 50:
            continue
            
        cleaned_article = {
            **article,
            "title": clean_text(article.get("title", "")),
            "summary_rss": clean_text(article.get("summary", "")),
            "content": content
        }
        cleaned_articles.append(cleaned_article)

    print(f"[INFO] Articles après nettoyage : {len(cleaned_articles)}")
    return cleaned_articles