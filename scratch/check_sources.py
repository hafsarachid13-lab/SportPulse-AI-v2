import sys
import os

# Ajouter le chemin du projet
sys.path.append(os.getcwd())

from backend.database.database import SessionLocal
from backend.database.models import Source

db = SessionLocal()
try:
    count = db.query(Source).filter(Source.is_active == True).count()
    print(f"DEBUG: Active sources count in DB = {count}")
    
    all_sources = db.query(Source).all()
    print(f"DEBUG: Total sources in DB = {len(all_sources)}")
    for s in all_sources:
        print(f" - {s.name}: is_active={s.is_active}")
finally:
    db.close()
