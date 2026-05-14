from typing import List, Dict, Optional
import re
from langdetect import detect
from collections import Counter
from .summarize_service import summarize_text as ai_summarize_text

def detect_language(text: str, source: str = None) -> str:
    """
    Détecte la langue du texte (fr, en, ar, es, etc.) avec priorité sur l'arabe.
    Force l'arabe si la source est Hesport.
    """
    try:
        if source and source.lower() == "hesport":
            return "ar"
            
        if not text or len(text) < 10:
            return "fr" # Par défaut en français si trop court
        
        # Détection manuelle de l'arabe (Plage Unicode \u0600-\u06FF)
        # On vérifie si au moins 5% des caractères sont arabes
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        if len(text) > 20 and (arabic_chars / len(text)) > 0.05:
            return "ar"
        elif arabic_chars > 5: # Pour les textes courts mais clairement arabes
            return "ar"
            
        lang = detect(text)
        
        # Mapping vers nos langues supportées
        supported_langs = ["fr", "en", "ar", "es"]
        if lang in supported_langs:
            return lang
        
        return "fr" # Default if not in supported list
    except Exception as e:
        print(f"Error detecting language: {e}")
        return "ar" if source and source.lower() == "hesport" else "fr"

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

# Liste noire de termes à exclure systématiquement (ex: Snooker)
BLACKLIST = ["snooker", "billiards", "cnooker", "pool player"]

def classify_sport(text: str) -> str:
    """
    Classe l'article avec gestion du multi-langue (FR, EN, AR) 
    et résolution des ambiguïtés (Football/Soccer/Rugby/Golf).
    """
    # 0. Vérification Blacklist
    text_lower = text.lower()
    if any(word in text_lower for word in BLACKLIST):
        return "Banni"

    # 1. Nettoyage et préparation
    text = text_lower
    
    categories = {
        "Football": [
            "football", "foot", "soccer", "calcio", "fútbol", "futebol", "psg", "real madrid", "barcelona", "juventus", "milan", "benfica", "bayern", 
            "ligue 1", "la liga", "premier league", "serie a", "bundesliga", "champions league", "coupe du monde", "world cup", "copa del monde", "coppa del mondo", "copa do mundo",
            "fifa", "uefa", "mercato", "كرة القدم", "مباراة", "منتخب", "كأس العالم", "هداف", "نادي", "البطولة"
        ],
        "Tennis": [
            "tennis", "atp", "wta", "roland garros", "wimbledon", "raquette", "racket", "racchetta", "raqueta", "set", "tie-break", "grand chelem", "grand slam", "كرة المضرب"
        ],
        "Basketball": [
            "basketball", "basket-ball", "basket", "nba", "baloncesto", "pallacanestro", "basquetebol", "fiba", "dunk", "lebron", "curry", "panier", "basket", "كرة السلة"
        ],
        "Rugby": [
            "rugby", "top 14", "all blacks", "xv", "nfl", "super bowl", "touchdown", "quarterback", "american football", "fútbol americano", "football americano", "futebol americano", "الرغبي", "كرة القدم الأمريكية"
        ],
        "Cyclisme": [
            "cyclisme", "cycling", "ciclismo", "vélo", "bike", "bicicleta", "tour de france", "giro", "vuelta", "peloton", "vtt", "mtb", "سباق الدراجات"
        ],
        "Athlétisme": [
            "athlétisme", "athletics", "atletica", "atletismo", "marathon", "maratón", "maratona", "100m", "200m", "400m", "saut", "jump", "salto", "ألعاب القوى", "ماراثون"
        ],
        "Natation": [
            "natation", "swimming", "nuoto", "natación", "natacao", "piscine", "pool", "piscina", "nage", "swim", "سباحة", "حوض سباحة"
        ],
        "Handball": [
            "handball", "pallamano", "balonmano", "andebol", "pivot", "كرة اليد"
        ],
        "Volleyball": [
            "volleyball", "volley", "pallavolo", "voleibol", "smash", "الكرة الطائرة"
        ],
        "Sports Mécaniques": [
            "f1", "formule 1", "formula 1", "grand prix", "gp", "ferrari", "moto", "motogp", "rallye", "dakar", 
            "racing", "indycar", "indy", "indianapolis", "nascar", "motorsport", "circuit", "speedway", "driver", "pilote", "paddock", "podium",
            "écurie", "سباق فورمولا", "سباق الدراجات النارية", "سباق السيارات"
        ],
        "Combat": [
            "boxe", "boxing", "mma", "ufc", "judo", "karate", "taekwondo", "ملاكمة", "WBA", "WBO", "World Boxing Organization", "فنون قتالية",
            "bout", "fighter", "heavyweight", "ring", "knockout", "ko", "round", "sparring", "heavyweight", "lightweight"
        ],
        "Golf":[
            "golf", "putt", "green", "swing", "birdie", "masters", "dp world tour", "غولف"
        ],
        "Hockey": [
            "hockey", "nhl", "puck", "ice", "hielo", "ghiaccio", "gelo", "stanley cup", "playoff", "goaltender", "هوكي"
        ],
        "Équitation": [
            "équitation", "equestrian", "ippica", "hípica", "cheval", "horse", "cavallo", "caballo", "cavalo", "jockey", "hippisme", "turf", "ascot", "longchamp", "guineas", "classic", "hippique", "فروسية", "سباق الخيل", "خيل", "جوكى",
            "derby", "stakes", "epsom", "york", "cheltenham", "thoroughbred", "stallion", "mare", "colt", "filly", "equiworld"
        ],
        "Ski": [
            "ski", "sci", "esquí", "neige", "snow", "neve", "nieve", "slalom", "تزلج", "تزحلق"
        ]
    }
    
    scores = {cat: 0 for cat in categories}
    for cat, keywords in categories.items():
        for kw in keywords:
            # Recherche de mots entiers avec \b pour plus de précision
            # Note: \b fonctionne moins bien avec l'arabe, donc on check l'existence simple pour l'arabe
            is_arabic = any('\u0600' <= c <= '\u06FF' for c in kw)
            
            if is_arabic:
                scores[cat] += text.count(kw) * 2
            else:
                # Utilisation de \b pour matcher le mot exact uniquement
                pattern = r'\b' + re.escape(kw) + r'\b'
                matches = re.findall(pattern, text)
                scores[cat] += len(matches)
    
    best_cat = max(scores, key=scores.get)
    return best_cat if scores[best_cat] > 0 else "Autre"

