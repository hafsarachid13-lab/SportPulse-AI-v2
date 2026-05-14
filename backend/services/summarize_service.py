import logging
import re
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

logger = logging.getLogger(__name__)

def preprocess_text(text: str) -> str:
    """Nettoie le texte avant le résumé."""
    text = re.sub(r'\(?Photo by .*?\)?|©.*|Copyright .*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def summarize_text(text: str, sentences_count: int = 3) -> str:
    """
    Génère un résumé extractif ultra-léger (LSA).
    Beaucoup plus rapide et stable que les modèles Transformers sur CPU.
    """
    if not text or len(text.strip()) < 100:
        return text

    try:
        clean_text = preprocess_text(text)
        
        # On utilise le français par défaut, sumy gère bien le multilingue si configuré
        language = "french" 
        
        parser = PlaintextParser.from_string(clean_text, Tokenizer(language))
        stemmer = Stemmer(language)
        summarizer = LsaSummarizer(stemmer)
        summarizer.stop_words = get_stop_words(language)

        # Sélection des N meilleures phrases
        summary_sentences = summarizer(parser.document, sentences_count)
        
        summary = " ".join([str(sentence) for sentence in summary_sentences])
        
        if not summary or len(summary) < 20:
            return clean_text[:250] + "..."
            
        return summary

    except Exception as e:
        logger.error(f"[SUMMARIZER] Échec sumy : {e}")
        return text[:250] + "..."
