from typing import Dict
from ..services.nlp_service import score_importance as nlp_score_importance

def score_importance(article: Dict) -> int:
    """
    Calcule le score d'importance via le service NLP.
    """
    return nlp_score_importance(article)