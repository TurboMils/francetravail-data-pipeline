# src/config/logging_config.py
from __future__ import annotations

import logging
import sys

from config.settings import settings


def setup_logging() -> None:
    """Configure le logging global (root logger) une seule fois."""
    # Si des handlers sont déjà présents, on ne refait pas la config
    root = logging.getLogger()
    if root.handlers:
        return

    level = getattr(logging, settings.log_level, logging.INFO)

    root.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)

    if settings.log_format == "json":
        fmt = (
            '{"ts":"%(asctime)s",'
            '"level":"%(levelname)s",'
            '"logger":"%(name)s",'
            '"msg":"%(message)s"}'
        )
    else:
        fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger nommé, en s'assurant que le root est configuré."""
    # S'assure que le root logger est configuré
    setup_logging()

    logger = logging.getLogger(name)

    return logger
