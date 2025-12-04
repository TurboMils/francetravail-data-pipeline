# src/db/init_db.py
from config.logging_config import get_logger, setup_logging
from db.models import Base
from db.sessions import engine

logger = get_logger(__name__)


def init_database() -> None:
    """Crée toutes les tables définies dans Base.metadata."""
    logger.info("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


if __name__ == "__main__":
    setup_logging()
    init_database()
