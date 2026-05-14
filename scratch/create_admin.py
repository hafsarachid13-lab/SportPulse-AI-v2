import sys
import os

# Add the project root to sys.path to import backend modules
sys.path.append(r"c:\Users\Mery\Downloads\Downloads\project-fin-de-formation-version pre final\project-fin-de-formation")

from backend.database.db import SessionLocal
from backend.database.models import User, UserRole
from backend.core.security import hash_password

def create_admin_user(email, username, password):
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"User with email {email} already exists.")
            return False

        # Create new admin user
        new_user = User(
            email=email,
            username=username,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"Admin user created successfully!")
        print(f"Email: {email}")
        print(f"Username: {username}")
        return True
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    email = "meryemn8n@gmail.com"
    username = "meryemn8n"
    password = "Admin2026!" # Temporary secure password
    create_admin_user(email, username, password)
