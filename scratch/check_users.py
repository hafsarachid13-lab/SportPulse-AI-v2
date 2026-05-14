import sqlite3
import os

db_path = r"c:\Users\Mery\Downloads\Downloads\project-fin-de-formation-version pre final\project-fin-de-formation\veille_sportive.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, email, role, is_active FROM users;")
        rows = cursor.fetchall()
        for row in rows:
            print(row)
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
