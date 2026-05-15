import requests
import feedparser
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
import logging
import re

# Configuration des logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

# La liste des sources est désormais récupérée depuis la base de données.

def clean_text(text: str) -> str:
    if not text: return ""
    return " ".join(text.split())

def validate_source_url(url: str) -> Dict:
    """Valide si une URL est exploitable (RSS ou Scraping classique sans blocage majeur)."""
    import requests
    from bs4 import BeautifulSoup
    
    # Validation du format basique
    if not url.startswith("http"):
        url = "https://" + url
        
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code in [401, 403, 429]:
            return {
                "is_valid": False,
                "detected_type": None,
                "reliability_score": 0,
                "message": f"Accès bloqué par le serveur (Erreur HTTP {response.status_code})"
            }
        
        if response.status_code != 200:
            return {
                "is_valid": False,
                "detected_type": None,
                "reliability_score": 0,
                "message": f"Le serveur a répondu avec une erreur {response.status_code}"
            }
            
        html = response.text
        soup = BeautifulSoup(html, "lxml")
        
        title = soup.title.string if soup.title else ""
        if title and ("Just a moment..." in title or "Attention Required!" in title):
            return {
                "is_valid": False,
                "detected_type": None,
                "reliability_score": 0,
                "message": "Protection Anti-Bot détectée (ex: Cloudflare). Scraping bloqué."
            }
            
        rss_links = soup.find_all("link", type=lambda t: t in ["application/rss+xml", "application/atom+xml"])
        if rss_links:
            return {
                "is_valid": True,
                "detected_type": "rss",
                "reliability_score": 95,
                "message": "Flux RSS détecté. Source hautement fiable pour la collecte."
            }
            
        article_links = [h.find("a") for h in soup.find_all(["h2", "h3"]) if h.find("a")]
        
        if len(article_links) >= 3:
            return {
                "is_valid": True,
                "detected_type": "scraping",
                "reliability_score": 75,
                "message": "Aucun RSS trouvé, mais la structure de la page permet le web scraping."
            }
        else:
            return {
                "is_valid": False,
                "detected_type": None,
                "reliability_score": 0,
                "message": "Aucun flux RSS trouvé et structure de la page non adaptée au scraping classique."
            }
            
    except requests.exceptions.Timeout:
        return {
            "is_valid": False,
            "detected_type": None,
            "reliability_score": 0,
            "message": "Le serveur met trop de temps à répondre (Timeout)."
        }
    except requests.exceptions.RequestException as e:
        return {
            "is_valid": False,
            "detected_type": None,
            "reliability_score": 0,
            "message": f"Impossible de joindre l'URL fournie."
        }

def fetch_rss(source: Dict, limit: int) -> List[Dict]:
    articles = []
    try:
        feed_url = source.get("rss") or source.get("url")
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:limit]:
            # Conversion de la date RSS en datetime Python
            published_at = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                from datetime import datetime
                import time
                published_at = datetime.fromtimestamp(time.mktime(entry.published_parsed))

            articles.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "source": source.get("name", "Inconnue"),
                "content_preview": clean_text(entry.get("summary", "")),
                "lang": source.get("lang", "fr"),
                "credibility": source.get("credibility", 75),
                "published_at": published_at
            })
    except Exception as e:
        logger.error(f"Error RSS {source.get('name')}: {e}")
    return articles

def scrape_site(source: Dict, limit: int) -> List[Dict]:
    articles = []
    try:
        response = requests.get(source["url"], headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "lxml")
        tags = soup.find_all(['h2', 'h3'], limit=limit)
        for tag in tags:
            link = tag.find('a')
            if link and link.get('href'):
                full_url = link['href'] if link['href'].startswith('http') else source['url'].rstrip('/') + '/' + link['href'].lstrip('/')
                articles.append({
                    "title": clean_text(tag.get_text()),
                    "url": full_url,
                    "source": source.get("name", "Inconnue"),
                    "content_preview": "",
                    "lang": source.get("lang", "fr"),
                    "credibility": source.get("credibility", 75)
                })
    except Exception as e:
        logger.error(f"Error Scraping {source.get('name')}: {e}")
    return articles