def score_importance(article: Dict) -> int:
    """Calcul du score d'importance journalistique professionnel multilingue."""
    total_score = 0
    title = article.get("title", "").strip()
    content = article.get("content", "").strip()
    full_text = (title + " " + content).lower()
    
    # 1. Mots-clés Urgents et Exclusivités (Score élevé)
    urgent_keywords = {
        # Français
        "urgent": 25, "alerte": 20, "officiel": 20, "exclu": 15, "dernière minute": 20,
        # Anglais
        "breaking": 25, "alert": 20, "official": 20, "exclusive": 20, "last minute": 20,
        # Espagnol
        "urgente": 25, "alerta": 20, "oficial": 20, "exclusivo": 20, "última hora": 20,
        # Arabe
        "عاجل": 25, "تنبيه": 20, "رسمي": 20, "حصري": 20, "آخر ساعة": 20
    }
    
    for kw, bonus in urgent_keywords.items():
        if kw in full_text:
            total_score += bonus
            break  # On ne cumule pas les bonus d'urgence pure

    # 2. Impact, Choc et Santé (Score moyen)
    impact_keywords = {
        # Choc / Scandale
        "shock": 15, "scandale": 15, "escándalo": 15, "صدمة": 15, "فضيحة": 15,
        "incroyable": 10, "unbelievable": 10, "increíble": 10, "لا يصدق": 10,
        # Santé / Urgence médicale
        "malaise": 15, "health scare": 15, "susto de salud": 15, "وعكة صحية": 15,
        # Succès / Histoire
        "record": 10, "historique": 15, "historic": 15, "histórico": 15, "تاريخي": 15,
        "légende": 15, "legend": 15, "leyenda": 15, "أسطورة": 15,
        "finale": 20, "transfert": 15, "fichaje": 15, "انتقال": 15
    }
    
    for kw, bonus in impact_keywords.items():
        if kw in full_text:
            total_score += bonus

    # 3. Entités célèbres (Boost de notoriété)
    famous = ["psg", "real madrid", "mbappe", "messi", "ronaldo", "om", "nba", "jo 2024", "chelsea", "liverpool", "bayern","paris-saint-germain","barcelona","manchester", "mancity","arsenal","juventus","ac milan"]
    entity_hits = sum(1 for entity in famous if entity in full_text)
    total_score += min(entity_hits * 5, 25)

    # 4. Ponctuation et Longueur
    if any(char in title for char in ["!", "?"]):
        total_score += 5
    
    if len(content) > 1000:
        total_score += 10
    
    # Score final plafonné à 100
    return int(min(total_score, 100))