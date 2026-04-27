"""
Scraper Service — Production RSS + Web Scraping Pipeline
Fetches real sports articles from 7+ sources using RSS feeds and BeautifulSoup.
No mock data. No paid APIs.
"""

import logging
import time
import random
import hashlib
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import feedparser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]

REQUEST_TIMEOUT = 15  # seconds
MAX_RETRIES = 2
RETRY_DELAY = 2  # seconds base delay

# ──────────────────────────────────────────────────────────
# RSS FEED SOURCES
# ──────────────────────────────────────────────────────────

RSS_SOURCES = [
    # BBC Sport
    {
        "name": "BBC Sport",
        "url": "https://feeds.bbci.co.uk/sport/rss.xml",
        "credibility": 0.95,
        "type": "rss",
    },
    {
        "name": "BBC Football",
        "url": "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "credibility": 0.95,
        "type": "rss",
    },
    {
        "name": "BBC Tennis",
        "url": "https://feeds.bbci.co.uk/sport/tennis/rss.xml",
        "credibility": 0.95,
        "type": "rss",
    },
    {
        "name": "BBC Formula 1",
        "url": "https://feeds.bbci.co.uk/sport/formula1/rss.xml",
        "credibility": 0.95,
        "type": "rss",
    },
    # ESPN
    {
        "name": "ESPN",
        "url": "https://www.espn.com/espn/rss/news",
        "credibility": 0.93,
        "type": "rss",
    },
    {
        "name": "ESPN Soccer",
        "url": "https://www.espn.com/espn/rss/soccer/news",
        "credibility": 0.93,
        "type": "rss",
    },
    # The Guardian Sport
    {
        "name": "The Guardian Sport",
        "url": "https://www.theguardian.com/sport/rss",
        "credibility": 0.92,
        "type": "rss",
    },
    {
        "name": "The Guardian Football",
        "url": "https://www.theguardian.com/football/rss",
        "credibility": 0.92,
        "type": "rss",
    },
    # Marca (English)
    {
        "name": "Marca",
        "url": "https://e00-marca.uecdn.es/rss/en/portada.xml",
        "credibility": 0.88,
        "type": "rss",
    },
    # Yahoo Sports
    {
        "name": "Yahoo Sports",
        "url": "https://sports.yahoo.com/rss/",
        "credibility": 0.85,
        "type": "rss",
    },
    # Sky Sports (scrape headlines page as fallback)
    {
        "name": "Sky Sports",
        "url": "https://www.skysports.com/rss/12040",
        "credibility": 0.91,
        "type": "rss",
    },
    # Goal.com
    {
        "name": "Goal.com",
        "url": "https://www.goal.com/feeds/en/news",
        "credibility": 0.84,
        "type": "rss",
    },
]

# ──────────────────────────────────────────────────────────
# SPORT CLASSIFICATION KEYWORDS
# ──────────────────────────────────────────────────────────

SPORT_KEYWORDS = {
    "Football": [
        "football", "soccer", "premier league", "la liga", "serie a", "bundesliga",
        "champions league", "europa league", "world cup", "transfer", "goal",
        "striker", "midfielder", "defender", "goalkeeper", "offside", "penalty",
        "manchester", "barcelona", "real madrid", "liverpool", "arsenal", "chelsea",
        "psg", "bayern", "juventus", "inter milan", "ac milan", "tottenham",
        "man city", "man united", "epl", "fa cup", "carabao", "ligue 1",
        "messi", "ronaldo", "mbappe", "haaland", "neymar", "ballon d'or",
    ],
    "Basketball": [
        "basketball", "nba", "wnba", "lakers", "celtics", "warriors", "bulls",
        "nets", "knicks", "bucks", "suns", "nuggets", "heat", "76ers",
        "lebron", "curry", "durant", "giannis", "jokic", "dunk", "three-pointer",
        "playoffs", "finals", "euroleague", "march madness", "ncaa basketball",
    ],
    "Tennis": [
        "tennis", "grand slam", "wimbledon", "roland garros", "us open",
        "australian open", "atp", "wta", "djokovic", "nadal", "federer",
        "alcaraz", "sinner", "swiatek", "sabalenka", "match point", "set",
        "ace", "deuce", "break point", "davis cup",
    ],
    "Formula 1": [
        "formula 1", "f1", "grand prix", "qualifying", "pole position",
        "pit stop", "verstappen", "hamilton", "leclerc", "norris", "sainz",
        "red bull racing", "ferrari", "mclaren", "mercedes f1", "fia",
        "sprint race", "drs", "podium",
    ],
    "Rugby": [
        "rugby", "six nations", "rugby world cup", "try", "scrum",
        "all blacks", "springboks", "wallabies", "premiership rugby",
    ],
    "Boxing & MMA": [
        "boxing", "mma", "ufc", "heavyweight", "knockout", "ko",
        "fight night", "tyson", "fury", "canelo", "jake paul",
    ],
    "Golf": [
        "golf", "pga", "masters", "the open", "ryder cup", "birdie",
        "eagle", "bogey", "tiger woods", "mcilroy",
    ],
    "Cricket": [
        "cricket", "ipl", "test match", "ashes", "t20", "odi",
        "wicket", "batsman", "bowler",
    ],
    "Cycling": [
        "cycling", "tour de france", "giro", "vuelta", "peloton",
        "pogacar", "vingegaard",
    ],
}

