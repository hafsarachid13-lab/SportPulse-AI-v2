from __future__ import annotations

import os
import logging
from collections.abc import Generator
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.database.models import Base

# Load .env file
load_dotenv()

logger = logging.getLogger(__name__)


def _build_default_mysql_url() -> str:
    driver = os.getenv("MYSQL_DRIVER", "mysql+pymysql")
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    database = os.getenv("MYSQL_DATABASE", "veille_sportive")
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")
    charset = os.getenv("MYSQL_CHARSET", "utf8mb4")
    
    credentials = user
    if password:
        credentials = f"{user}:{quote_plus(password)}"

    return f"{driver}://{credentials}@{host}:{port}/{database}?charset={charset}"


DATABASE_URL = os.getenv("DATABASE_URL") or _build_default_mysql_url()


def _engine_kwargs(url: str) -> dict:
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


def _get_engine():
    """Create database engine with diagnostic logging."""
    try:
        engine = create_engine(
            DATABASE_URL, 
            pool_pre_ping=True, 
            **_engine_kwargs(DATABASE_URL)
        )
        
        # Log database configuration (sanitized)
        if DATABASE_URL.startswith("sqlite"):
            logger.info(f"📦 Using SQLite: {DATABASE_URL}")
        else:
            sanitized_url = DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "***"
            logger.info(f"🗄️  Using MySQL: {sanitized_url}")
        
        return engine
    except Exception as e:
        logger.error(f"❌ Failed to create database engine: {e}")
        raise


engine = _get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create missing tables for local/dev usage.

    In production, run the SQL schema migration script instead.
    """
    Base.metadata.create_all(bind=engine)
