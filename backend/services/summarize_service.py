from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch
import logging

logger = logging.getLogger(__name__)

# --- CONFIGURATION DU MODÈLE MT5 ---
MODEL_NAME = "google/mt5-small"
_tokenizer = None
_model = None

def get_model():
    """Charge le modèle en mémoire une seule fois (Singleton)."""
    global _tokenizer, _model
    if _model is None:
        try:
            logger.info(f"[SUMMARIZER] Initialisation de {MODEL_NAME} sur CPU...")
            _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
            _model.to("cpu")
            logger.info("[SUMMARIZER] Modèle prêt.")
        except Exception as e:
            logger.error(f"[SUMMARIZER] Erreur critique : {e}")
            _model = "FAILED"
    return _tokenizer, _model

def summarize_text(text: str, max_length: int = 150) -> str:
    """Génère le résumé d'un article."""
    if not text or len(text) < 100:
        return text

    tokenizer, model = get_model()
    if model == "FAILED":
        return text[:300] + "..."

    try:
        input_text = "summarize: " + text
        inputs = tokenizer.encode(input_text, return_tensors="pt", max_length=512, truncation=True)

        summary_ids = model.generate(
            inputs,
            max_length=max_length,
            min_length=30,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True
        )

        return tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    except Exception as e:
        logger.error(f"[SUMMARIZER] Erreur : {e}")
        return text[:300] + "..."
