from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch
import logging
import threading
import re

logger = logging.getLogger(__name__)

# --- CONFIGURATION DU MODÈLE MT5 ---
# On repasse sur la version "small" pour plus de légèreté sur votre machine
MODEL_NAME = "google/mt5-small"
_tokenizer = None
_model = None
_model_lock = threading.Lock()

def get_model():
    """Charge le modèle en mémoire une seule fois (Singleton thread-safe)."""
    global _tokenizer, _model
    
    # Si le modèle est déjà prêt ou a échoué, on retourne tout de suite
    if _model is not None:
        return _tokenizer, _model
        
    with _model_lock:
        # Double check après acquisition du verrou
        if _model is None:
            try:
                logger.info(f"[SUMMARIZER] Initialisation de {MODEL_NAME} sur CPU...")
                # use_fast=False est recommandé pour mT5 sur certains environnements Windows
                _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=False)
                _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
                _model.to("cpu")
                logger.info("[SUMMARIZER] Modèle prêt.")
            except Exception as e:
                logger.error(f"[SUMMARIZER] Erreur critique : {e}")
                _model = "FAILED"
    return _tokenizer, _model

def preprocess_text(text: str) -> str:
    """Nettoie le texte avant de l'envoyer au modèle pour éviter les résumés parasites."""
    # Supprimer les crédits photos et mentions d'agences communes
    text = re.sub(r'\(?Photo by .*?\)?|©.*|Copyright .*', '', text, flags=re.IGNORECASE)
    text = re.sub(r' - [a-z ]+/icon sport -|-[a-z ]+/icon sport-', '', text, flags=re.IGNORECASE)
    text = re.sub(r'd\'états-unis\.com\.cl|......com', '', text, flags=re.IGNORECASE)
    # Supprimer les mentions de réseaux sociaux ou liens
    text = re.sub(r'https?://\S+', '', text)
    # Nettoyer les espaces multiples
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def summarize_text(text: str, max_length: int = 150) -> str:
    """Génère le résumé d'un article avec un modèle optimisé pour le résumé multilingue."""
    if not text or text.strip() == "":
        return ""

    # Nettoyage préalable pour améliorer la qualité
    clean_text = preprocess_text(text)

    # Si le texte est très court, on le renvoie tel quel
    if len(clean_text) < 150:
        return clean_text

    tokenizer, model = get_model()
    
    # Fallback si le modèle n'est pas chargé ou a échoué
    if model is None or model == "FAILED":
        return clean_text[:250] + "..." if len(clean_text) > 250 else clean_text

    try:
        # Pour mT5-small, un prompt plus direct aide parfois
        input_text = f"résumé: {clean_text}"
        
        inputs = tokenizer(input_text, return_tensors="pt", truncation=True, max_length=512)

        summary_ids = model.generate(
            inputs["input_ids"],
            max_length=max_length,
            min_length=40,
            length_penalty=1.5,
            num_beams=5,
            repetition_penalty=2.5,  # Évite les répétitions de mots
            no_repeat_ngram_size=3,
            early_stopping=True
        )

        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        
        # NETTOYAGE DES BALISES <extra_id_X> 
        summary = re.sub(r'<extra_id_\d+>', '', summary)
        summary = re.sub(r'\s+([-.:])\s+', r'\1 ', summary)
        summary = summary.strip()
        
        # Si le résultat du modèle est trop court ou vide, fallback
        if not summary or len(summary) < 20:
            return clean_text[:250] + "..."
            
        return summary
    except Exception as e:
        logger.error(f"[SUMMARIZER] Échec génération : {e}")
        return clean_text[:250] + "..."
    except Exception as e:
        logger.error(f"[SUMMARIZER] Échec génération : {e}")
        return text[:250] + "..."

