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
            articles.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "source": source["name"],
                "content_preview": clean_text(entry.get("summary", "")),
                "lang": source["lang"],
                "credibility": source["credibility"]
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
            imgs = article_body.find_all("img", src=True)
            for img in imgs:
                src = img["src"]
                # Ignorer les logos, trackers et petites icônes
                if not any(x in src.lower() for x in ["logo", "icon", "spacer", "ad", "track", "avatar"]):
                    image_candidates.append(src)
        
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

        # --- EXTRACTION CONTENU ---
        for s in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']): s.decompose()
        paragraphs = soup.find_all('p')
        content = " ".join([p.get_text() for p in paragraphs if len(p.get_text()) > 100])
        
        return {
            "content": clean_text(content[:5000]),
            "image_url": image_url
        }
    except Exception as e:
        logger.warning(f"Scrape failed for {url}: {e}")
        return {"content": "", "image_url": None}

def collect_all_articles(limit_per_source: int = 3) -> List[Dict]:
    all_articles = []
    for source in SPORTS_SOURCES:
        logger.info(f"Collecte : {source['name']}")
        found = fetch_rss(source, limit_per_source) if source.get("rss") else scrape_site(source, limit_per_source)
            
        for article in found:
            extra_data = scrape_full_article(article["url"])
            article.update(extra_data)
            all_articles.append(article)
            time.sleep(0.1)
            
    return all_articles