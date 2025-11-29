from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import settings
from config.logging_config import get_logger
from db.models import Base

logger = get_logger(__name__)


engine = create_engine(
    settings.database_url,
    pool_size=settings.postgres_pool_size, # Nombre de connexions persistantes dans le pool
    max_overflow=settings.postgres_max_overflow, # Nombre maximum de connexions supplémentaires autorisées
    pool_timeout=settings.postgres_pool_timeout, # Temps d'attente pour obtenir une connexion avant de lever une erreur
    pool_recycle=settings.postgres_pool_recycle, # Temps après lequel une connexion est recyclée
    future=True, # Utiliser le style 2.0 de SQLAlchemy
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
    logger.info("Initializing database with URL %s", settings.database_url)
    Base.metadata.create_all(bind=engine)
