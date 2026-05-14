import sys
import os

# Ajouter le chemin du projet au sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.services.nlp_service import detect_language

texts = [
    ("English", "to determine what will happen to the premier league, if an indepemission upholds the charge that they spied on one of their training sessions in the very latest."),
    ("French", "de l'équipe nationale, en arizona, cet événement s'est déroulé ce mercredi. (AFP) ... des etats-unis"),
    ("Arabic", "هذا مقال باللغة العربية حول كرة القدم والمنتخب المغربي في كأس العالم"),
    ("Spanish", "Este es un artículo en español sobre fútbol y la liga española."),
    ("Mixed (FR with some AR)", "Le joueur a dit 'شكرا' à ses fans après le match."),
    ("Short", "Bonjour tout le monde")
]

for name, t in texts:
    try:
        detected = detect_language(t)
        print(f"Target: {name:15} | Detected: {detected}")
    except Exception as e:
        print(f"Error for {name}: {e}")
