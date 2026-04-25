from typing import List, Dict, Optional
import re
from langdetect import detect
from collections import Counter
from .summarize_service import summarize_text as ai_summarize_text

def detect_language(text: str) -> str:
    """Détecte la langue du texte (fr, en, ar, etc.)."""
    try:
        if not text or len(text) < 20:
            return "unknown"
        return detect(text)
    except:
        return "unknown"

def summarize_text(text: str, sentences_count: int = 3) -> str:
    """Relaye la demande au service de résumé IA."""
    return ai_summarize_text(text)

def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """Extrait les mots-clés les plus fréquents."""
    if not text:
        return []
    
    words = re.findall(r'\w+', text.lower())
    stop_words = {"plus", "fait", "être", "avoir", "cette", "après", "selon", "dont", "avec", "pour", "dans"}
    
    filtered_words = [w for w in words if w not in stop_words and len(w) > 3]
    counts = Counter(filtered_words)
    return [word for word, count in counts.most_common(top_n)]

def classify_sport(text: str) -> str:
    """Classe l'article dans une catégorie sportive."""
    text = text.lower()
    categories = {
        "Football": ["football", "foot", "psg", "ligue 1", "champions league", "mercato", "fifa", "match", "but", "ballon"],
        "Tennis": ["tennis", "atp", "wta", "roland garros", "raquette", "set", "court"],
        "Basketball": ["basket", "nba", "fiba", "dunk", "lebron", "curry"],
        "Rugby": ["rugby", "xv", "top 14", "try", "essai", "mêlée"],
        "Formule 1": ["f1", "formule 1", "grand prix", "ferrari", "lewis hamilton", "verstappen"],
        "Cyclisme": ["cyclisme", "vélo", "tour de france", "peloton"],
        "Combat": ["boxe", "mma", "ufc", "ring", "k-o"]
    }
    
    scores = {cat: 0 for cat in categories}
    for cat, keywords in categories.items():
        for kw in keywords:
            if kw in text:
                scores[cat] += text.count(kw)
    
    best_cat = max(scores, key=scores.get)
    return best_cat if scores[best_cat] > 0 else "Autre"

def score_importance(article: Dict) -> int:
    """Calcul du score d'importance journalistique professionnel."""
    total_score = 0
    title = article.get("title", "").strip()
    content = article.get("content", "").strip()
    full_text = (title + " " + content).lower()
    
    urgent_keywords = {"urgent": 25, "breaking": 25, "alerte": 20, "officiel": 20, "exclu": 15}
    for kw, bonus in urgent_keywords.items():
        if kw in full_text:
            total_score += bonus
            break 

    impact_keywords = {"record": 10, "transfert": 15, "finale": 20, "victoire": 10, "champion": 15}
    for kw, bonus in impact_keywords.items():
        if kw in full_text:
            total_score += bonus

    entity_hits = 0
    famous = ["psg", "real madrid", "mbappe", "messi", "ronaldo", "om", "nba", "jo 2024"]
    for entity in famous:
        if entity in full_text:
            entity_hits += 1
    total_score += min(entity_hits * 5, 25)

    if any(char in title for char in ["!", "?"]):
        total_score += 5
    
    content_len = len(content)
    if content_len > 1000:
        total_score += 10
    
    return int(min(total_score, 100))