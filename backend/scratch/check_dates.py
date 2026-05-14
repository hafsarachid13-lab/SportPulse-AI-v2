import sys
import os
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.models import Article
from backend.database.db import DATABASE_URL, SessionLocal

from datetime import date, datetime, timedelta

def test_date_filter():
    db = SessionLocal()
    
    today = date.today()
    print(f"Today is: {today}")
    
    # Check all articles count
    total = db.query(Article).count()
    print(f"Total articles in DB: {total}")
    
    # Check today's articles by collected_at
    yesterday = datetime.now() - timedelta(days=1)
    today_collected = db.query(Article).filter(Article.collected_at >= yesterday).count()
    print(f"Articles with collected_at >= last 24h: {today_collected}")
    
    # Get one article from last 24h if exists
    latest_coll = db.query(Article).order_by(Article.collected_at.desc()).first()
    if latest_coll:
        print(f"Latest collected article: {latest_coll.title} | Collected at: {latest_coll.collected_at}")
    
    db.close()

if __name__ == "__main__":
    test_date_filter()
