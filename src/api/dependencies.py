from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from db.repository import OfferRepository
from db.sessions import get_session


def get_db() -> Generator[Session, None, None]:
    """Dépendance FastAPI pour obtenir une session DB."""
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def get_offer_repository(db: Session = Depends(get_db)) -> OfferRepository:
    """Dépendance FastAPI pour obtenir un repository d'offres."""
    return OfferRepository(db)
