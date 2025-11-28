#!/usr/bin/env python3

from config.logging_config import get_logger
from db.repository import OfferRepository
from db.sessions import init_db, get_session
from etl.extractors.france_travail_api import FranceTravailClient, FranceTravailApiError

logger = get_logger(__name__)


def main() -> None:
    logger.info("Initializing SQLite database...")
    init_db()

    client = FranceTravailClient()

    keyword = "developpeur python"
    departement = "75"
    limit = 50

    try:
        offres = client.search_offers(
            keyword=keyword,
            departement=departement,
            limit=limit,
            publiee_depuis=7,
            sort=1,
        )
    except FranceTravailApiError as exc:
        logger.error("API error while fetching offers: %s", exc)
        return

    logger.info("Fetched %d offers from API", len(offres))

    session = get_session()
    try:
        repo = OfferRepository(session)
        created, updated = repo.upsert_many_from_api(offres)
    finally:
        session.close()

    logger.info("Offers persisted to SQLite (created=%d, updated=%d)", created, updated)
    print(f"Offers persisted to SQLite (created={created}, updated={updated})")


if __name__ == "__main__":
    main()
