from config.logging_config import get_logger
from db.sessions import init_db, get_engine

logger = get_logger(__name__)


def main() -> None:
    logger.info("Initializing database using SQLAlchemy metadata...")
    engine = get_engine()
    init_db()
    logger.info("✅ Database initialization complete")


if __name__ == "__main__":
    main()
