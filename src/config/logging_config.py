import logging
import sys

from config.settings import settings


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level = getattr(logging, settings.log_level, logging.INFO)

    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)

    if settings.log_format == "json":
        fmt = '{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}'
    else:
        fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)
    logger.propagate = False

    return logger
