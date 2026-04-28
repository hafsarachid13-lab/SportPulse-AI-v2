from typing import Dict

def check_credibility(article: Dict) -> float:
    """
    Calcule un score de crédibilité basé sur la renommée de la source.
    Retourne un score entre 0 et 1.
    """
    source = article.get("source", "").lower()
    
    # Sources très fiables
    tier_1 = ["l'equipe", "bbc sport", "sky sports", "rmc sport", "the guardian", "le monde"]
    # Sources moyennement fiables ou agrégateurs
    tier_2 = ["yahoo sport", "msn sport", "foot mercato"]
    
    for s in tier_1:
        if s in source:
            return 1.0
            
    for s in tier_2:
        if s in source:
            return 0.7
            
    return 0.5