BREAKING_KEYWORDS = [
    "breaking", "just in", "official", "confirmed", "exclusive",
    "urgent", "announce", "signs", "transfer", "record", "injured",
    "fired", "sacked", "hired", "retired", "comeback", "suspended",
    "ban", "doping", "scandal", "historic", "upset", "shock",
]

# ──────────────────────────────────────────────────────────
# CREDIBILITY MAP
# ──────────────────────────────────────────────────────────

SOURCE_CREDIBILITY = {
    "BBC Sport": 0.95,
    "BBC Football": 0.95,
    "BBC Tennis": 0.95,
    "BBC Formula 1": 0.95,
    "ESPN": 0.93,
    "ESPN Soccer": 0.93,
    "The Guardian Sport": 0.92,
    "The Guardian Football": 0.92,
    "Sky Sports": 0.91,
    "Marca": 0.88,
    "Yahoo Sports": 0.85,
    "Goal.com": 0.84,
}


# ──────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────────────────────

def _get_session() -> requests.Session:
    """Create a requests session with random user agent."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    })
    return session


def _fetch_with_retry(url: str, session: requests.Session = None, retries: int = MAX_RETRIES) -> Optional[str]:
    """Fetch URL content with retry logic and exponential backoff."""
    if session is None:
        session = _get_session()

    for attempt in range(retries + 1):
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp.text
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching {url} (attempt {attempt + 1}/{retries + 1})")
        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP error {e.response.status_code} for {url}")
            if e.response.status_code in (403, 429):
                time.sleep(RETRY_DELAY * (attempt + 1))
                session.headers["User-Agent"] = random.choice(USER_AGENTS)
                continue
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error for {url}: {e}")

        if attempt < retries:
            delay = RETRY_DELAY * (2 ** attempt) + random.uniform(0, 1)
            time.sleep(delay)

    return None


def _normalize_url(url: str) -> str:
    """Normalize URL for deduplication."""
    parsed = urlparse(url)
    # Strip trailing slashes, fragments, common tracking params
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{path}".lower()


def _text_fingerprint(text: str) -> str:
    """Create a fingerprint from text for dedup."""
    cleaned = re.sub(r'[^a-z0-9\s]', '', text.lower().strip())
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return hashlib.md5(cleaned.encode()).hexdigest()


def _classify_sport(title: str, text: str = "") -> str:
    """Classify an article into a sport category based on keywords."""
    combined = f"{title} {text}".lower()
    scores = {}

    for sport, keywords in SPORT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            scores[sport] = score

    if scores:
        return max(scores, key=scores.get)
    return "General"


def _calculate_importance(article: Dict[str, Any]) -> float:
    """Calculate importance score (0.0 to 1.0) based on multiple factors."""
    score = 0.0

    # Factor 1: Source credibility (0-0.3)
    source_name = article.get("source", "")
    credibility = SOURCE_CREDIBILITY.get(source_name, 0.5)
    score += credibility * 0.3

    # Factor 2: Breaking news keywords (0-0.3)
    title = article.get("title", "").lower()
    text = article.get("text", "").lower()
    combined = f"{title} {text}"
    breaking_count = sum(1 for kw in BREAKING_KEYWORDS if kw in combined)
    score += min(breaking_count * 0.06, 0.3)

    # Factor 3: Freshness (0-0.2)
    pub_date = article.get("published_date", "")
    if pub_date:
        try:
            pub_dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            age_hours = (datetime.now(pub_dt.tzinfo) - pub_dt).total_seconds() / 3600
            if age_hours < 3:
                score += 0.2
            elif age_hours < 12:
                score += 0.15
            elif age_hours < 24:
                score += 0.1
            else:
                score += 0.05
        except (ValueError, TypeError):
            score += 0.1  # default for unparseable dates

    # Factor 4: Content richness (0-0.2)
    text_len = len(article.get("text", ""))
    if text_len > 1000:
        score += 0.2
    elif text_len > 500:
        score += 0.15
    elif text_len > 200:
        score += 0.1
    else:
        score += 0.05

    return round(min(score, 1.0), 3)


def _extract_summary(text: str, max_sentences: int = 3) -> str:
    """Extract a simple summary from article text (first N sentences)."""
    if not text:
        return "No summary available."

    # Split by sentence-ending punctuation
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if not sentences:
        return text[:300].strip() + ("..." if len(text) > 300 else "")

    summary = " ".join(sentences[:max_sentences])
    if len(summary) > 500:
        summary = summary[:500].rsplit(" ", 1)[0] + "..."
    return summary


def _extract_article_text(url: str, session: requests.Session) -> str:
    """Try to extract full article text using newspaper3k, fallback to BS4."""
    # Try newspaper3k first
    try:
        from newspaper import Article as NP_Article
        article = NP_Article(url)
        article.download()
        article.parse()
        if article.text and len(article.text) > 100:
            return article.text
    except Exception:
        pass

    # Fallback: basic BS4 extraction
    try:
        html = _fetch_with_retry(url, session, retries=1)
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")

        # Remove script/style/nav/footer
        for tag in soup(["script", "style", "nav", "footer", "aside", "header"]):
            tag.decompose()

        # Try common article containers
        article_tag = soup.find("article")
        if article_tag:
            paragraphs = article_tag.find_all("p")
        else:
            paragraphs = soup.find_all("p")

        text = " ".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30)
        return text[:5000]  # cap at 5000 chars
    except Exception as e:
        logger.debug(f"Text extraction failed for {url}: {e}")
        return ""


# ──────────────────────────────────────────────────────────
# RSS FEED PARSING
# ──────────────────────────────────────────────────────────

def _parse_rss_feed(source: Dict[str, Any], session: requests.Session) -> List[Dict[str, Any]]:
    """Parse a single RSS feed and return list of raw articles."""
    source_name = source["name"]
    feed_url = source["url"]
    articles = []

    logger.info(f"  📡 Fetching RSS: {source_name} ({feed_url})")

    try:
        # feedparser can handle URL directly but we use session for headers
        content = _fetch_with_retry(feed_url, session, retries=MAX_RETRIES)
        if not content:
            logger.warning(f"  ❌ Failed to fetch {source_name}")
            return []

        feed = feedparser.parse(content)

        if not feed.entries:
            logger.warning(f"  ⚠️ No entries in {source_name} feed")
            return []

        logger.info(f"  ✅ Got {len(feed.entries)} entries from {source_name}")

        for entry in feed.entries[:15]:  # limit per source
            title = entry.get("title", "").strip()
            if not title:
                continue

            link = entry.get("link", "")
            if not link:
                continue

            # Parse published date
            pub_date = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    pub_date = datetime(*entry.published_parsed[:6]).isoformat()
                except Exception:
                    pass
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                try:
                    pub_date = datetime(*entry.updated_parsed[:6]).isoformat()
                except Exception:
                    pass

            # Get description/summary from RSS entry
            description = ""
            if hasattr(entry, "summary"):
                # Strip HTML from RSS summary
                soup = BeautifulSoup(entry.summary, "html.parser")
                description = soup.get_text(strip=True)
            elif hasattr(entry, "description"):
                soup = BeautifulSoup(entry.description, "html.parser")
                description = soup.get_text(strip=True)

            articles.append({
                "title": title,
                "url": link,
                "source": source_name,
                "published_date": pub_date or datetime.now().isoformat(),
                "text": description,  # RSS summary as text; full text fetched later
                "credibility": source.get("credibility", 0.5),
            })

    except Exception as e:
        logger.error(f"  ❌ Error parsing {source_name}: {e}")

    return articles


# ──────────────────────────────────────────────────────────
# DEDUPLICATION
# ──────────────────────────────────────────────────────────

def _deduplicate_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate articles by URL normalization and title similarity."""
    seen_urls = set()
    seen_titles = set()
    unique = []

    for art in articles:
        # URL-based dedup
        norm_url = _normalize_url(art.get("url", ""))
        if norm_url in seen_urls:
            continue

        # Title-based dedup (fingerprint)
        title_fp = _text_fingerprint(art.get("title", ""))
        if title_fp in seen_titles:
            continue

        seen_urls.add(norm_url)
        seen_titles.add(title_fp)
        unique.append(art)

    removed = len(articles) - len(unique)
    if removed > 0:
        logger.info(f"  🔄 Deduplication: removed {removed} duplicates, {len(unique)} remain")

    return unique


