from ..services.nlp_service import classify_sport as nlp_classify_sport

def classify_sport(text: str) -> str:
    """
    Détermine le sport de l'article via le service NLP.
    """
    return nlp_classify_sport(text)