def scrape_full_article(url: str) -> Dict:
    """Extrait le contenu et l'image principale avec une logique multi-couches."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "lxml")
        base_domain = "/".join(url.split("/")[:3])
        
        # --- CHASSE À L'IMAGE (Multi-niveaux) ---
        image_candidates = []
        
        # 1. Meta Tags (Priorité absolue)
        for meta_prop in ["og:image", "twitter:image", "image"]:
            mt = soup.find("meta", property=meta_prop) or soup.find("meta", attrs={"name": meta_prop}) or soup.find("meta", itemprop=meta_prop)
            if mt: image_candidates.append(mt.get("content"))
            
        # 2. Link tags
        lt = soup.find("link", rel=re.compile(r"image_src|shortcut icon"))
        if lt: image_candidates.append(lt.get("href"))
        
        # 3. Analyse du corps de l'article
        article_body = soup.find("article") or soup.find("main") or soup.find("div", class_=re.compile(r"content|article|story"))
        if article_body:
            # Chercher dans <picture>
            pic = article_body.find("picture")
            if pic:
                source_tag = pic.find("source")
                if source_tag: image_candidates.append(source_tag.get("srcset", "").split(",")[0].split(" ")[0])
            
            # Chercher toutes les images
            imgs = article_body.find_all("img")
            for img in imgs:
                # Tester plusieurs attributs possibles pour le lazy-loading
                candidates = [
                    img.get("src"), 
                    img.get("data-src"), 
                    img.get("data-srcset"), 
                    img.get("original-src"),
                    img.get("srcset")
                ]
                for src in candidates:
                    if src:
                        # Si c'est un srcset, on prend le premier lien
                        src = src.split(",")[0].split(" ")[0]
                        # Ignorer les logos, trackers et petites icônes
                        if not any(x in src.lower() for x in ["logo", "icon", "spacer", "ad", "track", "avatar", "placeholder"]):
                            image_candidates.append(src)
                            break
        
        # --- SÉLECTION DE LA MEILLEURE CANDIDATE ---
        image_url = None
        for cand in image_candidates:
            if cand and len(cand) > 5:
                # Normalisation URL
                if cand.startswith("//"): cand = "https:" + cand
                elif cand.startswith("/"): cand = base_domain + cand
                elif not cand.startswith("http"): cand = base_domain + "/" + cand
                
                image_url = cand
                break # On prend la première valide

        # --- EXTRACTION DU TITRE ---
        title = None
        # 1. Meta Tags
        for meta_prop in ["og:title", "twitter:title"]:
            mt = soup.find("meta", property=meta_prop) or soup.find("meta", attrs={"name": meta_prop})
            if mt: 
                title = clean_text(mt.get("content"))
                break
        # 2. H1 (Si pas de meta title ou trop court)
        if not title or len(title) < 15:
            h1 = soup.find("h1")
            if h1: title = clean_text(h1.get_text())

        # --- EXTRACTION DE LA DATE ---
        published_at = None
        for meta_prop in ["article:published_time", "og:pubdate", "pubdate"]:
            mt = soup.find("meta", property=meta_prop) or soup.find("meta", attrs={"name": meta_prop})
            if mt:
                try:
                    from dateutil import parser
                    published_at = parser.parse(mt.get("content"))
                    break
                except: continue

        # --- EXTRACTION CONTENU ---
        for s in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']): s.decompose()
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text() for p in paragraphs if len(p.get_text()) > 100])

        return {
            "title": title,
            "content": clean_text(content[:5000]),
            "image_url": image_url,
            "published_at": published_at
        }
    except Exception as e:
        logger.warning(f"Scrape failed for {url}: {e}")
        return {"content": "", "image_url": None}

def process_source(source: Dict, limit_per_source: int = 3) -> List[Dict]:
    """Extrait les articles pour une source spécifique."""
    logger.info(f"Collecte : {source.get('name')}")
    
    # Appel de la fonction selon le type
    if source.get("type", "").lower() == "rss":
        found = fetch_rss(source, limit_per_source)
    else:
        found = scrape_site(source, limit_per_source)
        
    source_articles = []
    for article in found:
        # 1. Scraping complet
        extra_data = scrape_full_article(article["url"])
        
        # Mise à jour du titre si trouvé
        if extra_data.get("title"):
            article["title"] = extra_data["title"]
        
        article.update({k: v for k, v in extra_data.items() if k != "title"})

        # 2. FILTRE DE DATE : On ne garde que les articles d'aujourd'hui
        from datetime import date
        today = date.today()
        art_date = article.get("published_at")
        
        if art_date and hasattr(art_date, 'date'):
            if art_date.date() != today:
                logger.info(f"Article ignoré (trop ancien) : {article['title']}")
                continue
        
        source_articles.append(article)
        time.sleep(0.1)
        
    return source_articles

def get_sources_with_credibility():
    """Fonction dépréciée si on gère la liste via DB, laissée pour rétrocompatibilité."""
    return []