from config.logging_config import get_logger
from db.models import Base
from db.session import engine

logger = get_logger(__name__)


def init_db() -> None:
    logger.info("Creating tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created.")
