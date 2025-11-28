from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.logging_config import get_logger
from db.models import Base

logger = get_logger(__name__)

# Répertoire et fichier SQLite local
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
SQLITE_PATH = DATA_DIR / "data.db"
DATABASE_URL = f"sqlite:///{SQLITE_PATH}"


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # spécifique SQLite
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)


def get_engine():
    """Retourne l'engine global (utile pour scripts)."""
    return engine


def get_session() -> Session:
    """Retourne une nouvelle session SQLAlchemy."""
    return SessionLocal()


def init_db() -> None:
    """Création des tables si elles n'existent pas."""
    logger.info("Initializing SQLite database at %s", SQLITE_PATH)
    Base.metadata.create_all(bind=engine)
