from typing import List, Dict
from datetime import datetime

def generate_press_review(articles: List[Dict]) -> str:
    """
    Génère une revue de presse synthétique à partir d'une liste d'articles traités.
    """
    if not articles:
        return "Aucun article pertinent trouvé aujourd'hui."

    # Trier par score d'importance
    top_articles = sorted(articles, key=lambda x: x.get("importance_score", 0), reverse=True)
    
    review_parts = []
    review_parts.append(f"# REVUE DE PRESSE SPORTIVE - {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
    
    # Résumé par catégorie sportive
    sports = {}
    for a in top_articles:
        cat = a.get("sport_category", "Autre")
        if cat not in sports:
            sports[cat] = []
        sports[cat].append(a)
        
    for sport, apps in sports.items():
        review_parts.append(f"## {sport.upper()}")
        for a in apps[:3]: # Top 3 par sport
            review_parts.append(f"- **{a['title']}** ({a['source']})")
            review_parts.append(f"  > {a['summary']}\n")
            
    review_parts.append("\n--- \n*Revue générée automatiquement par l'Agent IA Antigravity*")
    
    return "\n".join(review_parts)