# ──────────────────────────────────────────────────────────
# ENRICHMENT (full text + classification + scoring)
# ──────────────────────────────────────────────────────────

def _enrich_articles(articles: List[Dict[str, Any]], fetch_full_text: bool = True) -> List[Dict[str, Any]]:
    """Enrich articles with full text, sport classification, importance score, and summary."""
    session = _get_session()
    enriched = []

    for i, art in enumerate(articles):
        # Optionally fetch full article text for top articles
        text = art.get("text", "")
        if fetch_full_text and len(text) < 200 and i < 30:
            try:
                full_text = _extract_article_text(art["url"], session)
                if full_text and len(full_text) > len(text):
                    text = full_text
                # Small delay to be respectful
                time.sleep(random.uniform(0.3, 0.8))
            except Exception as e:
                logger.debug(f"Full text extraction failed: {e}")

        art["text"] = text
        art["sport"] = _classify_sport(art.get("title", ""), text)
        art["summary"] = _extract_summary(text)
        art["importance_score"] = _calculate_importance(art)

        enriched.append(art)

    return enriched


# ──────────────────────────────────────────────────────────
# PUBLIC API
# ──────────────────────────────────────────────────────────

def fetch_articles(max_per_source: int = 15, fetch_full_text: bool = True) -> List[Dict[str, Any]]:
    """
    Main entry point: fetch real sports articles from all RSS sources.
    Returns a list of enriched article dicts compatible with ReviewService.
    """
    logger.info("=" * 60)
    logger.info("🚀 STARTING LIVE ARTICLE SCRAPING")
    logger.info(f"   Sources configured: {len(RSS_SOURCES)}")
    logger.info("=" * 60)

    all_articles = []
    session = _get_session()
    successful_sources = 0
    failed_sources = 0

    # Fetch from all sources (parallel with ThreadPoolExecutor)
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_source = {
            executor.submit(_parse_rss_feed, source, _get_session()): source
            for source in RSS_SOURCES
        }

        for future in as_completed(future_to_source):
            source = future_to_source[future]
            try:
                articles = future.result()
                if articles:
                    all_articles.extend(articles)
                    successful_sources += 1
                else:
                    failed_sources += 1
            except Exception as e:
                logger.error(f"  ❌ Source {source['name']} raised exception: {e}")
                failed_sources += 1

    logger.info(f"📊 Scraping complete: {successful_sources} sources OK, {failed_sources} failed")
    logger.info(f"   Raw articles collected: {len(all_articles)}")

    if not all_articles:
        logger.error("❌ No articles collected from any source!")
        return []

    # Deduplication
    logger.info("🔄 Deduplicating articles...")
    unique_articles = _deduplicate_articles(all_articles)

    # Enrich with classification + scoring
    logger.info("🧠 Enriching articles (classification, scoring, summaries)...")
    enriched = _enrich_articles(unique_articles, fetch_full_text=fetch_full_text)

    # Sort by importance
    enriched.sort(key=lambda x: x.get("importance_score", 0), reverse=True)

    logger.info(f"✅ Final article count: {len(enriched)}")
    logger.info("=" * 60)

    return enriched


def get_sources_with_credibility() -> List[Dict[str, Any]]:
    """Return all configured sources with their credibility scores."""
    seen = set()
    sources = []
    for src in RSS_SOURCES:
        base_name = src["name"].split(" ")[0]  # Group by base name
        if base_name not in seen:
            seen.add(base_name)
            sources.append({
                "name": src["name"],
                "url": src["url"],
                "credibility_score": src["credibility"],
                "type": src["type"],
            })
    return sources
