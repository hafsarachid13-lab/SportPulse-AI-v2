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

# REPERTOIRE MONDIAL DES SOURCES SPORTIVES
SPORTS_SOURCES = [
    {"name": "Reuters Sports", "url": "https://www.reuters.com/sports/", "rss": "https://www.reuters.com/business/sports/rss", "lang": "en", "country": "Global", "credibility": 98},
    {"name": "AP Sports", "url": "https://apnews.com/hub/sports", "rss": None, "lang": "en", "country": "Global", "credibility": 98},
    {"name": "FIFA", "url": "https://www.fifa.com/", "rss": "https://www.fifa.com/rss/index.xml", "lang": "en", "country": "Global", "credibility": 100},
    {"name": "UEFA", "url": "https://www.uefa.com/", "rss": "https://www.uefa.com/rss/index.xml", "lang": "en", "country": "Europe", "credibility": 100},
    {"name": "CAF", "url": "https://www.cafonline.com/", "rss": None, "lang": "fr", "country": "Africa", "credibility": 95},
    {"name": "L'Equipe", "url": "https://www.lequipe.fr/", "rss": "https://xml.lequipe.fr/rss/uneseule/actu_rss.xml", "lang": "fr", "country": "France", "credibility": 95},
    {"name": "RMC Sport", "url": "https://rmcsport.bfmtv.com/", "rss": "https://rmcsport.bfmtv.com/rss/football/", "lang": "fr", "country": "France", "credibility": 90},
    {"name": "Sky Sports", "url": "https://www.skysports.com/", "rss": "https://www.skysports.com/rss/12040", "lang": "en", "country": "UK", "credibility": 95},
    {"name": "ESPN", "url": "https://www.espn.com/", "rss": "https://www.espn.com/espn/rss/news", "lang": "en", "country": "USA", "credibility": 95},
    {"name": "Marca", "url": "https://www.marca.com/", "rss": "https://e00-marca.uecdn.es/rss/portada.xml", "lang": "es", "country": "Spain", "credibility": 88},
    {"name": "Hesport", "url": "https://www.hesport.com/", "rss": "https://www.hesport.com/feed/", "lang": "ar", "country": "Morocco", "credibility": 85},
    {"name": "Arryadia", "url": "https://arryadia.snrt.ma/", "rss": "https://arryadia.snrt.ma/rss", "lang": "fr", "country": "Morocco", "credibility": 95}
]

def clean_text(text: str) -> str:
    if not text: return ""
    return " ".join(text.split())

def fetch_rss(source: Dict, limit: int) -> List[Dict]:
    articles = []
    try:
        feed = feedparser.parse(source["rss"])
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
                "source": source["name"],
                "content_preview": clean_text(entry.get("summary", "")),
                "lang": source["lang"],
                "credibility": source["credibility"],
                "published_at": published_at
            })
    except Exception as e:
        logger.error(f"Error RSS {source['name']}: {e}")
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
                    "source": source["name"],
                    "content_preview": "",
                    "lang": source["lang"],
                    "credibility": source["credibility"]
                })
    except Exception as e:
        logger.error(f"Error Scraping {source['name']}: {e}")
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

def fetch_articles(limit_per_source: int = 3) -> List[Dict]:
    all_articles = []
    for source in SPORTS_SOURCES:
        logger.info(f"Collecte : {source['name']}")
        found = fetch_rss(source, limit_per_source) if source.get("rss") else scrape_site(source, limit_per_source)
            
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
            
            # Si on a une date, on vérifie qu'elle est d'aujourd'hui
            if art_date and hasattr(art_date, 'date'):
                if art_date.date() != today:
                    logger.info(f"Article ignoré (trop ancien) : {article['title']}")
                    continue
            
            all_articles.append(article)
            time.sleep(0.1)
            
    return all_articles

def get_sources_with_credibility():
    """Retourne la liste des sources avec leur score de crédibilité normalisé (0-1)."""
    return [
        {"name": s["name"], "credibility_score": s["credibility"] / 100.0} 
        for s in SPORTS_SOURCES
    ]