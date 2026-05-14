import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database.db import SessionLocal
from backend.database.models import Article

db = SessionLocal()
try:
    articles = db.query(Article).order_by(Article.collected_at.desc()).limit(10).all()
    print(f"{'ID':<5} | {'Lang':<5} | {'Title':<50}")
    print("-" * 65)
    for a in articles:
        print(f"{a.id:<5} | {a.langue:<5} | {a.title[:50]:<50}")
finally:
    db.close()
