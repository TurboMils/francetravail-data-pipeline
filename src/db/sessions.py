from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

engine = create_engine(
    settings.database_url,
    pool_size=settings.postgres_pool_size,
    max_overflow=settings.postgres_max_overflow,
    pool_timeout=settings.postgres_pool_timeout,
    pool_recycle=settings.postgres_pool_recycle,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
