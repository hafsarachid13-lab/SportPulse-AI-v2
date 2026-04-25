from ..services.nlp_service import summarize_text

def summarize_article(text: str) -> str:
    """
    Module faisant appel au service NLP pour résumer l'article.
    """
    return summarize_text(text)