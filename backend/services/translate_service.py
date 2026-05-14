from deep_translator import GoogleTranslator
import logging

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = ["ar", "fr", "en", "es"]

def translate_text(text: str, target_lang: str) -> str:
    """
    Traduit un texte vers la langue cible en utilisant Google Translator.
    Supporte: 'ar', 'fr', 'en'.
    """
    if not text or text.strip() == "":
        logger.warning("[TRANSLATE] Texte vide fourni.")
        return ""

    if target_lang not in SUPPORTED_LANGUAGES:
        logger.error(f"[TRANSLATE] Langue non supportée : {target_lang}")
        raise ValueError(f"Langue '{target_lang}' non supportée. Utilisez: {SUPPORTED_LANGUAGES}")

    try:
        # On définit 'auto' pour la langue source pour plus de flexibilité
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        return translated
    except Exception as e:
        logger.error(f"[TRANSLATE] Échec de la traduction : {e}")
        # En cas d'échec technique (timeout, etc.), on renvoie le texte original
        return text
